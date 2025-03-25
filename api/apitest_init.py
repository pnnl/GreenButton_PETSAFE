from flask import Flask
from return_sample_json import read_json
#from json import dumps

# Run the app and define its routing
def init_app():
    app = Flask(__name__) # instance_relative_config=False

    with app.app_context():
        # By default, a route only answers to GET requests.
            
        # Mimics customerMockData.json
        @app.route("/speedes/1_0/customers", methods=['GET'])
        def get_all_customers():
            data = read_json("mockData/customerMockData.json")
            return data
        
        # Mimics electricMeters.json
        @app.route("/speedes/1_0/meters", methods=['GET'])
        def get_all_meters():
            data = read_json("mockData/electricMeters.json")
            return data
        
        # Mimics users.json
        # Should this be merged into customer return, or are users sufficiently distinct from customers
        # to need their own endpoint?
        @app.route("/speedes/1_0/users", methods=["GET"])
        def get_all_users():
            data = read_json("mockData/users.json")
            return data
        
        # Validate whether a user's password is correct
        # Takes user_id (specified in URL) and entered password (POSTed)
        # Status True means password matches
        # Status False means incorrect password
        # Temporary; returns will likely be adjusted once auth tables are handled
        # True/false is too easy to fake; auth tokens are a bit harder
        # Will try to keep inputs the same if possible, but expect outputs may change
        @app.route("/speedes/1_0/login", methods=["POST"])
        def test_password(user_id, password):
            # Placeholder; actual API tests against the stored password
            return {"Password match": True}

        # Metering data- exact format subject to change at the moment, but this is the endpoint for a specific building's data
        # (temporarily returning the pre-import data from file; what parameters do you want to keep?)
        # TODO: handling multiple meters for one building instead of just the main line meter
        @app.route("/speedes/1_0/energy/<building_id>", methods=["GET"])
        def get_all_energy_records(building_id):
            data = read_json(f"mockData/building-{building_id}-data.json")
            return data
        
        # To be added (please let me know if any of these are unnecessary-
        # I can also merge actions into a single endpoint and go by HTTP request type
        # if that's preferred):

        # CUSTOMERS
        # /speedes/1_0/customers/<customer_id> : returns a specific customer
        # /speedes/1_0/customers/add : add a new customer (POST)
        # /speedes/1_0/customers/<customer_id>/update : update existing customer records (POST)
        # /speedes/1_0/customers/<customer_id>/delete : delete existing customer (DELETE)

        # BUILDINGS
        # /speedes/1_0/buildings/<id> : return metadata about buildings (component meters, address, etc)

        # METERS
        # /speedes/1_0/meters/add : add a meter (POST)
        # /speedes/1_0/meters/update : update a meter (POST)
        # speedes/1_0/meters/delete : delete a meter (DELETE)

        # TIMEZONES? - I do have temporary routes for modifying timezones, though I expect this will be automated
        # such that there doesn't need to be an endpoint- please let me know if I'm wrong and access is needed
        

    return app

if __name__ == "__main__":
    app = init_app()
