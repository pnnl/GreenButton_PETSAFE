from flask import Flask, jsonify, request, abort
from datetime import datetime

from dct_backend.retrieve_coefficients import prepare_coefficients, average_coefficients
from dct_backend.unpickle_buildings import unpickle_buildings
from database_config import *
import influx_database as idb

# Checks for start and end date arguments in routing, then ensures
# that the dates are valid, exist in the data, and that end > start.
# Returns the dates if these checks pass.
def check_for_date_limiter_arguments(request):
    # Fallbacks
    # TODO: fall back to whole data span? Or is None sensible? Think about it
    start_date = None
    end_date = None
    # Determine if we have any date filtering
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    try: # Validity check: are these dates formatted in a valid way?
        if start_date:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        if dt_start and dt_end:
            assert dt_end > dt_start # Does end come AFTER start? If not, request is malformed
    except (ValueError, AssertionError): # Malformed date
        abort(400)
    # TODO sanity check: do we HAVE these dates available? If not, 404
    return start_date, end_date

# Check that the requested ID actually exists
# If it does, returns the id
# Otherwise, aborts request (404: building does not exist, not found error)
def sanity_check_building_id(id):
    try:
        client = idb.init_database()
        # Setup apis
        query_api = client.query_api()
        # TODO: parameterize, not fstring
        #query = f"SELECT 1 FROM POWER WHERE building_id = {id} LIMIT 1;"
        query = f'from(bucket:"{bucket}")\
        |> range(start: {data_startdate}, stop: {data_enddate})\
        |> filter(fn:(r) => r._measurement == "power" and r._field == "real_power" and r.building_id == "{id}")\
        |> limit(n: 1)'
        results = query_api.query(query=query)
        idb.close_client(client)
    except Exception as ex:
        print(ex)
        # Refine this as needed; for now, assume the code is at fault
        abort(500)
    # Test if we have any results
    if results:
        return id # Building exists
    else:
        abort(404) # Building does not exist; bad request

# Run the app and define its routing
def init_app():
    app = Flask(__name__) # instance_relative_config=False
    # app.config.from_object('config.Config')

    # If we need plugins, their inits go here

    with app.app_context():
        from dct_backend import retrieve_site_data, retrieve_coefficients #, dct_averaging
        # Blueprint registration goes here, e.g. app.register_blueprint(auth.auth_bp)

        # By default, a route only answers to GET requests.

        @app.route('/')
        def get_index():
            # Placeholder
            return jsonify({'message': 'Authentication needed'})
        
        # --------------- RAW DATA -------------------
        
        # Needs permission checks- third parties should not have access,
        # non-owners should only hae DP access
        # Return the actual power data for a given site
        # TODO Would it be useful (and safe) to also return links to what buildings the site is in?
        @app.route("/sites/<int:point_id>")
        def get_point_data(point_id):
            # TODO: Sanity check point_id exists (relies on querying non-Influx database)
            # Determine if we have any date filtering
            start, end = check_for_date_limiter_arguments(request)
            point_data = retrieve_site_data.get_site_real(point_id, start, end)
            return point_data.to_json(orient="columns") # TODO Check that orient makes sense
        
        # Returns what sites a given building contains
        # Relies on non-Influx metadata database
        # TODO: also return links to view those sites' power IF user is authorized to see that
        @app.route("/buildings/<int:id>/sites")
        def get_sites_in_building(id):
            sanity_check_building_id(id) # Make sure building exists!
            sites = retrieve_site_data.list_component_sites(id)
            return sites.to_json(orient="columns") # TODO Check that orient makes sense
        
        # Display real power readings for a given building
        @app.route("/buildings/<int:id>/realpower")
        def get_building_real_power(id):
            sanity_check_building_id(id) # Make sure building exists!
            # Prep client
            client = idb.init_database()
            # Get real power
            # TODO: different tag depending on permissions granted by OAuth status
            # For now, raw is what's in the database
            power = idb.read_points_in_range(client=client, building_id=id, privacy_tag="raw")
            idb.close_client(client)
            # TODO: make datetimes obviously datetimes (currently UNIX stamps, which may be confusing to humans)
            # Right now it's hard to understand and that will be a problem in the future. Make it easier to work with
            return power.to_json(orient="records")
        
        # --------------- DCT DATA -------------------
        
        # TODO: should this be different for different views? Or can the same URL respond differently
        # depending on auth status? Is error 401/403 enough? Check best practices
        # Third parties should only have DP access
        # Calculates DCT coefficients for each DAY in the sample period
        # Returns JSON in format:
        # TODO document here
        @app.route("/buildings/<int:id>/coefficients")
        def get_coefficients_for_each_day(id):
            sanity_check_building_id(id) # Make sure building exists!
            # TODO: change return privacy depending on querying party?
            all_coefficients = prepare_coefficients(id)
            # TODO: format frame into something easier to parse in JSON, like "frequency": "value"
            # At minimum, make datetimes obviously datetimes (currently UNIX stamps, which may be confusing to humans)
            # Right now it's hard to understand and that will be a problem in the future. Make it easier to work with
            return all_coefficients.to_json(orient="columns")
        
        # Would this be better as /buildings/id/coefficients?avg=true ?
        # Returns JSON in format:
        # Coefficient: Value
        @app.route("/buildings/<int:id>/coefficients/average")
        def get_average_coefficients(id):
            sanity_check_building_id(id) # Make sure building exists!
            # TODO: change return privacy depending on querying party
            all_coefficients = prepare_coefficients(id)
            avg_coefficients = average_coefficients(all_coefficients)
            # TODO: add frame comment so it's clear what this is and how it's useful
            return avg_coefficients.to_json(orient="columns")
        
        # APIs for protection profiles
        # /buildings/<id>/methodname?parameter=n

        # /buildings/<id>/methodname
        # Arguments: 
        # strength=050 (range: 000 to 100)
        # start=2023-07-03 (YYYY-mm-dd) (TODO: optional?)
        # end=2023-07-08 (YYYY-mm-dd) (must come after start; TODO optional?)
        # Returns JSON in format:
        @app.route("/buildings/<int:id>/signature/lowpass")
        def lowpass_filter_actual_minus_average(id):
            sanity_check_building_id(id) # Make sure building exists!
            # Get and sanity check arguments
            # Lowpass strength
            strength = float(request.args.get('strength'))
            # Check validity of argument
            if not strength or not 100 >= strength >= 000:
                abort(400) # Malformed request
            if strength > 1: # If the user asked for strength like strength=75, not strength=075
                strength = strength / 100 # Convert to percentage for use
            # Start and end dates; get and check validity
            start, end = check_for_date_limiter_arguments(request)
            # Perform lowpass filtering on DCT data
            lowpass_data_frame = retrieve_coefficients.lowpass_filter_output(id, start, end, strength)
            return lowpass_data_frame.to_json(orient="columns") # TODO: check orient makes sense for this case

        # --------------- USER DATA -------------------

        # Return what meters the user has added to their profile?
        

    return app

if __name__ == "__main__":
    app = init_app()
