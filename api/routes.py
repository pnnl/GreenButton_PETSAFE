from flask import jsonify, request, abort, Blueprint, Response
from database_config import *
import scripts.influx_database as idb
import scripts.mysql_database as msq
from scripts.validity_tests import *
from scripts.sqlWorkerClass import sqlTableWorker
from scripts.common_functions import *
from json import dumps

# OVERARCHING TODO:
# Hook all actions into authentication/authorization.
# Right now, they're way too open- anyone can do anything.
# The goal state is users only being permitted to alter or view
# resources they have the correct permissions to work with.

# OVERARCHING TODO:
# Determine which add/update/delete endpoints are covered by GB
# implementation and remove them if not needed in this API

# Define column names to hide when retrieving data - never return these to the user
sensitive_columns = ["first_name", "last_name", "password"]
# Versioning information for the API
# Appended to every endpoint; e.g. /energy becomes /speedes/1_0/energy
# with prefix = '/speedes/1_0'
prefix = '/speedes/1_0'

# All routes in this blueprint
endpoints = Blueprint('api_routing', __name__, template_folder='templates')

# --------------- DIRECTIONS -------------------

@endpoints.route('/')
def get_index():
    return jsonify({'ref_links': {
                "building_energy": {
                    "ref": f'{prefix}/energy',
                    "type": "GET",
                    "description": "Time series energy usage data. A GET request may be issued to this endpoint for further information."},
                "customers": {
                    "ref": f'{prefix}/customers',
                    "type": "GET",
                    "description": "Retail customer metadata. A GET request may be issued to this endpoint for further information."},
                "users": {
                    "ref": f'{prefix}/users',
                    "type": "GET",
                    "description": "Application user metadata. A GET request may be issued to this endpoint for further information."},
                "meters": {
                    "ref": f'{prefix}/meters',
                    "type": "GET",
                    "description": "Metadata about meters. A GET request may be issued to this endpoint for further information."},
                "addresses": {
                    "ref": f'{prefix}/addresses',
                    "type": "GET",
                    "description": "Address information and operations. A GET request may be issued to this endpoint for further information."}
                }
            })
        
# --------------- ROUTING DOCUMENTATION -------------------
        
@endpoints.route("/energy/")
def energy_instructions():
    message = {"ref_links": {
        "real_power": {
        "ref": f"{prefix}/energy/realpower/<meter_id>",
        "parameters": {"meter_id": "integer corresponding to the meter_id of a usage point"},
        "description": "Real power time series data for the meter given by meter_id. Returns time-series data."
        }
    }}
    return Response(message, status=200, mimetype='application/json')

@endpoints.route("/customers/")
def customers_instructions():
    message = {"ref_links": {
        "all": {
        "ref": f"{prefix}/customers/all",
        "type": "GET",
        "parameters": {},
        "description": "Metadata about all customers the requesting user is permitted to view. Returns a set of customers."
        },
        "by_id": {
        "ref": f"{prefix}/customers/<customer_id>",
        "type": "GET",
        "parameters": {"meter_id": "integer corresponding to the meter_id of a usage point"},
        "description": "Information about a specific customer corresponding to customer_id."
        }
    }}
    return Response(message, status=200, mimetype='application/json')

@endpoints.route("/users/")
def users_instructions():
    message = {"ref_links": {
        "all": {
        "ref": f"{prefix}/users/all",
        "type": "GET",
        "parameters": {},
        "description": "Metadata about all users permitted to be viewed. Will not return sensitive data. Returns a set of users."
        }
    }}
    return Response(message, status=200, mimetype='application/json')

