import pandas as pd
from numpy import squeeze
from dct_backend import basic_dct, alter_coefficients, retrieve_site_data
from dct_backend.unpickle_buildings import unpickle_buildings
from flask import abort
import database_config

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

def lowpass_filter_output(
        id: int, 
        start: str, 
        end: str, 
        strength: float
        ):
    # Get the average DCT coefficients for the period
    all_coefficients = prepare_coefficients(id)
    avg_coefficients = average_coefficients(all_coefficients)
    # Lowpass filter the average coefficients
    altered_avg_coeffs = alter_coefficients.drop_coefficients(avg_coefficients.copy(), \
                                            method="drop high", PORTION_TO_DROP=strength) # Lowpass
    # Reconstruct average data from actual average coefficients
    actual_avg = basic_dct.recompose(avg_coefficients.copy())
    # Reconstruct average data from altered average coefficients
    altered_avg = basic_dct.recompose(altered_avg_coeffs.copy())
    # Create "signature" for a random day in the sample: actual real power minus actual average
    this_building = retrieve_site_data.get_building(id, unpickle_buildings(database_config.BUILDING_DATABASE_PATH))
    # Select random day first
    # TODO: REWORK FOR INFLUX
    random_days, random_day_data = retrieve_site_data.get_random_day_in_sample(start, end, this_building)
    day = random_days[0]
    day_str = day.strftime("%Y-%m-%d")
    # TODO Temp error method; this could probably be exploited. Find a better way to do cross-file error handling
    if isinstance(random_days, int):
        abort(random_days)
    # Build signature
    # Fix average formatting to conform to frame
    index = random_day_data.index
    actual_avg = pd.Series(squeeze(actual_avg)).set_axis(index)
    altered_avg = pd.Series(squeeze(altered_avg)).set_axis(index)
    # Building frame to graph on top of random day selected actual
    random_day_data[f"DCT Average for {start} to {end}"] = actual_avg
    random_day_data[f"Modified DCT Average: Drop Top {strength * 100}%"] = altered_avg
    random_day_data[day_str + " Signature (Actual - Avg)"] = random_day_data["real_power"] - actual_avg
    # Show effects of altering average: signature + modified average
    # The difference between actual and modified average for each point will affect sig + modified
    # and produce visual changes; higher filtering = more "smoothing" and amplitude loss
    random_day_data[day_str + " Reconstructed with Modified Average"] = random_day_data[day_str + " Signature (Actual - Avg)"] \
                                                                        + altered_avg
    # Rename real_power for more clarity
    random_day_data = random_day_data.rename(columns={"real_power": f"{day_str} Real Power"})
    return random_day_data