from flask import Flask
from return_sample_json import read_json
#from json import dumps

# Run the app and define its routing
def init_app():
    app = Flask(__name__) # instance_relative_config=False

    with app.app_context():
        # By default, a route only answers to GET requests.
            
        @app.route("/speedes/1_0/customers", methods=['GET'])
        def list_customers():
            data = read_json("mockData/customerMockData.json")
            return data
        
        @app.route("/speedes/1_0/meters", methods=['GET'])
        def list_meters():
            data = read_json("mockData/electricMeters.json")
            return data
        
        @app.route("/speedes/1_0/users", methods=["GET"])
        def list_users():
            data = read_json("mockData/users.json")
            return data

        @app.route("/speedes/1_0/energy/<building_id>", methods=["GET"])
        def list_energy_records(building_id):
            data = read_json(f"mockData/building-{building_id}-data.json")
            return data
        

    return app

if __name__ == "__main__":
    app = init_app()
