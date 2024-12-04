import pandas as pd
import pickle
import numpy as np

import plotly.express as px
from random import sample
from os.path import exists
from os import makedirs
from sklearn.metrics import root_mean_squared_error as rmse

import config
from dct import graph_dct
import dct.dct_config as dctc
from list_files import list_files_in_dir

from dct import perform_dct

# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

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
    if days_to_select > len(all_days):
        if dctc.PRINT_DEBUG == True:
            print("Sample size should be less than or equal to days in time period sampled.\nReducing to match days in time period.")
        days_to_select = len(all_days)
    random_days = sample(all_days, days_to_select)

    # UNCOMMENT TO FORCE DATE -----------------
    #forced_date = "2023-07-05"
    #random_days=[datetime.strptime(forced_date, "%Y-%m-%d")]
    # UNCOMMENT TO FORCE DATE -----------------

    random_days.sort() # Ensures dates are in chronological order
    # Get the data for the randomly sampled days
    # Old ver: random_data = building_data.query(f"index in {random_days}")
    # Reworked because type mismatches in isin will be deprecated, but we can't coerce index
    # to a string within a query fstring, and adding a whole column just to remove it later
    # seems unnecessary. There probably is still a better way to handle this: TODO find it.
    # For now, this works.
    for date in random_days:
        date = date.date()
        next_day = date+pd.Timedelta(1, "d")
        if "random_data" not in locals():
            random_data = building_data[date:next_day].iloc[:-1] # No right inclusion
        else:
            slice = building_data[date:next_day].iloc[:-1] # No right inclusion
            random_data = random_data._append(slice)

    random_data["Date"] = random_data.index.date
    for day in random_days:   
        day = day.date()
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
    
    save_images = False
    if save_images == True:
        fig.write_image(save_dir + save_title + ".png")

    return fig, actual_building_data

def DCT_with_DP(avg_frame, building_id, percent_to_drop):
    actual_days = avg_frame.drop(["Averaged DCT"], axis=1) # Used to reconstruct data from signature
    actual_avg = avg_frame["Averaged DCT"]
    # Apply DP to the averaged coefficients
    # Get coefficients back for the averaged DCT coefficient reconstruction
    decomposed_dct = perform_dct.decompose(avg_frame["Averaged DCT"])
    # Apply filter
    recomposed_dct = perform_dct.drop_coefficients(decomposed_dct, PORTION_TO_DROP=percent_to_drop)
    # Reconstruct and graph
    modified_avg = perform_dct.recompose(recomposed_dct)
    dp_title = "Averaged DCT: drop top " + str(percent_to_drop * 100) + "% coefficients to 0"
    avg_frame[dp_title] = modified_avg # Place in graph frame

    # Deconstruct data and reconstruct with modified average to see effect on stats
    rmse_per_day = {}
    for day in actual_days.columns:
        # Deconstruct to signature
        day_signature = deconstruct_day_with_dct_avg(actual_days[day], actual_avg)
        # Reconstruct using modified average with DP applied
        reconstructed_day = reconstruct_day_with_dct_avg(day_signature, modified_avg)
        # Get RMSE for the day
        day_rmse = rmse(actual_days[day].values, reconstructed_day.values)
        if dctc.PRINT_DEBUG == True:
            print(f"RMSE for Building {building_id}, drop {percent_to_drop * 100}% on {day}: {day_rmse}")
        rmse_per_day[day] = day_rmse
        # Add to frame for comparison
        col_title = day.strftime("%Y-%m-%d") + " reconstructed with modified DCT average"
        avg_frame[col_title] = reconstructed_day
        avg_frame[day.strftime("%Y-%m-%d") + " Minus Actual DCT Average"] = day_signature

    title = 'Effects of Averaging DCT Coefficients with and without DP: Building ' + str(building_id) + ', ' + dctc.START_DATE + " to " + dctc.END_DATE
    fig = px.line(avg_frame, labels={"index": "Time", "value": "Real Power"}, title=title, \
                  color_discrete_sequence=px.colors.qualitative.Safe, width=3000)
    averaged_dct_line_index = dctc.COMPARISON_DATE_SAMPLE_SIZE + 1 # Index of average DCT
    for line in fig.data:
        line.opacity = 0.4
    average_dct_line = fig.data[averaged_dct_line_index]
    dct_after_drop = fig.data[averaged_dct_line_index - 1]
    average_dct_line.line.color = "red"
    average_dct_line.opacity = 1
    dct_after_drop.line.color = "purple"
    dct_after_drop.opacity = 1
    if building_id == 0:
        pass #fig.show()

    save_dir = "data/graphs/" + "building-" + str(building_id) + "/modified-averages/quarterly/oct-dec/"
    save_title = "full-week-drop-top-" + str(percent_to_drop) + "-from-" + dctc.START_DATE + " to " + dctc.END_DATE + '-Building ' + \
        str(building_id) + "-Random-Days-Count-" + str(dctc.COMPARISON_DATE_SAMPLE_SIZE) + "-VS-Averaged-DCT-Reconstruction-Normalized"
    save_images = False
    if save_images == True:
        if not exists(save_dir):
            makedirs(save_dir)
        fig.write_html(save_dir + save_title + ".html")
        #fig.write_image(save_dir + save_title + ".png")
    return rmse_per_day

# Get how a day's power differs from the average for storage
# day_real_power and day_avg should be Series objects or similar
def deconstruct_day_with_dct_avg(day_real_power, day_avg):
    day_signature = day_real_power - day_avg
    return day_signature

# Reconstruct a day using the average or a modified average.
# day_signature and day_avg should be Series objects or similar
def reconstruct_day_with_dct_avg(day_signature, day_avg):
    return day_signature + day_avg