@endpoints.route("/addresses/")
def addresses_instructions():
    message = {"ref_links": {
        "add": {
        "ref": f"{prefix}/addresses/add",
        "type": "POST",
        # TODO: currently accepts individual address parts instead of one fullAddress string (see addresses table in datacustodian.sql); 
        # rework into one string as described here to allow separation of DB structure and user interface structure
        "parameters": {"description": "String describing the address. 255 characters or fewer.",
                       "fullAddress": "String containing the full address in the format, all sections optional: (fraction number) (unit) (building) (street number) \
                        (street prefix) (street name) (street suffix) (street type) (city) (country) (state) (zip code, with or without four digit addition) \
                            (latitude) (longitude)"},
        "description": "Request to add an address to application storage. Returns HTTP status code with address upon success/failure."
        },
        "by_id": {
            "view": {"ref": f"{prefix}/addresses/<address_id>",
                     "type": "GET",
                    "parameters": {"address_id": "integer corresponding to a specific address"},
                    "description": "View an address corresponding to an address_id. Returns the address upon success."},
            "update": {"ref": f"{prefix}/addresses/<address_id>",
                    "type": "POST",
                    # TODO: Can this be abstracted further from the underlying data structure?
                    "parameters": {"address_id": "integer corresponding to a specific address",
                                   "other": "optional: address components that must be changed. e.g. passing 'city' with a value of 'Richland' will update the city field of that address_id to Richland."},
                    "description": "Change details of an address. Returns the altered address upon success."},
            "delete": {"ref": f"{prefix}/addresses/<address_id>/delete",
                    "type": "DELETE",
                    "parameters": {"address_id": "integer corresponding to a specific address"},
                    "description": "Delete an address corresponding to an address_id. Returns HTTP status code."}
        }
    }}
    return Response(message, status=200, mimetype='application/json')


# --------------- RAW DATA -------------------

# Display real power readings for a given meter
# TODO: do we need apparent power equiv, or would it be better to include
# both in the same endpoint?
@endpoints.route("/energy/realpower/<int:meter_id>")
def get_building_real_power(meter_id):
    sanity_check_building_id(meter_id) # Make sure building exists!
    # Prep client
    client = idb.init_client()
    # Get real power
    # TODO: different tag depending on permissions granted by OAuth status
    # For now, raw is what's in the database
    power = idb.read_points_in_range(client=client, meter_id=meter_id, privacy_tag="raw")
    idb.close_client(client) # Done separately to run some extra code before closing
    # Convert to local time
    # Get local time.
    # TODO get from end user, not from server
    local_time = "America/Los_Angeles"
    # Convert to local time
    power = convert_to_tz(power, local_time)
    # Mark which meter the data comes from
    power["meter_id"] = meter_id
    return power.to_json(orient="records", date_format="iso")

# --------------- ADDRESSES --------------------
        
