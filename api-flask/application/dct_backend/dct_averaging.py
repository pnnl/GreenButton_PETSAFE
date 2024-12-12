import pandas as pd
from typing import Optional

import plotly.express as px
from random import sample
from os.path import exists
from os import makedirs
from sklearn.metrics import root_mean_squared_error as rmse

# These need to be replaced by function arguments or hardcoding
import config
import dct.dct_config as dctc

from dct import perform_dct

# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

if config.OUTPUT_DIR[-1] != "/":
    config.OUTPUT_DIR += "/"

# Use DCT to create an average demand curve for a given temporospacial resolution
# e.g. if you're performing DCT on a span of 7 days, take the coefficients for each of those
# days and average them. Then, reconstruct data from that average.
def make_average_dct_curve(building_data, building_id, dct_count, averaged_coefficients):
    avg_coefficients = averaged_coefficients / dct_count
    recomposed = perform_dct.recompose(avg_coefficients.values)
    # Recreate a demand curve from the average coefficients, then graph it against
    # seven randomly selected days of actual data, normalized first if applicable
    # Get range of all dates for this building
    start_date = dctc.START_DATE
    end_date = dctc.END_DATE
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
    # The actual power for the selected days
    for line in fig.data[0:-1]:
        line.opacity = 0.4
    # The average power made with DCT; red and opaque for visibility against actual
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

# Use DCT modification methods on the averaged demand curve
# Relies on make_average_dct_curve() to make the average first
def DCT_with_DP(
        avg_frame, 
        dp_column, 
        building_id, 
        percent_to_drop: Optional[float] = 0,
        keep_highest: Optional[int] = 0,
        threshold: Optional[float] = 0
        ):
    actual_days = avg_frame.drop(["Averaged DCT"], axis=1) # Used to reconstruct data from signature
    actual_avg = avg_frame["Averaged DCT"]

    # OPERATIONS
    modify_avg = True
    modify_day_signature = True
    save_images = True
    dirname = "/modified-average-and-modified-actual-minus-average/full-week-no-weekends/"
    filename = "no-weekends-drop-top-" + str(percent_to_drop)
    graph_title = 'Effects of DCT Lowpass Filtering on Both Average and Actual - Average Real Power:'

    if modify_avg == True:
        # Apply DP to the averaged coefficients
        # Get coefficients back for the averaged DCT coefficient reconstruction
        actual_dct_avg = avg_frame[dp_column]
        decomposed_dct = perform_dct.decompose(actual_dct_avg)
        # Apply filter
        recomposed_dct = perform_dct.drop_coefficients(decomposed_dct, \
                                    THRESHOLD_VAL=threshold, PORTION_TO_DROP=percent_to_drop, NUMBER_OF_LARGEST=keep_highest)
        # Reconstruct and graph
        modified_avg = perform_dct.recompose(recomposed_dct)
        dp_title = "Averaged DCT: Zero top " + str(percent_to_drop * 100) + "% coefficients"
        avg_frame[dp_title] = modified_avg # Place in graph frame
    else:
        modified_avg = avg_frame[dp_column] # No changes made

    # Deconstruct data and reconstruct with modified average to see effect on stats
    rmse_per_day = {}
    for day in actual_days.columns:
        # Deconstruct to signature
        day_signature = deconstruct_day_with_dct_avg(actual_days[day], actual_avg)

        # Modify Actual - Average with DCT
        if modify_day_signature == True:
            decomposed_sig = perform_dct.decompose(day_signature)
            modified_sig_coeffs = perform_dct.drop_coefficients(decomposed_sig, \
                                            THRESHOLD_VAL=threshold, PORTION_TO_DROP=percent_to_drop, NUMBER_OF_LARGEST=keep_highest)
            recomposed_sig = perform_dct.recompose(modified_sig_coeffs)
            colname = f"{day} actual minus avg, zero top {percent_to_drop * 100}% coefficients"
            avg_frame[colname] = recomposed_sig

            reconstructed_day = reconstruct_day_with_dct_avg(recomposed_sig, modified_avg)

            # Name the modified average column according to the process used to create it
            match dctc.DROP_METHOD:
                case "drop high":
                    colname = f"{day} Modified Actual Minus Average: Zero Top " + str(percent_to_drop * 100) + "%"
                case "drop high keep max":
                    colname = f"{day} Modified Actual Minus Average: Zero Top " + str(percent_to_drop * 100) + "%, Keep Largest " + str(keep_highest)
                case "threshold":
                    colname = f"{day} Modified Actual Minus Average: reduce coefficients <= " + str(threshold) + " to 0"
                case "roll down":
                    colname = f"{day} Modified Actual Minus Average: add high coefficients to low, then zero high"
            avg_frame[colname] = recomposed_sig
        else:
            # Reconstruct using modified average with DP applied
            reconstructed_day = reconstruct_day_with_dct_avg(day_signature, modified_avg)

        # Get RMSE for the day
        day_rmse = rmse(actual_days[day].values, reconstructed_day)#.values)
        if dctc.PRINT_DEBUG == True:
            print(f"RMSE for Building {building_id} on {day}: {day_rmse}")
        rmse_per_day[day] = day_rmse
        # Add to frame for comparison
        col_title = day.strftime("%Y-%m-%d") + " reconstructed with modified coefficients"
        avg_frame[col_title] = reconstructed_day
        avg_frame[day.strftime("%Y-%m-%d") + " Minus Actual DCT Average"] = day_signature

    # Graph the results
    title = graph_title + ' Building ' + str(building_id) + ', ' + dctc.START_DATE + " to " + dctc.END_DATE
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
    if building_id == 0 and dctc.GRAPH_DCT == True:
        fig.show()

    # Save the results
    save_dir = "data/graphs/" + "building-" + str(building_id) + dirname
    save_title = filename + "-from-" + dctc.START_DATE + " to " + dctc.END_DATE + '-Building ' + \
        str(building_id) + "-Random-Days-Count-" + str(dctc.COMPARISON_DATE_SAMPLE_SIZE) + "-VS-Averaged-DCT-Reconstruction-Normalized"
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