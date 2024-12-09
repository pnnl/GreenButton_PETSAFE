import pandas as pd
import pickle
from os.path import exists
from os import makedirs
import datetime
from json import dumps, JSONEncoder

from list_files import list_files_in_dir

# subclass JSONEncoder
# Overriding to enable datetime processing: datetime object -> UNIX timestamp
class DateTimeEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

# Ensure format is correct
def prep_filepath(dir):
    if dir[-1] != "/":
        dir += "/"
    return dir

# Retrieve buildings from file
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
    
# Extract a specific building
def select_building(frame, id):
    return frame[frame["building_id"] == id]
    
# Extract data between dates
def select_dates(frame, start, end):
    return frame[start:end]

# Export straight to CSV file, no modification
# If file exists, append (no headers)
def export_simple_csv(building_data, export_path):
    # Export the building to CSV
    if exists(export_path):
        with open(export_path, "a") as outfile:
            building_data.to_csv(outfile, header=False)
    else:
        with open(export_path, "w") as outfile:
            building_data.to_csv(outfile)
    print("Done.")

# Export straight to JSON, no modification
# Record orientation for human comprehension
def export_simple_json(building_data, export_path):
    # Export the building to CSV
    if exists(export_path):
        mode = "w" #"a"
    else:
        mode = "w"
    with open(export_path, mode) as outfile:
            building_data = building_data.reset_index()
            building_data.to_json(outfile, indent=4, orient='records')
    print("Done.")

# Export metadata of building to JSON file
def export_json_metadata(
        metadata: dict, 
        export_dir: str
        ):
    bid = metadata["building_id"]
    if isinstance(metadata, dict):
        print("Saving metadata.")
        json_metadata = dumps(metadata, indent=4, cls=DateTimeEncoder)
        # TODO: find a way to write all metadata entries to one file coherently?
        with open(export_dir + bid + "-metadata.json", "w") as outfile:
            outfile.write(json_metadata)
    else:
        print("Metadata must be a dictionary list.")

# Prep metadata for the building so it can be exported to file
def extract_metadata(building_data, start_date, end_date):
    metadata = {}
    metadata["building_id"] = int(building_data["building_id"].iloc[0])
    # TODO: would it be better to save this as a sub-dict for JSON? sites {{site entry}, {site entry}}
    metadata["component_sites"] = building_data["point_id"].iloc[0][1:-1] # Cut out brackets
    metadata["start_date"] = datetime.datetime.strptime(start_date,'%Y-%m-%d') # TODO: start date of full data?
    metadata["end_date"] = datetime.datetime.strptime(end_date,'%Y-%m-%d') # TODO: does this need to be the end of the day (23:45)?
    building_data = building_data.drop(columns=["point_id"]) # We keep building_id since it's needed when making multiple files
    return metadata, building_data

def main():
    # Variables for controlling exports; change as needed
    read_dir = "data/buildings/"
    export_dir = "data/exports/"
    export_filename = "bzero.json"
    buildings_to_export = [0] #[0,1,2,3,4,5,6,7,8,9]
    start_date = "2023-10-02"
    end_date = "2023-10-08"

    # Leave this alone, though; it gets used later
    export_path = export_dir + export_filename

    # Sanity checks
    if not exists(export_dir):
        makedirs(export_dir)

    # Get requested buildings between requested dates
    buildings = unpickle_buildings(read_dir)
    for id in buildings_to_export:
        building_data = select_building(buildings, id)
        building_data = select_dates(building_data, start_date, end_date)
        metadata, building_data = extract_metadata(building_data, start_date, end_date)
        export_json_metadata(metadata, export_dir)
        #export_simple_csv(building_data, export_path)
        export_simple_json(building_data, export_path)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping.")