@endpoints.route("/addresses/add", methods=['POST'])
# POST
# Add a new address
def add_address():
    worker = sqlTableWorker("addresses", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/addresses/<int:address_id>", methods=['GET'])
# GET
# Retrieve the address at this id
def get_address(address_id):
    worker = sqlTableWorker("addresses", "id", request, resource_id=address_id)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/addresses/<int:address_id>/update", methods=['POST'])
# POST
# Update the address
def update_address(address_id):
    worker = sqlTableWorker("addresses", "id", request, resource_id=address_id)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/addresses/<int:address_id>/delete", methods=['DELETE'])
# Delete the address record
def delete_address(address_id):
    worker = sqlTableWorker("addresses", "id", request, resource_id=address_id)
    return worker.perform_request_operation(flask_response=True)

            
# --------------- OTHER MAPPINGS --------------------
            
@endpoints.route("/meters/<usp_id>", methods=['GET'])
def get_usage_point(usp_id):
    worker = sqlTableWorker("usage_points", "id", request, resource_id=usp_id)
    return worker.perform_request_operation(flask_response=True)

# Return the list of meters at a given address
# TODO JWT to secure this against unauthorized users who want to know what meters exist in a
# building they don't own; check ownership/residency before returning for an address
@endpoints.route("/addresses/<int:address_id>/meters")
def get_point_data(address_id):
    # Sanity check address_id exists (relies on querying non-Influx database)
    worker = sqlTableWorker("addresses", "id", resource_id=address_id)
    address_exists = worker.check_if_in_table(address_id)
    if address_exists:
        # Find out what meters list this address as their site
        sanity_check_building_id(address_id)
        status, sites = list_component_sites(address_id)
        # TODO: also return links to view those sites' power IF user is authorized to see that
        return Response(sites.to_json(), status=status, mimetype='application/json')
    else:
        return Response("Address not found.", status=404, mimetype='application/json')


# --------------- POTENTIALLY REDUNDANT --------------------
# TODO: These endpoints may need to be removed or altered if the GB implementation
# is fully responsible for these operations; else, consider constraining use
# or otherwise limiting these further

@endpoints.route("/users/all", methods=['GET'])
def get_all_users():
    # Get a list of all users: basic information, username and contact info, and mailing address
    query = "SELECT retail_customers.username, retail_customers.role, retail_customers.first_name,\
        retail_customers.last_name, retail_customers.full_name, retail_customers.accountNumber,\
        retail_customers.email, retail_customers.phone_number, addresses.*  \
        FROM retail_customers \
        LEFT JOIN addresses ON retail_customers.address_id=addresses.id;"
    try:
        status, users = sqlTableWorker.run_query(query)
        # If there is no full_name, build one from other columns if possible; we need a full name
        name_mask = users.full_name.isin([None, ""])
        users.loc[name_mask, "full_name"] = users["first_name"] + " " + users["last_name"]
        # Rename the column to match expected output; clean up column if needed for use
        users.rename(columns={"full_name": "legalName"}, inplace=True)
        users.fillna("", inplace=True)
        # Get addresses in their own frame for future use to convert to a dictionary
        user_addresses = pd.DataFrame()
        # Find out which columns contain address fields so we can format them
        query = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name=%s;"
        status, address_cols = sqlTableWorker.run_query(query, ("addresses",))
        # Format the address frame into ONLY address columns
        ignore_cols = ["id", "description", "published", "self_link_href", "self_link_rel", "up_link_href", "up_link_rel", \
                       "updated", "uuid"]
        # TODO: there has to be a better way to do this
        for col in address_cols["COLUMN_NAME"]:
            if col not in ignore_cols and col in users.columns:
                user_addresses[col] = users[col]
        # Remove any unneeded columns after processing (particularly in addresses)
        # so we don't return unnecessary data
        remove_cols = ["published", "self_link_href", "self_link_rel", "up_link_href", "up_link_rel", \
                       "updated", "uuid", "id", "description", "first_name", "last_name"]
        remove_cols = remove_cols + user_addresses.columns.to_list()
        for col in remove_cols:
            if col in users.columns:
                del users[col]
        # Convert latitude and longitude from decimal to float- the loss of precision
        # is unfortunate, but dumps() doesn't accept Decimal objects and converting to a
        # string results in scientific notation, which may be confusing to end users
        user_addresses["latitude"] = user_addresses["latitude"].apply(float)
        user_addresses["longitude"] = user_addresses["longitude"].apply(float)
        # Build the dictionaries for addresses to store as {"address": {user_addresses}}
        # Address must be stored as a dictionary so that the response follows proper
        # JSON formatting- address data needs to be grouped under "address": {}
        users["address"] = user_addresses.to_dict(orient="records")
        # Format for return
        dict_users = users.to_dict(orient="records")
        users = {"Users": dict_users}
        # Return the list of users in JSON for return
        users = dumps(users)
    except Exception as ex:
        print("Could not retrieve users:", ex)
        users = None
    return Response(users, status=status, mimetype='application/json')

@endpoints.route("/customers/all", methods=['GET'])
# GET
# Retrieve list of all customers
def get_all_customers():
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/customers/<int:cust_id>", methods=['GET'])
# GET
# Retrieve the customer info
def get_customer(cust_id):
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=cust_id)
    return worker.perform_request_operation(flask_response=True)
            
