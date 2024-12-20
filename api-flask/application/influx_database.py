import influxdb_client_3 as influx
from typing import Optional
from os import environ
import pandas as pd
from datetime import datetime

host = "http://127.0.0.1:8086"
bucket = "Buildings"
#database = "Buildings"
# In a deployment environment, this should be handled as a secret
token = environ.get("INFLUXDB_TOKEN")
org = "PNNL"

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
        client.close()
        return "Success"
    else:
        return "Database does not exist"

def read_points_in_range(client, start_datetime, end_datetime):
    # Sanity checks on date range
    if validate_date_range(start_datetime, end_datetime) == "Valid date range":
        # Query for data between the points
        pass

def import_from_json(
        client, 
        filename: Optional[str] = None,
        json_data: Optional[str] = None):
    # Accepted filetypes: .feather, .parquet, .csv, .json, .orc
    # Sanity check that file exists and is right type
    # Sanity check file quality/formatting
    if filename and json_data:
        # Should we process both? Risk of conflicts; TODO
        print("Please read from file OR json string")
    if filename and not json_data:
        # Setup point config
        measurement = "power"
        # Retrieve the file data
        # TODO error handling
        client.write_file(file=filename, measurement_name=measurement, write_precision="s", \
                          tag_columns=["building_id"], timestamp_column="timestamp")
        return "Success"
    elif json_data:
        # Write from json
        pass

# Read pickled buildings into database, keeping in mind that they may already exist
# InfluxDB2 is equipped to handle duplicate values; see
# https://docs.influxdata.com/influxdb/v2/write-data/best-practices/duplicate-points/
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