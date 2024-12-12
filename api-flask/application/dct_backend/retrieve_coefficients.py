from dct import perform_dct
from dct import graph_dct
import dct.dct_config as dctc
import dct.normalization as norm
from dct.unpickle_buildings import unpickle_buildings

# Should this be allowed to make bulk id requests?
def prepare_coefficients(id):
    # Retrieve buildings and normalize them
    # TODO: Only retrieve requested building (this was taken from when we wanted to do all of them each time)
    buildings = unpickle_buildings(dctc.BUILDING_DIRECTORY)
    buildings["real_power"] = norm.normalize(buildings["real_power"])
    # Decompose with DCT
    all_building_coefficient_frames = []
    # Get each building's data
    this_building = buildings[buildings["building_id"] == id]
    building_coefficients = perform_dct.dct_by_day(this_building, "real_power") # Once per day in period
    building_coefficients.index.name = 'Coefficient'
    all_building_coefficient_frames.append(building_coefficients) # To allow concatenation into one plot later
    # Make a graph out of it
    fig, frame = graph_dct.graph_coefficients_as_box_all_buildings(all_building_coefficient_frames,
                                                    title=f"Coefficient Magnitudes by Building",
                                                    transpose=True)
    #fig = fig.to_html(full_html=False)
    return frame #, fig