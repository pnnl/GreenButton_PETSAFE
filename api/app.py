from flask import Flask, render_template, url_for

from dct import perform_dct
from dct import graph_dct
import dct.dct_config as dctc
import dct.normalization as norm
from dct.unpickle_buildings import unpickle_buildings

app = Flask(__name__)

def get_default_stylesheet():
    return url_for('static', filename='default.css')

@app.route("/")
@app.route("/index")
@app.route("/.html")
def hello_world():
    stylepath = get_default_stylesheet()
    text = "Homepage"
    return render_template('default.html', text=text, style=stylepath, fig="nope")

@app.route("/user")
def give_info():
    stylepath = get_default_stylesheet()
    text = "This is a test: unauthenticated user."
    return render_template('default.html', text=text, style=stylepath)

@app.route("/building-owner")
def give_bowner():
    stylepath = get_default_stylesheet()
    text = "This is a test: building owner."
    return render_template('default.html', text=text, style=stylepath)

@app.route("/utility")
def give_utility():
    stylepath = get_default_stylesheet()
    text = "This is a test: utility."
    return render_template('default.html', text=text, style=stylepath)

@app.route("/data-owner")
def tenant():
    stylepath = get_default_stylesheet()
    text = "This is a test: data owner/tenant."
    return render_template('default.html', text=text, style=stylepath)

# End GUI endpoint testing. Now testing DCT interfaces.

def dct_coefficient_prep():
    # Retrieve buildings and normalize them
    buildings = unpickle_buildings(dctc.BUILDING_DIRECTORY)
    buildings["real_power"] = norm.normalize(buildings["real_power"])
    # Decompose with DCT
    all_building_coefficient_frames = []
    for id in buildings["building_id"].unique():
        # Get each building's data
        this_building = buildings[buildings["building_id"] == id]
        building_coefficients = perform_dct.dct_by_day(this_building, "real_power") # Once per day in period
        building_coefficients.index.name = 'Coefficient'
        all_building_coefficient_frames.append(building_coefficients) # To allow concatenation into one plot later
    # Make a graph out of it
    fig, frame = graph_dct.graph_coefficients_as_box_all_buildings(all_building_coefficient_frames,
                                                    title=f"Coefficient Magnitudes by Building",
                                                    transpose=True)
    fig = fig.to_html(full_html=False)
    return fig, frame

@app.route("/coefficients")
def get_coefficients():
    stylepath = get_default_stylesheet()
    text = "Coefficient data."
    fig, frame = dct_coefficient_prep()
    return render_template('default.html', text=frame, style=stylepath, fig=fig)