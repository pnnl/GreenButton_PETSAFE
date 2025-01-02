import influxdb_client_3 as influx
from typing import Optional
from os.path import exists, splitext
from datetime import datetime

from database_config import *
#host = "http://127.0.0.1:8086"
#bucket = "Buildings"
# In a deployment environment, this should be handled as a secret
#token = environ.get("INFLUXDB_TOKEN")
#org = "PNNL"

# These are the suggested defaults in the documentation.
# TODO: decide if these need to be tweaked for better performance/security
write_options = influx.WriteOptions(batch_size=500,
                            flush_interval=10_000,
                            jitter_interval=2_000,
                            retry_interval=5_000,
                            max_retries=5,
                            max_retry_delay=30_000,
                            exponential_base=2)

def validate_date_range(start_date, end_date):
    # TODO: do we need to check whether the dates are a certain distance apart, too?
    try: # Validity check: are these dates formatted in a valid way?
        if start_date:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        if dt_start and dt_end:
            assert dt_end > dt_start # Does end come AFTER start? If not, request is malformed
    except (ValueError, AssertionError): # Malformed date
        # TODO: return something better
        return "Invalid date range"
    # TODO sanity check: do we HAVE these dates available? If not, 404
    return "Valid date range"

def init_database():
    # Init the database
    try:
        client = influx.InfluxDBClient3(host=host, org=org, token=token, database=bucket)
        # TODO: write and read options, config; batch write may be of interest
        return client
    except Exception as ex:
        print("Could not initialize connection:", ex)

def close_client(client):
    # Sanity check that client exists
    if client:
        # TODO: is there anything else we should run first?
        client.close()
        return "Success"
    else:
        return "Database client does not exist"

def read_points_in_range(
        client, 
        start_datetime: Optional[datetime] = None, 
        end_datetime: Optional[datetime] = None,
        building_id: Optional[int] = None
        ):
    # Return all data
    if start_datetime == None and end_datetime == None:
        query = f"SELECT * FROM POWER"
        if building_id != None:
            try:
                building_id = int(building_id)
            except:
                return "Cannot query: building id must be an integer"
            # TODO: parameterized, not fstring
            query = query + f" WHERE building_id == {building_id}"
        results = client.query(org=org, query=query, language="sql", mode="pandas")
        return results
    # Sanity checks on date range
    if validate_date_range(start_datetime, end_datetime) == "Valid date range":
        # Query for data between the points
        # TODO: parameterized, not fstring
        # fstring is known injection vulnerability
        query = f"SELECT * FROM POWER WHERE timestamp BETWEEN '{start_datetime}' AND '{end_datetime};"
        results = client.query(query=query, language="sql", mode="pandas")
        print(results)
        return results

def import_from_json(
        client, 
        filename: Optional[str] = None,
        json_data: Optional[str] = None):
    # Accepted filetypes: .feather, .parquet, .csv, .json, .orc
    if filename and json_data:
        # Should we process both? Risk of conflicts; TODO
        print("Please read from file OR json string")
        return "Cannot import: pass only one of filename or raw data"
    # Sanity check that file exists
    elif filename and exists(filename):
        # Sanity check that file is right type
        name, file_extension = splitext(filename)
        if file_extension not in [".json", ".feather", ".parquet", ".csv", ".orc"]:
            return "Cannot import: invalid filetype"
        # Setup point config
        measurement = "power"
        # Retrieve the file data
        # TODO error handling
        client.write_file(file=filename, measurement_name=measurement, write_precision="s", \
                          tag_columns=["building_id"], timestamp_column="timestamp")
        return "Success"
    elif json_data:
        # Write directly from json
        pass

# Read pickled buildings into database, keeping in mind that they may already exist
# InfluxDB2 is equipped to handle duplicate values; see
# https://docs.influxdata.com/influxdb/v2/write-data/best-practices/duplicate-points/
# TODO: Not functional yet; for now, use export to JSON and import from that
def import_from_pickled_buildings(pickle_dir, client):
    # Retrieve buildings into a dataframe
    from dct_backend.unpickle_buildings import unpickle_buildings
    buildings = unpickle_buildings(pickle_dir)
    # For each building, add to database
    measurement = "real_power"
    for id in buildings["building_id"].unique():
        this_building = buildings[buildings["building_id"] == id]
        tag_key = "building_id"
        tag_value = id
        with client.write_api(write_options=SYNCHRONOUS) as write_client:
            pass

if __name__ == "__main__":
    # Read data into database
    from dct_backend import list_files
    client = init_database()
    read_from_dir = "./dec-2024-exports/"
    for file in list_files.list_files_in_dir(read_from_dir, append_path=True):
        print("Reading", file)
        # TODO: incorporate metadata (in its own bucket?)
        if "metadata" not in file:
            import_from_json(client=client, filename=file)
        else: # metadata file
            pass
    client.close()