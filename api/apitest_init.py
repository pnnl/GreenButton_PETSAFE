from flask import Flask, jsonify, request, abort
from return_sample_json import read_json
#from json import dumps

from dct_backend.retrieve_coefficients import prepare_coefficients, average_coefficients
from database_config import *
import influx_database as idb
import mysql_database as msq
from validity_tests import *
from modify_tables import sqlTableWorker

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
            
            
        @app.route("/speedes/1_0/customers", methods=['GET'])
        def list_customers():
            data = read_json("mockData/customerMockData.json")
            return data
        
        @app.route("/speedes/1_0/meters", methods=['GET'])
        def list_meters():
            data = read_json("mockData/electricMeters.json")
            return data
        

    return app

if __name__ == "__main__":
    app = init_app()
