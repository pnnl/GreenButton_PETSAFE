from api.database_config import *
import api.scripts.influx_database as idb
from setup.exports_imports.building_aggregation import list_files

if __name__ == "__main__":
    # Remove old data
    idb.delete_building_data()
    # Read data into database
    client = idb.init_client()
    read_from_dir = "./sample_energy_data"
    for file in list_files.list_files_in_dir(read_from_dir, append_path=True):
        # TODO: incorporate metadata (in its own bucket?)
        if "metadata" not in file:
            print("Reading", file)
            idb.import_from_json(filename=file)
        else: # metadata file
            # TODO: Metadata -> MySQL
            pass
    client.close()
    print("Data read successfully")