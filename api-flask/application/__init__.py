from flask import Flask

def init_app():
    app = Flask(__name__) # instance_relative_config=False
    # app.config.from_object('config.Config')

    # If we need plugins, their inits go here

    with app.app_context():
        # Include routing
        from . import routes
        from .dct_backend import basic_dct, alter_coefficients, dct_averaging, basic_dct
        # Blueprint registration goes here, e.g. app.register_blueprint(auth.auth_bp)

    return app