# "Logical point on a network at which consumption or production is either 
# physically measured (e.g., metered) or estimated (e.g., unmetered street lights)."
@endpoints.route("/meters/all", methods=['GET'])
def get_all_usage_points():
    # Should we also include serviceDeliveryPoints here, or only for specific meters?
    # Makes most sense as specific meters but wait to see use case to confirm
    # Get all usage points
    # TODO: only allow those associated with the account doing the requesting; AKA, no asking for meters you have no right to view
    # Tying in authorizations is likely the way to go here
    query = "SELECT usage_points.id, usage_points.status, usage_points.roleFlags, addresses.* FROM usage_points \
        LEFT JOIN addresses ON usage_points.address_id=addresses.id;"
    results = msq.query(query)
    address_cols = msq.query("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name=%s;", ("addresses",))
    # Rename columns to match expected output
    # Done via copying so the for loop later that iterates over the original columns
    # doesn't complain about id's absence (and since it deletes it, this does act as a rename)
    results["meterId"] = results["id"]
    # Get address data into its own frame so it can be formatted into a single string per record more easily
    address_data = pd.DataFrame()
    for col in address_cols["COLUMN_NAME"]:
        address_data[col] = results[col]
        del results[col]
    # Format the addresses
    addresses = []
    for row_id in address_data.index:
        addresses.append(build_address(address_data.iloc[row_id]))
    results["address"] = addresses
    # Set up datetime metadata
    todayDate = datetime.today().strftime('%Y-%m-%d')
    results["requestDate"] = todayDate
    # Get the point's address as a single string
    # TODO: These are filler values that must be retrieved from the table; should be stored
    # on data intake
    results["startDate"] = "None"
    results["terminationDate"] = "None"
    # TODO: These are filler values right now. We need to be able to query or create the actual values
    # based on who's making the query or else remove these fields from output
    results["requestor"] = ""
    results["account"] = ""
    results["accountNumber"] = "FAKEACC" # TODO: this is probably what we need to request to get the above
    # TODO: Also filler values depending on share information; these will need to be retrieved
    # from the MySQL database for the requesting entity
    results["sharedWith"] = "[None]"
    results["entity"] = ""
    results["entityAccessType"] = "Placeholder for Sample Data"
    results["purpose"] = "Testing"
    results["privacyProfile"] = "None"
    results["action"] = "Test"
    # Remove columns that don't need to be displayed
    del results["roleFlags"]
    del results["addresses.id"]
    # Format columns
    # Format to JSON
    if results.empty:
        abort(404) # Resource not found, does not exist
    return results.to_json(orient="records")   

# Add a new customer
@endpoints.route("/customers/add", methods=['POST'])
def add_customer():
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)

# Update a customer
@endpoints.route("/customers/<int:cust_id>/update", methods=['POST'])
def update_customer(cust_id):
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=cust_id)
    return worker.perform_request_operation(flask_response=True)

# Delete a customer       
@endpoints.route("/customers/<int:cust_id>/delete", methods=['DELETE'])
def delete_customer(cust_id):
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=cust_id)
    return worker.perform_request_operation(flask_response=True)

# Edit meters (usage_points)
@endpoints.route("/meters/<usp_id>/update", methods=['POST'])
def update_usage_point(usp_id):
    worker = sqlTableWorker("usage_points", "id", request, resource_id=usp_id)
    return worker.perform_request_operation(flask_response=True)
        
# Delete meters (usage_points)
@endpoints.route("/meters/<usp_id>/delete", methods=['DELETE'])
def delete_usage_point(usp_id):
    worker = sqlTableWorker("usage_points", "id", request, resource_id=usp_id)
    return worker.perform_request_operation(flask_response=True)

# Delete service_delivery_points
@endpoints.route("/service-delivery-points/<int:sdp_id>/delete", methods=['DELETE'])
def delete_sdpoint(sdp_id):
    worker = sqlTableWorker("service_delivery_points", "id", request, resource_id=sdp_id)
    return worker.perform_request_operation(flask_response=True)

# Add service_delivery_points and usage_points together- AKA add a meter           
@endpoints.route("/meters/add", methods=['POST'])
def add_usage_point():
    table = "service_delivery_points"
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
            # TODO Is this a risk to be concerned about? A user of the API could potentially try to
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
    # For now, we're assuming these already exist.
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

@endpoints.route("/timezones", methods=['GET'])
# GET
# Retrieve list of time zones currently supported
# POST
# Add a new time zone
def get_all_timezones():
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)
        
# Add a new time zone
@endpoints.route("/timezones/add", methods=['POST'])
def add_timezones():
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)
        
# Retrieve the details for this time zone
@endpoints.route("/timezones/<int:tz_id>", methods=['GET'])
def get_timezone(tz_id):
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=tz_id)
    return worker.perform_request_operation(flask_response=True)

# POST, update a time zone
@endpoints.route("/timezones/<int:tz_id>/update", methods=['POST'])
def update_timezone(tz_id):
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=tz_id)
    return worker.perform_request_operation(flask_response=True)

# Delete a timezone 
@endpoints.route("/timezones/<int:tz_id>/delete", methods=['DELETE'])
def delete_timezone(tz_id):
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=tz_id)
    return worker.perform_request_operation(flask_response=True)