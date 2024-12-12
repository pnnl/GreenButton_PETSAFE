from flask import Flask, request, jsonify
from dct_backend.retrieve_coefficients import prepare_coefficients

@app.route('/')
def get_index():
    # Placeholder
    return jsonify({'message': 'Authentication needed'})

# TODO: should this be different for different views? Or can the same URL respond differently
# depending on auth status? Is error 401/403 enough? Check best practices
@app.route("/buildings/<id>/coefficients")
def get_coefficients(id):
    frame = prepare_coefficients(id)
    # TODO: format frame into something easier to parse in JSON, like "frequency": "value"
    return jsonify({"coefficients": frame})