import pandas as pd
import pickle
import numpy as np

import plotly.express as px
from random import sample
from datetime import datetime
from os.path import exists
from os import makedirs

import config
from dct import graph_dct
import dct.dct_config as dctc
from list_files import list_files_in_dir

from dct import perform_dct

def prep_filepath():
    # Fix left-off trailing slash
    if config.OUTPUT_DIR[-1] != "/":
        config.OUTPUT_DIR += "/"
    filepath = config.OUTPUT_DIR + "coefficients/"
    # Append to filepath depending on switches used for processing
    # TODO: break this into fewer checks not dependent on processing switches
    if dctc.DCT_ONE_DAY == True:
        filepath = filepath + "one-day/"
    if dctc.GRAPH_TARGET == "d":
        filepath = filepath + "daily-coefficients/"
    if dctc.RESAMPLE_BEFORE_DCT == True:
        filepath = filepath + "resampled-buildings/"
    if dctc.HIGH_ONLY == True:
        filepath = filepath + "top-" + str(dctc.HIGH_THRESHOLD) + "/"
    if dctc.NORMALIZE == True: # TODO: separate switch for reading vs writing normalized data?
        filepath = filepath + "normalized/"
    else:
        filepath = filepath + "non-normalized/"
    return filepath

# Retrieve previously calculated DCT coefficients and perform operations using them
def retrieve_and_analyze():
    filepath = prep_filepath()
    if dctc.GRAPH_COEFFICIENTS_PER_BUILDING == True or dctc.GRAPH_TARGET == "d":
        coefficients = pd.DataFrame()
    else:
        coefficients = np.empty(0, dtype=np.float64)
    try:
        for file in list_files_in_dir(filepath, append_path=True):
            with open(file, "rb") as file:
                building_coefficients = pickle.load(file)
                # This will be a list of numpy arrays; one array per day of data
            if dctc.SHOW_DCT == True:
                print(building_coefficients)
            if dctc.GRAPH_TARGET == "d": # One graph for each day
                graph_dct.graph_coefficients_as_box(building_coefficients)
                break # Temp while testing
            elif dctc.GRAPH_COEFFICIENTS_PER_BUILDING == True:
                coefficients[str(file)[79:-19]] = pd.Series(building_coefficients)
            else:
                coefficients = np.append(coefficients, building_coefficients)
    except Exception as ex:
        print("Could not unpickle building coefficients:", ex)
        raise SystemExit # For now
            
    if dctc.GRAPH_COEFFICIENTS_PER_BUILDING == True:
        graph_dct.graph_coefficients_by_building(coefficients)
    elif dctc.GRAPH_OVERALL_COEFFICIENT_DIST == True:
        graph_dct.graph_coefficients_as_hist(coefficients)

def make_average_dct_curve(building_data, building_id, dct_count, averaged_coefficients):
    avg_coefficients = averaged_coefficients / dct_count
    recomposed = perform_dct.recompose(avg_coefficients.values)
    # Recreate a demand curve from the average coefficients, then graph it against
    # seven randomly selected days of actual data, normalized first if applicable
    # Get range of all dates for this building
    start_date = dctc.START_DATE #building_data.index[0]
    end_date = dctc.END_DATE #building_data.index[-1]
    all_days =  pd.date_range(start=start_date, end=end_date, freq="d", normalize=True, inclusive="left").tolist()
                
    # Select random dates to graph
    days_to_select = dctc.COMPARISON_DATE_SAMPLE_SIZE # must be smaller than days in sample
    random_days = sample(all_days, days_to_select)
    random_days_just_dates = [day.strftime("%Y-%m-%d") for day in random_days] # Cut off times
    if days_to_select > len(random_days_just_dates):
        print("Sample size should be less than or equal to days in time period sampled.\nReducing to match days in time period.")
        days_to_select = len(random_days_just_dates)
    # Grab all times for selected days
    random_days = [pd.date_range(start=date, end=date+pd.Timedelta(1, "d"), \
                                freq="15min", normalize=True, inclusive="left").tolist() \
                                for date in random_days]
    random_days = sum(random_days, [])
    random_days = [day.strftime("%Y-%m-%d %H:%M") for day in random_days]
    random_data = building_data.query(f"index in {random_days}")
    random_data["Date"] = random_data.index.date
    for day in random_days_just_dates:   
        day = datetime.strptime(day,'%Y-%m-%d').date()
        day_data = random_data[random_data["Date"] == day]
        if "actual_building_data" not in locals():
            actual_building_data = pd.DataFrame()
            actual_building_data["Time"] = day_data.index.time
        day_data = day_data.reset_index()
        actual_building_data[day] = pd.DataFrame(day_data["real_power"])
    actual_building_data = actual_building_data.set_index("Time")

    actual_building_data["Averaged DCT"] = recomposed
    title = 'Building ' + str(building_id) + ' VS Averaged DCT Reconstruction from ' + dctc.START_DATE + " to " + dctc.END_DATE
    fig = px.line(actual_building_data, labels={"index": "Time", "value": "Real Power"}, title=title)
    for line in fig.data[0:-1]:
        #line.line.color = "#A9A9A9"
        line.opacity = 0.4
    fig.data[-1].line.color = "red"
    # Save to file
    save_dir = "data/graphs/" + "building-" + str(building_id) + "/"
    save_title = dctc.START_DATE + " to " + dctc.END_DATE + '-Building ' + str(building_id) + '-Random-Days-VS-Averaged-DCT-Reconstruction-Normalized'
    if not exists(save_dir):
        makedirs(save_dir)
    fig.write_image(save_dir + save_title + ".png")
    return fig