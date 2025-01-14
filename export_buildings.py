import pandas as pd
import pickle
from os.path import exists
from os import makedirs
import datetime
from json import dumps, JSONEncoder
from shutil import make_archive, rmtree

from list_files import list_files_in_dir

# Variables for controlling exports; change as needed
buildings_to_export = range(0, 30)
start_date = "2023-01-01"
end_date = "2023-12-31"
privacy_tag = "raw"

# Path variables
# Ensure read_dir and export_dir end with slashes
read_dir = "output/buildings/"
export_dir = "application/import-to-database/"


# subclass JSONEncoder
# Overriding to enable datetime processing: datetime object -> UNIX timestamp
class DateTimeEncoder(JSONEncoder):
    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

# Ensures path format is correct
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
    
# Fix formatting if necessary
read_dir = prep_filepath(read_dir)
export_dir = prep_filepath(export_dir)
    
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
def export_simple_json(building_data, meter_type, export_path, tag):
    # Tag the data
    building_data["privacy"] = tag
    building_data = building_data.drop(["duration"], axis=1)
    # Export the building to CSV
    if exists(export_path):
        mode = "w" #"a"
    else:
        mode = "w"
    with open(export_path, mode) as outfile:
            building_data = building_data.reset_index()
            building_data["meter_type"] = meter_type
            building_data.to_json(outfile, indent=4, orient='records')
    print("Done.")

# Export metadata of building to JSON file
def export_json_metadata(
        metadata: dict, 
        export_dir: str,
        tag: str
        ):
    metadata["privacy"] = tag
    bid = metadata["building_id"]
    if isinstance(metadata, dict):
        print("Saving metadata.")
        json_metadata = dumps(metadata, indent=4, cls=DateTimeEncoder)
        filename = str(bid) + "-metadata-" + tag + ".json"
        if export_dir:
            # Once to add the path, once to append details to filenames
            filename = export_dir + filename
        # TODO: find a way to write all metadata entries to one file coherently?
        with open(filename, "w") as outfile:
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
    # Sanity checks; set up directories
    if not exists(export_dir):
        makedirs(export_dir)
    if not exists(export_dir + "/data"):
        makedirs(export_dir + "/data")
    
    # Prep filenames
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    zipfile_name = export_dir + "data/" + today

    # Get requested buildings between requested dates
    buildings = unpickle_buildings(read_dir)
    for id in buildings_to_export:
        building_name = f"building-{id}"
        export_path = zipfile_name + "-" + building_name + "-" + privacy_tag + ".json"
        building_data = select_building(buildings, id)
        building_data = select_dates(building_data, start_date, end_date)
        metadata, building_data = extract_metadata(building_data, start_date, end_date)
        export_json_metadata(metadata, export_dir + "data/", tag=privacy_tag)
        #export_simple_csv(building_data, export_path)
        export_simple_json(building_data, "raw_aggregate", export_path, tag=privacy_tag)
    
    # Zip up the results
    make_archive(export_dir + today + "-" + privacy_tag, 'zip', export_dir + "/data")

    # Delete the WIP zipfile directory; no longer needed
    rmtree(export_dir + "data")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping.")
