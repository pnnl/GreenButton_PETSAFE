from flask import Flask, jsonify, request, abort, request
from datetime import datetime

from dct_backend.retrieve_coefficients import prepare_coefficients, average_coefficients
from database_config import *
import influx_database as idb
import mysql_database as msq
from datetime import datetime as dt
from uuid import uuid4
from pbkdf2 import crypt
from typing import Optional
#from json import dumps

# Verify that a list of keys corresponds with columns in a table
# keys: the list of column names to test
# table: the name of the table to test on
def check_against_columns(
        key_dict: dict, 
        table: str,
        return_invalid_keys: Optional[bool] = False
        ):
    # TODO: Also check types of data for validity?
    # Get the list of valid columns for the table
    keys = key_dict.keys()
    query = 'SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;'
    cols_in_table = [v for vals in (msq.query(query, (table,)).values) for v in vals] # Flatten list
    # Detect invalid columns
    invalid_keys = []
    for key in keys:
        if key not in cols_in_table:
            invalid_keys.append(key)
    # Remove invalid column keys from the dict and give feedback
    # TODO: API feedback on what got dropped
    for badkey in invalid_keys:
        print(f"{badkey} is not in {table}; dropping and continuing")
        del key_dict[badkey]
    # Check for missing columns, fill with None for later imputation
    for col in cols_in_table:
        if col not in key_dict.keys():
            key_dict[col] = None
    # TODO: what if needed rows are missing? e.g. ID row
    # Return the legitimate keys; optionally, also return the invalid keys
    if return_invalid_keys == True:
        return key_dict, invalid_keys
    else:
        return key_dict

# Checks for start and end date arguments in routing, then ensures
# that the dates are valid, exist in the data, and that end > start.
# Returns the dates if these checks pass.
# request: the HTTP request
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
# id: the id to check
def sanity_check_building_id(id):
    try:
        client = idb.init_database()
        # Setup apis
        query_api = client.query_api()
        # TODO: parameterize, not fstring
        #query = f"SELECT 1 FROM POWER WHERE building_id = {id} LIMIT 1;"
        query = f'from(bucket:"{influx_bucket}")\
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

def hash_value(value):
    # https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#pbkdf2
    value = crypt(value, iterations=60000) # NIST FIPS-140; pbkdf2 is used here; check iteration count for final
    return value

# Determine if the types of the record match the types of the database
def check_types(record, table):
    # Assumption: all columns are filled in the record prior to reaching this function
    # Retrieve the types of the table's columns and validate
    # the supplied record fields as being the right type.
    query = "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;"
    types = msq.query(query, (table,))
    match = []
    for i in len(types): # For every entry in the record
        item_type = type(record[i]) # Get the type of that part of the record
        # Get the corresponding column's type and convert to the Python 
        # equivalent for comparison
        col_type = msq.convert_to_python_type(types[i])
        if item_type != col_type:
            # TODO: SHOULD we coerce the type into the correct one if possible? 
            # (eg int -> float can be done; forcing float only is overly restrictive)
            match.append(False)
            print(f"Type of column {i}: {record[i]} ({item_type}) does not match database; must be {col_type}.)")
        else:
            match.append(True) # Types match, good to go
    return match

# Get variable number of arguments and format into a record
# Some fields need to be auto-generated; others will need to be
# provided by the user. This function handles both and returns
# a record composed of the specified columns.
# column_names: the names of the columns in the table
# id_col_name: the primary key column name for the table (TODO: what if multi-level key?)
# uplink: the unique part of the uplink. Excludes naming/versioning.
# e.g. "customers/" is correct; "/speedes/1.0/customers/" is not.
# request: the HTTP request. Needed to get values for user-supplied params.
def build_record(
        column_names: list, # Ensure these are in order!
        id_col_name: str,
        uplink: str,
        request # The HTTP request; needed to get params
):
    row = {}
    # Build record from supplied column names, getting from request as needed
    for col in column_names:
        # The primary key column
        if col == id_col_name:
            record_id = request.values.get(col) # Used to build self link
            row[col] = record_id
        # UUID column
        elif col == "uuid":
            row[col] = uuid4() #uuid5(mysql_host, id)
        # bool columns
        elif col in ["enabled"]:
            try:
                row[col] = bool(request.values.get(col))
            except:
                print(col, "must be convertable to a Boolean value")
        # Uplinks and self links
        elif col == "up_link_href" and uplink != None:
            row[col] = "/speedes/1_0/" + uplink
        elif col == "up_link_rel" and uplink != None:
            row[col] = "up"
        elif col == "self_link_href" and uplink != None:
            try:
                row[col] = "/speedes/1_0/" + uplink + str(record_id)
            except:
                # For now, this works, but there's a better way somewhere
                return "Columns out of order" # TODO: is this always the case?
        elif col == "self_link_rel" and uplink != None:
            row[col] = "self"
        # Date columns that need to be generated
        elif col == "published" or col == "updated":
            row[col] = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        elif "password" in col:
            # Store as a hash, not the raw password!
            row[col] = hash_value(request.values.get(col))
        # Other columns that need to be requested from http
        else:
            row[col] = request.values.get(col)
    # Flatten the dictionary into just the values and return for use
    # as a new record
    record = tuple(row.values())
    return record

