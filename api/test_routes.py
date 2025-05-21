from flask import Blueprint
from scripts.return_sample_json import read_json

test_endpoints = Blueprint('api_routing', __name__, template_folder='templates')

# Mimics customerMockData.json
# Probably shouldn't be shown directly to the user? TODO check again where this is used by frontend
@test_endpoints.route("/customers", methods=['GET'])
def get_all_customers():
    data = read_json("mockData/customerMockData.json")
    return data
        
# Mimics electricMeters.json
# Note: format may change
# Purpose: meters owned or accessible to the currently authenticated customer
@test_endpoints.route("/meters", methods=['GET'])
def get_all_meters():
    data = read_json("mockData/electricMeters.json")
    return data
        
# Mimics users.json
# Should this be merged into customer return, or are users sufficiently distinct from customers
# to need their own endpoint?
# Probably shouldn't be shown directly to the user? TODO check again where this is used by frontend
@test_endpoints.route("/users", methods=["GET"])
def get_all_users():
    data = read_json("mockData/users.json")
    return data

# Metering data- exact format subject to change at the moment, but this is the endpoint for a specific building's data
# (temporarily returning the pre-import data from file; what parameters do you want to keep?)
# /energy/realpower/1 is a working example
# TODO: handling multiple meters in one request
# Note: ideally, request ONLY one meter at a time. You will be able to request more, but the user
# needs to be warned that it might take a few seconds to get that data
@test_endpoints.route("/energy/realpower/<building_id>", methods=["GET"])
def get_all_energy_records(building_id):
    data = read_json(f"mockData/building-{building_id}-data.json")
    return data

# More endpoints may be added if needed; these are the ones we know we need right now