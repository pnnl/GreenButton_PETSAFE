from flask import Blueprint
from scripts.return_sample_json import read_json

# Routes with no database requirements for use in testing
# Output format should mirror actual output in routes.py

test_endpoints = Blueprint('api_routing', __name__, template_folder='templates')

# Mimics customerMockData.json
# Probably shouldn't be shown directly to the user; the final API should filter the user
# list to only those the requestor is authorized to view
@test_endpoints.route("/customers/all", methods=['GET'])
def get_all_customers():
    data = read_json("mockData/customerMockData.json")
    return data
        
# Mimics electricMeters.json
# Note: format may change
# Purpose: meters owned or accessible to the currently authenticated customer
@test_endpoints.route("/meters/all", methods=['GET'])
def get_all_meters():
    data = read_json("mockData/electricMeters.json")
    return data
        
# Mimics users.json
# Should this be merged into customer return, or are users sufficiently distinct from customers
# to need their own endpoint?
# Probably shouldn't be shown directly to the user; the final API should filter the user
# list to only those the requestor is authorized to view
@test_endpoints.route("/users/all", methods=["GET"])
def get_all_users():
    data = read_json("mockData/users.json")
    return data

# Metering data- exact format subject to change at the moment, but this is the endpoint for a specific building's data
# (temporarily returning the pre-import data from file; what parameters do you want to keep?)
# /energy/realpower/1 is a working example
# Note: ideally, request ONLY one meter at a time. You will be able to request more, but the user
# needs to be warned that it might take a few seconds to get that data
# Note: final endpoint currently cannot handle more than one meter per request. Building this functionality
# is likely desirable; TODO
@test_endpoints.route("/energy/realpower/<building_id>", methods=["GET"])
def get_all_energy_records(building_id):
    data = read_json(f"mockData/building-{building_id}-data.json")
    return data