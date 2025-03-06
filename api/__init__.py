from flask import Flask, jsonify
#from json import dumps
from database_config import *

# Define column names to hide when retrieving data
sensitive_columns = ["first_name", "last_name", "password"]

# Run the app and define its routing
def init_app():
    app = Flask(__name__) # instance_relative_config=False
    # app.config.from_object('config.Config')

    # If we need plugins, their inits go here

    with app.app_context():

        from routes import endpoints
        app.register_blueprint(endpoints)

        # By default, a route only answers to GET requests.

        @app.route('/speedes/1_0')
        def get_index():
            # Placeholder
            return jsonify({'message': '/speedes/1_0/buildings'})
        

    return app

if __name__ == "__main__":
    app = init_app()
