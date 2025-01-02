import pandas as pd
import pickle
from dct_backend.list_files import list_files_in_dir

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