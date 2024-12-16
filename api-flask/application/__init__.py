from flask import Flask, jsonify, request, abort
from dct_backend.retrieve_coefficients import prepare_coefficients
from dct_backend.unpickle_buildings import unpickle_buildings

def check_for_date_limiter_arguments(request):
    start_date, end_date = None
    # Determine if we have any date filtering
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    # TODO sanity check: do we HAVE these dates available?
    return start_date, end_date

# Check that the requested ID actually exists
def sanity_check_building_id(id):
    buildings = unpickle_buildings("../../data/buildings/")
    all_ids = set(buildings["building_id"])
    if id in all_ids:
        return id
    else: # This should be used to trigger a 400 error in the code- building doesn't exist, bad request
        return None

def init_app():
    app = Flask(__name__) # instance_relative_config=False
    # app.config.from_object('config.Config')

    # If we need plugins, their inits go here

    with app.app_context():
        # Include routing
        #from . import routes
        from .dct_backend import basic_dct, alter_coefficients, basic_dct, retrieve_site_data #, dct_averaging
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
        @app.route("/sites/<int:point_id>")
        def get_point_data(point_id):
            # TODO: Sanity check point_id exists
            # Determine if we have any date filtering
            start, end = check_for_date_limiter_arguments(request)
            point_data = retrieve_site_data.get_site_real(point_id, start, end)
            return point_data.to_json(orient="columns") # TODO Check that orient makes sense
        
        # Returns what sites a given building contains
        @app.route("/buildings/<int:id>/sites")
        def get_sites_in_building(id):
            if sanity_check_building_id(id) == None:
                abort(404) # Building does not exist; bad request
            sites = retrieve_site_data.list_component_sites(id)
            return sites.to_json(orient="columns") # TODO Check that orient makes sense
        
        # --------------- DCT DATA -------------------
        
        # TODO: should this be different for different views? Or can the same URL respond differently
        # depending on auth status? Is error 401/403 enough? Check best practices
        # Third parties should only have DP access
        # Calculates DCT coefficients for each DAY in the sample period
        @app.route("/buildings/<int:id>/coefficients")
        def get_coefficients_for_each_day(id):
            if sanity_check_building_id(id) == None:
                abort(404) # Building does not exist; bad request
            # TODO: change return privacy depending on querying party
            all_coefficients = prepare_coefficients(id)
            # TODO: format frame into something easier to parse in JSON, like "frequency": "value"
            # At minimum, make datetimes obviously datetimes (currently UNIX stamps, which may be confusing to humans)
            # Right now it's hard to understand and that will be a problem in the future. Make it easier to work with
            return all_coefficients.to_json(orient="columns")
        
        @app.route("/buildings/<int:id>/coefficients/average")
        def get_average_coefficients(id):
            if sanity_check_building_id(id) == None:
                abort(404) # Building does not exist; bad request
            # TODO: change return privacy depending on querying party
            all_coefficients = prepare_coefficients(id)
            all_coefficients = all_coefficients.transpose()
            days_in_sample = all_coefficients[0].size
            # Calculate the coefficients for one day, averaged for the time period
            avg = all_coefficients.sum() / days_in_sample # Sums by rows, aka per coefficient
            if "avg_coefficients" not in locals(): # Make the initial frame
                avg_coefficients = avg
                dct_count = 1
            else: # Add the building to the frame
                avg_coefficients += avg
                dct_count += 1
            avg_coefficients = avg_coefficients / dct_count
            print(avg_coefficients)
            # TODO: add frame comment so it's clear what this is and how it's useful
            # Format:
            # Coefficient: value
            return avg_coefficients.to_json(orient="columns")
        

    return app

app = init_app()
