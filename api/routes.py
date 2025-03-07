from flask import jsonify, request, abort, Blueprint
from database_config import *
import influx_database as idb
import mysql_database as msq
from validity_tests import *
from modify_tables import sqlTableWorker
from dct_backend import retrieve_site_data

# Define column names to hide when retrieving data
sensitive_columns = ["first_name", "last_name", "password"]

# All routes in this blueprint
endpoints = Blueprint('api_routing', __name__, template_folder='templates')

prefix = '/speedes/1_0'

@endpoints.route('/')
def get_index():
    return jsonify({'available endpoints': {
                "building energy data": f'{prefix}/buildings',
                "customer data": f'{prefix}/customers',
                "premises": f'{prefix}/sites',
                "time zones": f'{prefix}/timezones',
                "meters / usage points": f'{prefix}/usage-points',
                }
            })
        
# --------------- RAW DATA -------------------
        
    # Needs permission checks- third parties should not have access,
    # non-owners should only hae DP access
    # Return the actual power data for a given site
    # TODO Would it be useful (and safe) to also return links to what buildings the site is in?
@endpoints.route("/sites/<int:point_id>")
def get_point_data(point_id):
    # TODO: Sanity check point_id exists (relies on querying non-Influx database)
    # Determine if we have any date filtering
    start, end = check_for_date_limiter_arguments(request)
    point_data = retrieve_site_data.get_site_real(point_id, start, end)
    return point_data.to_json(orient="columns") # TODO Check that orient makes sense
        
# Returns what sites a given building contains
# Relies on non-Influx metadata database
# TODO: also return links to view those sites' power IF user is authorized to see that
@endpoints.route("/buildings/<int:id>/sites")
def get_sites_in_building(id):
    sanity_check_building_id(id) # Make sure building exists!
    sites = retrieve_site_data.list_component_sites(id)
    return sites.to_json(orient="columns") # TODO Check that orient makes sense
        
# Display real power readings for a given building
@endpoints.route("/buildings/<int:id>/realpower")
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
        
@endpoints.route("/timezones", methods=['GET'])
# GET
# Retrieve list of time zones currently supported
# POST
# Add a new time zone
def get_all_timezones():
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/timezones/add", methods=['POST'])
# POST
# Add a new time zone
def add_timezones():
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/timezones/<int:tz_id>", methods=['GET'])
# GET
# Retrieve the time for this time zone
def get_timezone(tz_id):
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=tz_id)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/timezones/<int:tz_id>/update", methods=['POST'])
# POST
# Update the time zone (e.g. DST status)
def update_timezone(tz_id):
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=tz_id)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/timezones/<int:tz_id>/delete", methods=['DELETE'])
def delete_timezone(tz_id):
    worker = sqlTableWorker("time_configurations", "id", request, resource_id=tz_id)
    return worker.perform_request_operation(flask_response=True)
            
# --------------- RETAIL CUSTOMERS --------------------

@endpoints.route("/customers", methods=['GET'])
# GET
# Retrieve list of all customers
def get_all_customers():
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/customers/add", methods=['POST'])
# POST
# Add a new customer
def add_customer():
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/customers/<int:cust_id>", methods=['GET'])
# GET
# Retrieve the customer info
def get_customer(cust_id):
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=cust_id)
    return worker.perform_request_operation(flask_response=True)
            
@endpoints.route("/customers/<int:cust_id>/update", methods=['POST'])
# POST
# Update the customer
def update_customer(cust_id):
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=cust_id)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/customers/<int:cust_id>/delete", methods=['DELETE'])
def delete_customer(cust_id):
    worker = sqlTableWorker("retail_customers", "id", request, resource_id=cust_id)
    return worker.perform_request_operation(flask_response=True)
            
# --------------- SERVICE DELIVERY AND USAGE POINTS -------------------
# TODO Rename to meters?
# "Logical point on a network at which consumption or production is either 
# physically measured (e.g., metered) or estimated (e.g., unmetered street lights)."
@endpoints.route("/usage-points", methods=['GET'])
def get_all_usage_points():
    # Should we also include serviceDeliveryPoints here, or only for specific meters?
    # Makes most sense as specific meters but wait to see use case to confirm
    results = msq.query("SELECT * FROM usage_points;")
    # Format to JSON
    if results == []:
        abort(404) # Resource not found, does not exist
    return results.to_json(orient="records")
            
@endpoints.route("/usage-points/add", methods=['POST'])
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
            
            
@endpoints.route("/usage-points/<usp_id>", methods=['GET'])
def get_usage_point(usp_id):
    worker = sqlTableWorker("usage_points", "id", request, resource_id=usp_id)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/usage-points/<usp_id>/update", methods=['POST'])
def update_usage_point(usp_id):
    worker = sqlTableWorker("usage_points", "id", request, resource_id=usp_id)
    return worker.perform_request_operation(flask_response=True)
        
@endpoints.route("/usage-points/<usp_id>/delete", methods=['DELETE'])
def delete_usage_point(usp_id):
    worker = sqlTableWorker("usage_points", "id", request, resource_id=usp_id)
    return worker.perform_request_operation(flask_response=True)
        
            
@endpoints.route("/service-delivery-points/<int:sdp_id>/delete", methods=['DELETE'])
def delete_sdpoint(sdp_id):
    worker = sqlTableWorker("service_delivery_points", "id", request, resource_id=None)
    return worker.perform_request_operation(flask_response=True)