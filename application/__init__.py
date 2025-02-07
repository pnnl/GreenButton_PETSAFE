from flask import Flask, jsonify, request, abort
#from json import dumps

from dct_backend.retrieve_coefficients import prepare_coefficients, average_coefficients
from database_config import *
import influx_database as idb
import mysql_database as msq
from validity_tests import *

# Define column names to hide when retrieving data
sensitive_columns = ["first_name", "last_name", "password"]

# Run the app and define its routing
def init_app():
    app = Flask(__name__) # instance_relative_config=False
    # app.config.from_object('config.Config')

    # If we need plugins, their inits go here

    with app.app_context():
        from dct_backend import retrieve_site_data, retrieve_coefficients #, dct_averaging
        # Blueprint registration goes here, e.g. app.register_blueprint(auth.auth_bp)

        # By default, a route only answers to GET requests.

        @app.route('/speedes/1_0')
        def get_index():
            # Placeholder
            return jsonify({'message': '/speedes/1_0/buildings'})
        
        # --------------- RAW DATA -------------------
        
        # Needs permission checks- third parties should not have access,
        # non-owners should only hae DP access
        # Return the actual power data for a given site
        # TODO Would it be useful (and safe) to also return links to what buildings the site is in?
        @app.route("/speedes/1_0/sites/<int:point_id>")
        def get_point_data(point_id):
            # TODO: Sanity check point_id exists (relies on querying non-Influx database)
            # Determine if we have any date filtering
            start, end = check_for_date_limiter_arguments(request)
            point_data = retrieve_site_data.get_site_real(point_id, start, end)
            return point_data.to_json(orient="columns") # TODO Check that orient makes sense
        
        # Returns what sites a given building contains
        # Relies on non-Influx metadata database
        # TODO: also return links to view those sites' power IF user is authorized to see that
        @app.route("/speedes/1_0/buildings/<int:id>/sites")
        def get_sites_in_building(id):
            sanity_check_building_id(id) # Make sure building exists!
            sites = retrieve_site_data.list_component_sites(id)
            return sites.to_json(orient="columns") # TODO Check that orient makes sense
        
        # Display real power readings for a given building
        @app.route("/speedes/1_0/buildings/<int:id>/realpower")
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
        
        # --------- TIME ZONE DATA -----------
        # TODO: combine with Usage Points; the two are never seen separately
        
        @app.route("/speedes/1_0/timezones", methods=['GET', 'POST'])
        # GET
        # Retrieve list of time zones currently supported
        # POST
        # Add a new time zone
        def all_timezones():
            if request.method == 'POST':
                # Get the details of the new zone
                table = "time_configurations"
                cols = get_cols_in_table(table)
                record = build_record(cols, "id", "timezones/", request)
                # Send it to be validated, escaped, and added
                status, values = msq.insert_MySQL(record, "time_configurations")
                # Format status and return
                # TODO: Does GBA have known status formats for results?
                return values.to_json(orient="records"), status, {'Content-Type': 'application/json'}
            
            # Query for list of existing time zones
            elif request.method == 'GET':
                results = msq.query("SELECT * FROM time_configurations;")
                # Format to JSON
                if results.empty:
                    abort(404)
                return results.to_json(orient="records")
        
        @app.route("/speedes/1_0/timezones/<int:tz_id>", methods=['GET', 'POST', 'DELETE'])
        # GET
        # Retrieve the time for this time zone
        # PUT (POST instead?)
        # Update the time zone (e.g. DST status)
        def specific_timezone(tz_id):
            if request.method == 'GET':
                results = msq.query("SELECT * FROM time_configurations WHERE id = %s;", (tz_id,))
                # Format to JSON
                if results.empty:
                    abort(404) # Resource not found, does not exist
                return results.to_json(orient="records")
            
            # Update timezone information
            elif request.method == "POST":
                request_contents = dict(request.args) # Get arguments to pass along changes
                values, status = update_row("time_configurations", request_contents)
                return values.to_json(orient="records"), status, {'Content-Type': 'application/json'}
            
            elif request.method == "DELETE":
                status = msq.delete_record(tz_id, "time_configurations")
                # TODO: check if delete_record aborts on fail. If not, adjust to return relevant http code
                return {'operation':'deletion'}, 201, {'Content-Type': 'application/json'}
            
        # --------------- RETAIL CUSTOMERS --------------------

        @app.route("/speedes/1_0/customers", methods=['GET', 'POST'])
        # GET
        # Retrieve list of customers
        # POST
        # Add a new customer
        def all_customers():
            if request.method == 'POST':
                table = "retail_customers"
                cols = get_cols_in_table(table)
                record = build_record(cols, "id", "customers/", request)
                # Validate that data's types are all valid to insert
                if False not in check_types(record, table):
                    result, code = msq.insert_MySQL(record, table)
                else:
                    status = "Cannot insert: invalid data type"
                    return {'status':status}, 400, {'Content-Type': 'application/json'}
                # Format status and return
                return result.to_json(orient="records"), code, {'Content-Type': 'application/json'}
            
            elif request.method == "GET":
                # Do not return password or full name due to sensitivity
                # Is the publish date sensitive (could be used to determine how long they've spent w/utility company)?
                table = "retail_customers"
                cols = get_cols_in_table(table)
                cols[:] = [x for x in cols if x not in sensitive_columns] # Remove sensitive columns from output
                cols = ', '.join(cols) # Convert to string for query
                cols = cols[:-2] + " " # Remove final comma
                results = msq.query(f"SELECT {cols} FROM {table};") # TODO: can this be parameterized? if not, escape?
                print(results)
                # Format to JSON
                if results.empty:
                    abort(404) # Resource not found, does not exist
                return results.to_json(orient="records")

            
        @app.route("/speedes/1_0/customers/<int:cust_id>", methods=['GET', 'POST', 'DELETE'])
        # GET
        # Retrieve the customer info
        # PUT (POST instead?)
        # Update the customer
        def specific_customers(cust_id):
            if request.method == 'GET':
                # Some of this information is sensitive; it should be handled differently
                # E.G. password, full name
                # Temporarily not returning but should probably ask what's expected
                table = "retail_customers"
                cols = get_cols_in_table(table)
                cols[:] = [x for x in cols if x not in sensitive_columns] # Remove sensitive columns from output
                cols = ', '.join(cols) # Convert to string for query
                cols = cols[:-2] + " " # Remove final comma
                results = msq.query(f"SELECT {cols} FROM {table} WHERE id = %s;", (cust_id,))
                # Format to JSON
                if results.empty:
                    abort(404) # Resource not found, does not exist
                return results.to_json(orient="records")
            
            # Update customer info
            elif request.method == "POST":
                request_contents = dict(request.args) # Get arguments to pass along changes
                result, code = update_row("retail_customers", request_contents)
                return result.to_json(orient="records"), code, {'Content-Type': 'application/json'}
            
            elif request.method == "DELETE":
                status = msq.delete_record(cust_id, "retail_customers")
                return {'operation':"deletion"}, status, {'Content-Type': 'application/json'}
            
        # --------------- SERVICE DELIVERY AND USAGE POINTS -------------------
        # TODO Rename to meters?
        # "Logical point on a network at which consumption or production is either 
        # physically measured (e.g., metered) or estimated (e.g., unmetered street lights)."
        @app.route("/speedes/1_0/usagePoints", methods=['GET', 'POST'])
        def usage_points():
            if request.method == 'GET':
                # Should we also include serviceDeliveryPoints here, or only for specific meters?
                # Makes most sense as specific meters but wait to see use case to confirm
                results = msq.query("SELECT * FROM usage_points;")
                # Format to JSON
                if results == []:
                    abort(404) # Resource not found, does not exist
                return results.to_json(orient="records")
            
            elif request.method == "POST":
                table = "service_delivery_points"
                #cols = get_cols_in_table(table)
                # Add a new point
                # First things first: we need a serviceDeliveryPoint entry for the usagePoint
                # The same SDP can be used by many usagePoints, so check if it exists first
                sdp_id = request.values.get("id")
                sdp_results = msq.query("SELECT COUNT(id) FROM service_delivery_points WHERE id = %s", sdp_id)
                if sdp_results.empty: # The ID doesn't exist yet
                    try:
                        sdp_name = str(request.values.get("sdp_name"))
                        sdp_tariffProfile = str(request.values.get("sdp_tariffProfile"))
                        sdp_customerAgreement = str(request.values.get("sdp_customerAgreement"))
                        # Add to database
                        record = (sdp_id, sdp_customerAgreement, sdp_name, sdp_tariffProfile)
                        status = msq.insert_MySQL(record, table)
                    except:
                        # Is this a risk to be concerned about? A user of the API could potentially try to
                        # add usage points to see if SDPs exist yet by checking the responses.
                        print("This usagePoint needs sdp_name, sdp_tariffProfile, and sdp_customerAgreement fields supplied.")
                    if status != "Success": # We failed to add the usagePoint's SDP
                        print(status)
                        abort(500) # For now. I think there's a better error code for this though
                    else:
                        pass # All is well, SDP exists. Explicit continue.
                # SDP exists for this usagePoint. 
                # This table ALSO needs a localTimeParameters_id, sourced from time_configurations
                # AND a retail_customers_id from retail_customers.
                # (and a subscription_id, but that's temporarily dropped as a constraint)
                # For now, we're assuming these already exist, but TODO:
                # find out whether that assumption is reasonable or not.
                # Add the usagePoint to the database.
                table = "usage_points"
                cols = get_cols_in_table(table)
                record = build_record(cols, "id", "usagePoints/", request)
                if False not in check_types(record, table):
                    status = msq.insert_MySQL(record, table)
                else:
                    status = "Cannot insert: invalid data type"
                    return {'status':status}, 400, {'Content-Type': 'application/json'}
                # Format status and return
                return {'status':status}, 201, {'Content-Type': 'application/json'}
            
            
        @app.route("/speedes/1_0/usagePoints/<usp_id>", methods=['GET', 'POST', 'DELETE'])
        def specific_usage_point(usp_id):
            if request.method == 'GET':
                # Should we also include the related serviceDeliveryPoints data here?
                results = msq.query("SELECT * FROM usage_points WHERE id = %s;", (usp_id,))
                # Format to JSON
                if results == []:
                    abort(404) # Resource not found, does not exist
                return results.to_json(orient="records")
            
            # Update the record
            elif request.method == "POST":
                request_contents = dict(request.args) # Get arguments to pass along changes
                result, code = update_row("usage_points", request_contents)
                return result.to_json(orient="records"), code, {'Content-Type': 'application/json'}

            elif request.method == "DELETE":
                status = msq.delete_record(usp_id, "usage_points")
                return {'operation':"deletion"}, status, {'Content-Type': 'application/json'}
        


        # TODO: combine with Usage Points; the two are never seen separately
        # and SDP is just the revenue part of a UsagePoint
        @app.route("/speedes/1_0/serviceDeliveryPoints", methods=['GET', 'POST'])
        # GET
        # Retrieve list of all points
        # POST
        # Add a new point
        def all_sdpoints():
            if request.method == 'POST':
                record = build_record(
                    ["id", "customerAgreement", "name", "tariffProfile"], "id", None, request
                    )
                print(record)
                status = msq.insert_MySQL(record, "service_delivery_points")
                # Format status and return
                # TODO: Return other http codes if it failed
                return {'status':status}, 201, {'Content-Type': 'application/json'}
            
            elif request.method == "GET":
                results = msq.query("SELECT * FROM service_delivery_points;")
                # Format to JSON
                if results == []:
                    abort(404) # Resource not found, does not exist
                return results.to_json(orient="records")
            
        @app.route("/speedes/1_0/serviceDeliveryPoints/<int:tz_id>", methods=['GET', 'POST', 'DELETE'])
        # GET
        # Retrieve the time for this time zone
        # PUT (POST instead?)
        # Update the time zone (e.g. DST status)
        def specific_sdpoints(cust_id):
            if request.method == 'GET':
                results = msq.query("SELECT * FROM service_delivery_points WHERE id = %s;", (cust_id,))
                # Format to JSON
                if results == []:
                    abort(404) # Resource not found, does not exist
                return results.to_json(orient="records")
            # Update customer info
            elif request.method == "POST":
                record = build_record(
                    ["id", "customerAgreement", "name", "tariffProfile"], "id", None, request
                    )
                # When updating, we need to change published so it stays the same;
                # handle this in the update code once update method is clarified (TODO)
                # Push the update TODO
                #column = None
                #value = None
                #status = msq.update_record(tz_id, column, value)
                status = "Update Not Yet Implemented"
                return {'status':status}, 501, {'Content-Type': 'application/json'}
            elif request.method == "DELETE":
                cust_id = request.values.get('id')
                status = msq.delete_record(cust_id, "service_delivery_points")
                # Check if it handles failure or not
                return {'status':status}, 201, {'Content-Type': 'application/json'}

        # --------------- DCT DATA -------------------
        
        # TODO: should this be different for different views? Or can the same URL respond differently
        # depending on auth status? Is error 401/403 enough? Check best practices
        # Third parties should only have DP access
        # Calculates DCT coefficients for each DAY in the sample period
        # Returns JSON in format:
        # TODO document here
        @app.route("/speedes/1_0/buildings/<int:id>/coefficients")
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
        @app.route("/speedes/1_0/buildings/<int:id>/coefficients/average")
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
        @app.route("/speedes/1_0/buildings/<int:id>/signature/lowpass")
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
