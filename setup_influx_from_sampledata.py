from building_aggregation import list_files
from api.database_config import *
from api.influx_database import *

if __name__ == "__main__":
    # Remove old data
    delete_building_data()
    # Read data into database
    client = init_client()
    read_from_dir = "./sample_energy_data"
    for file in list_files.list_files_in_dir(read_from_dir, append_path=True):
        # TODO: incorporate metadata (in its own bucket?)
        if "metadata" not in file:
            print("Reading", file)
            import_from_json(filename=file)
        else: # metadata file
            pass
    client.close()
    print("Data read successfully")