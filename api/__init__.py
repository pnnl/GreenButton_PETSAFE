from flask import Flask

# IF INTEGRATING ENDPOINTS: please see /api/apitest_init.py and /api/test_routes.py
# This file should mirror the eventual endpoints, but does not
# require the backend to function.

# Run the app and define its routing
def init_app(is_test=True):
    app = Flask(__name__) # instance_relative_config=False
    # app.config.from_object('config.Config')
    # If we need plugins, their inits go here
    with app.app_context():
        if is_test == True:
            from test_routes import test_endpoints as endpoints
        else:
            from routes import endpoints
        app.register_blueprint(endpoints, url_prefix='/speedes/1_0') # Routing
    return app

if __name__ == "__main__":
    app = init_app()
