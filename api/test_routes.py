from flask import Flask, Blueprint
from return_sample_json import read_json

test_endpoints = Blueprint('api_routing', __name__, template_folder='templates')

# Mimics customerMockData.json
@test_endpoints.route("/customers", methods=['GET'])
def get_all_customers():
    data = read_json("mockData/customerMockData.json")
    return data
        
# Mimics electricMeters.json
# Note: format may change
@test_endpoints.route("/meters", methods=['GET'])
def get_all_meters():
    data = read_json("mockData/electricMeters.json")
    return data
        
# Mimics users.json
# Should this be merged into customer return, or are users sufficiently distinct from customers
# to need their own endpoint?
@test_endpoints.route("/users", methods=["GET"])
def get_all_users():
    data = read_json("mockData/users.json")
    return data

# Metering data- exact format subject to change at the moment, but this is the endpoint for a specific building's data
# (temporarily returning the pre-import data from file; what parameters do you want to keep?)
# TODO: handling multiple meters for one building instead of just the main line meter?
# Format should be stable for the moment
@test_endpoints.route("/energy/realpower/<building_id>", methods=["GET"])
def get_all_energy_records(building_id):
    data = read_json(f"mockData/building-{building_id}-data.json")
    return data
        
# To be added:

# CUSTOMERS
# /speedes/1_0/customers/<customer_id> : returns a specific customer (GET)

# BUILDINGS
# /speedes/1_0/addresses/<address_id>/meters : return the list of meter_ids associated with the given address
# /speedes/1_0/buildings/<id> : return metadata about buildings (component meters, address, etc)