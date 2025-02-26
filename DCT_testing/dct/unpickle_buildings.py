import pandas as pd
import pickle

import config
from list_files import list_files_in_dir

# Building module-related imports
from building_analysis.reader import Reader

def prep_filepath(dir):
    if dir[-1] != "/":
        dir += "/"
    return dir

def unpickle_buildings(dir):
    filepath = prep_filepath(dir)
    buildings_frame = pd.DataFrame()
    # Get all buildings from files and place in one big frame for processing
    try:
        for file in list_files_in_dir(filepath, append_path=True):
            with open(file, "rb") as file:
                building = pickle.load(file)
            buildings_frame = pd.concat((buildings_frame, building))
        return buildings_frame
    except Exception as ex:
        print("Could not unpickle buildings:", ex)
        raise SystemExit # For now
    
def unpickle_resample_buildings(dir):
    filepath = prep_filepath(dir)
    try:
        reader = Reader(config.START_DATE, config.END_DATE, resolution=config.STAT_TEMPORAL_RESOLUTION, read_dir=filepath)
        buildings = reader.get_data()
        return buildings
    except Exception as ex:
        print(ex)
        raise SystemExit