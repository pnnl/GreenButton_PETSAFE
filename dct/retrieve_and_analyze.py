import pandas as pd
import pickle
import numpy as np

import config
from dct import graph_dct
import dct.dct_config as dctc
from list_files import list_files_in_dir

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