def update_row(
        table: str, 
        new_data: dict # Must include the ID column of the row to change
        ):
    # Validate that the columns we're asking to change actually exist
    new_data = check_against_columns(new_data, table)
    # For columns with a value of None, grab the old value from the table
    none_cols = [col for col in new_data.keys() if new_data[col] == None]
    #none_cols = ", ".join(none_cols) # Format for query
    # TODO: some tables have different id column names. Account for that.
    row_id = new_data["id"]
    query = f"SELECT * FROM {table} WHERE id = %s;"
    values = msq.query(query, (row_id,))
    # Overwrite the columns listed in new_data with the new data
    for col in new_data:
        if col not in none_cols: # If this column has been supplied with new values to update to
            if "password" in col: # Hash the password column values!
                new_data[col] = hash_value(new_data[col])
            values[col] = new_data[col]
    # Place the values into the table, overwriting the existing row
    query = f"UPDATE {table} SET "
    parameters = []
    for col in new_data:
        query += f"{col} = %s, "
        parameters.append(values[col].iloc[0])
    query = query[:-2] + " " # Remove final comma
    query += f"WHERE id = {row_id};"
    print(query)
    print(parameters)
    status = msq.query(query, parameters)
    return status

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
                # TODO: add feedback if values are missing so the user can correctly supply them
                record = build_record(
                    ["id", "description", "published", "updated", "up_link_href", "up_link_rel", \
                     "self_link_href", "self_link_rel", "uuid", "dstEndRule", "dstOffset", "dstStartRule",\
                    "tzOffset"], "id", "timezones/", request
                    )
                # Send it to be validated, escaped, and added
                status = msq.insert_MySQL(record, "time_configurations")
                # Format status and return
                # TODO: Does GBA have known status formats for results?
                return jsonify({'status': str(status)})
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
                status = update_row("time_configurations", request_contents)
                return jsonify({'status': str(status)})
            elif request.method == "DELETE":
                tz_id = request.values.get('id')
                status = msq.delete_record(tz_id, "time_configurations")
                return jsonify({'status': str(status)})
            
        # --------------- RETAIL CUSTOMERS --------------------

        @app.route("/speedes/1_0/customers", methods=['GET', 'POST'])
        # GET
        # Retrieve list of customers
        # POST
        # Add a new customer
        def all_customers():
            if request.method == 'POST':
                record = build_record(
                    ["id", "description", "published", "self_link_href", "self_link_rel", "up_link_href", "up_link_rel", \
                    "updated", "uuid", "enabled", "first_name", "last_name", \
                    "password", "role", "username"], "id", "customers/", request
                    )
                status = msq.insert_MySQL(record, "retail_customers")
                # Format status and return
                # TODO: Does GBA have known status formats for results?
                return jsonify({'status': str(status)})
            elif request.method == "GET":
                # Do not return password or full name due to sensitivity
                # Is the publish date sensitive (could be used to determine how long they've spent w/utility company)?
                results = msq.query("SELECT id, username, description, role, enabled, published, self_link_href, self_link_rel, \
                                    up_link_href, up_link_rel, updated, uuid FROM retail_customers;")
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
                results = msq.query("SELECT id, first_name, last_name, username, description, role, enabled, published, \
                                    self_link_href, self_link_rel, up_link_href, up_link_rel, \
                                    updated, uuid FROM retail_customers WHERE id = %s;", (cust_id,))
                # Format to JSON
                if results.empty:
                    abort(404) # Resource not found, does not exist
                return results.to_json(orient="records")
            # Update customer info
            elif request.method == "POST":
                request_contents = dict(request.args) # Get arguments to pass along changes
                status = update_row("retail_customers", request_contents)
                return jsonify({'status': str(status)})
            elif request.method == "DELETE":
                cust_id = request.values.get('id')
                status = msq.delete_record(cust_id, "retail_customers")
                return jsonify({'status': str(status)})
            
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
                    except:
                        # Is this a risk to be concerned about? A user of the API could potentially try to
                        # add usage points to see if SDPs exist yet by checking the responses.
                        print("This usagePoint needs sdp_name, sdp_tariffProfile, and sdp_customerAgreement fields supplied.")


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
                # TODO: Does GBA have known status formats for results?
                return jsonify({'status': str(status)})
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
                return jsonify({'status': str(status)})
            elif request.method == "DELETE":
                cust_id = request.values.get('id')
                status = msq.delete_record(cust_id, "service_delivery_points")
                return jsonify({'status': str(status)})

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
