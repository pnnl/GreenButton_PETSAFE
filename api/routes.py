from flask import jsonify, request, abort, Blueprint, Response
from database_config import *
import influx_database as idb
import mysql_database as msq
from validity_tests import *
from sqlWorkerClass import sqlTableWorker
from common_functions import *
from json import dumps

# OVERARCHING TODO:
# Hook all actions into authentication/authorization.
# Right now, they're way too open- anyone can do anything.
# The goal state is users only being permitted to alter or view
# resources they have the correct permissions to work with.

# OVERARCHING TODO:
# Determine which add/update/delete endpoints are covered by GB
# implementation and remove them if not needed in this API

# Define column names to hide when retrieving data
sensitive_columns = ["first_name", "last_name", "password"]
# Versioning information for the API
prefix = '/speedes/1_0'

# All routes in this blueprint
endpoints = Blueprint('api_routing', __name__, template_folder='templates')

# --------------- DIRECTIONS -------------------

@endpoints.route('/')
def get_index():
    return jsonify({'available endpoints': {
                "building energy data": f'{prefix}/energy',
                "customer data": f'{prefix}/customers',
                "premises": f'{prefix}/sites',
                "time zones": f'{prefix}/timezones',
                "meters / usage points": f'{prefix}/meters',
                }
            })
        
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
    power = idb.read_points_in_range(client=client, building_id=meter_id, privacy_tag="raw")
    idb.close_client(client)
    # Mark which meter the data comes from
    power["meter_id"] = meter_id
    # TODO: make datetimes obviously datetimes (currently UNIX stamps, which may be confusing to humans)
    # Right now it's hard to understand and that will be a problem in the future. Make it easier to work with
    return power.to_json(orient="records")

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

            
# --------------- RETAIL CUSTOMERS --------------------

@endpoints.route("/users", methods=['GET'])
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
        # Build the dictionaries for addresses to store as {"address": {user_addresses}}
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

@endpoints.route("/customers", methods=['GET'])
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
            
# --------------- SERVICE DELIVERY AND USAGE POINTS -------------------
# "Logical point on a network at which consumption or production is either 
# physically measured (e.g., metered) or estimated (e.g., unmetered street lights)."
@endpoints.route("/meters", methods=['GET'])
def get_all_usage_points():
    # Should we also include serviceDeliveryPoints here, or only for specific meters?
    # Makes most sense as specific meters but wait to see use case to confirm
    results = msq.query("SELECT * FROM usage_points;")
    # Format to JSON
    if results == []:
        abort(404) # Resource not found, does not exist
    return results.to_json(orient="records")       
            
@endpoints.route("/meters/<usp_id>", methods=['GET'])
def get_usage_point(usp_id):
    worker = sqlTableWorker("usage_points", "id", request, resource_id=usp_id)
    return worker.perform_request_operation(flask_response=True)

# Return the list of meters at a given address
# TODO Would it be useful (and safe) to also return links to what buildings the site is in?
# TODO JWT to secure this against unauthorized users who want to know what meters exist in a
# building they don't own
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


# --------------- ADD, UPDATE, DELETE --------------------
# TODO: These endpoints may need to be removed if the GB implementation
# is fully responsible for these operations; else, consider constraining use
# or otherwise limiting these further

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

# TODO: See if this can be removed; GB API handles this, right?
@endpoints.route("/login", methods=["POST"])
# POST
# Validate whether a user's password is correct
# Takes user_id (specified in URL) and entered password (POSTed)
# password_correct == True means password matches
# password_correct == False means incorrect password or other failure to match
# TODO: tie this into JWT - return is a placeholder for the token integration 
# (request a token, return to user?)
def test_password(customer_id, password):
    # Retrieve the login information for this user_id
    worker = sqlTableWorker("logins", "customer_id", request, resource_id=customer_id)
    # Returns True if successful match, False in any other case
    # If False, see status code for reason matching failed (wrong password, user not found, etc.)
    statuscode, password_correct = worker.check_password(customer_id, password)
    # Will likely return the token instead of placeholder
    return Response({"Password match": password_correct}, status=statuscode, mimetype='application/json')

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