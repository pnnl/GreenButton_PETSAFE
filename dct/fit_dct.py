import pandas as pd
import plotly.express as px
import pickle
import numpy as np
from os.path import exists
from os import makedirs
#from time import perf_counter

import config
from dct import perform_dct
import dct.dct_config as dctc

def fit_dct(this_building, subdir):
    coefficients = []
    # Day by day coefficients
    if dctc.AGGREGATE_BEFORE_DCT == False and dctc.DAILY_DCT_GRAPH == True:
        coefficients = pd.DataFrame()
        dates = np.unique(this_building.index.date) # timestamp is index
        for day in dates:
            # Get the day of data and do DCT on it
            day_data = this_building[this_building.index.date == day]
            day_dct_matrix = perform_dct.decompose(day_data["real_power"], log=False)

            if dctc.HIGH_ONLY == True:
                drop_index = int(dctc.HIGH_THRESHOLD * day_dct_matrix.size)
                day_dct_matrix = day_dct_matrix[drop_index:]
            #day_dct_matrix = dct.drop_coefficients(day_dct_matrix)

            #coefficients[str(day)] = day_dct_matrix
            # Concat is used to stop frame fragmentation warnings
            day_dct_matrix = pd.DataFrame(day_dct_matrix).rename(columns={0: str(day)})
            coefficients = pd.concat([coefficients, day_dct_matrix], axis=1)

            if dctc.DCT_ONE_DAY == True:
                break

    elif dctc.ANALYZE_DCT_PER_BUILDING == True:
        coefficients = perform_dct.decompose(this_building["real_power"], log=False)
    else:
        print("No operation chosen.")

    filename = "Building-" + str(this_building["building_id"].iloc[0]) + "-coefficients.pkl"
    print("Saving DCT coefficients to pickle file at", filename)
    # Set directory path of output- output directory in config + "buildings" subdirectory
    dirpath = config.OUTPUT_DIR + "/coefficients/"
    if dctc.DCT_ONE_DAY == True:
        dirpath = dirpath + "/one-day/"
    if dctc.DAILY_DCT_GRAPH == True:
        dirpath = dirpath + "/daily-coefficients/"
    if dctc.ANALYZE_DCT_PER_BUILDING == True:
        dirpath = dirpath + "/resampled-buildings/"
    if dctc.HIGH_ONLY == True:
        dirpath = dirpath + "/top-" + str(dctc.HIGH_THRESHOLD) + "/"
    dirpath = dirpath + subdir + "/"
    if not exists(dirpath):
        makedirs(dirpath)
    # Save as file to output dir
    with open(dirpath + filename, "wb") as outfile:
        pickle.dump(coefficients, outfile)