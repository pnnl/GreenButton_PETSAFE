from flask import Flask

# Run the app and define its routing
def init_app():
    app = Flask(__name__) # instance_relative_config=False
    with app.app_context():
        # Please see /api/test_routes.py for routing information
        # Append /speedes/1_0 to the routes for full path
        from test_routes import test_endpoints
        app.register_blueprint(test_endpoints, url_prefix='/speedes/1_0') # Routing
    return app

if __name__ == "__main__":
    app = init_app()
