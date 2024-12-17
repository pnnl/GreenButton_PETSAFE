from dct_backend import basic_dct
from dct_backend.unpickle_buildings import unpickle_buildings

# Should this be allowed to make bulk id requests?
# Calculates DCT coefficients for each DAY in the sample period
def prepare_coefficients(id):
    try:
        # Retrieve buildings and normalize them
        # TODO: Only retrieve requested building (this was taken from when we wanted to do all of them each time)
        buildings = unpickle_buildings("../../data/buildings/")
        buildings["real_power"] = basic_dct.normalize(buildings["real_power"])
        # Decompose with DCT
        # Get each building's data
        this_building = buildings[buildings["building_id"] == int(id)]
        building_coefficients = basic_dct.dct_by_day(this_building, "real_power") # Once per day in period
        building_coefficients.index.name = 'Coefficient'
        return building_coefficients
    except ValueError:
        return "No data for building. Does building exist?"
    
def average_coefficients(all_coefficients):
    all_coefficients = all_coefficients.transpose()
    days_in_sample = all_coefficients[0].size
    # Calculate the coefficients for one day, averaged for the time period
    avg = all_coefficients.sum() / days_in_sample # Sums by rows, aka per coefficient
    if "avg_coefficients" not in locals(): # Make the initial frame
        avg_coefficients = avg
        dct_count = 1
    else: # Add the building to the frame
        avg_coefficients += avg
        dct_count += 1
    avg_coefficients = avg_coefficients / dct_count
    return avg_coefficients.transpose()