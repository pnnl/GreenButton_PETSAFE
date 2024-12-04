import pandas as pd
import pickle
from os.path import exists
from os import makedirs

from list_files import list_files_in_dir

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
    
def select_building(frame, id):
    return frame[frame["building_id"] == id]
    
def select_dates(frame, start, end):
    return frame[start:end]

def main():
    read_dir = "data/buildings/"
    export_dir = "data/exports/"
    export_filename = "all-in-one.csv"
    buildings_to_export = [0,1,2,3,4,5,6,7,8,9]
    start_date = "2023-10-02"
    end_date = "2023-10-08"

    # Sanity checks
    if not exists(export_dir):
        makedirs(export_dir)

    # Get requested buildings between requested dates
    buildings = unpickle_buildings(read_dir)
    for id in buildings_to_export:
        building_data = select_building(buildings, id)
        building_data = select_dates(building_data, start_date, end_date)
        # Export the building to CSV
        export_path = export_dir + export_filename
        if exists(export_path):
            with open(export_path, "a") as outfile:
                building_data.to_csv(outfile, header=False)
        else:
            with open(export_path, "w") as outfile:
                building_data.to_csv(outfile)
        print("Done.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping.")
