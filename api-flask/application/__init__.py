from flask import Flask, jsonify
from dct_backend.retrieve_coefficients import prepare_coefficients
from pandas import DataFrame

def init_app():
    app = Flask(__name__) # instance_relative_config=False
    # app.config.from_object('config.Config')

    # If we need plugins, their inits go here

    with app.app_context():
        # Include routing
        #from . import routes
        from .dct_backend import basic_dct, alter_coefficients, basic_dct #, dct_averaging
        # Blueprint registration goes here, e.g. app.register_blueprint(auth.auth_bp)

        @app.route('/')
        def get_index():
            # Placeholder
            return jsonify({'message': 'Authentication needed'})

        # TODO: should this be different for different views? Or can the same URL respond differently
        # depending on auth status? Is error 401/403 enough? Check best practices
        @app.route("/buildings/<id>/coefficients")
        def get_coefficients(id):
            all_coefficients = prepare_coefficients(id)
            # TODO: format frame into something easier to parse in JSON, like "frequency": "value"
            # At minimum, make datetimes obviously datetimes (currently UNIX stamps, which may be confusing to humans)
            # Right now it's hard to understand and that will be a problem in the future. Make it easier to work with
            print(all_coefficients)
            return all_coefficients.to_json(orient="columns")

    return app

app = init_app()
