import influxdb_client as influx
from influxdb_client.client.write_api import SYNCHRONOUS
import influxdb_client_3 as influx3
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

# Determine whether a provided date range:
# 1. is formatted in ISO format: YYYY-mm-dd
# 2. is correctly ordered (end is after start)
# TODO: also validate that these dates do exist in the data?
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


# Create a client object for use in reading and writing data.
# Returns the client object
# NOTE: reading requires initializing a query API object from the client object
# NOTE: client object should be closed with close_client() when finished using it
def init_database():
    # Init the database
    try:
        client = influx.InfluxDBClient(url=host, org=org, token=token)
        # TODO: write and read options, config; batch write may be of interest
        return client
    except Exception as ex:
        print("Could not initialize connection:", ex)

# Can only write, not read; may write more quickly, enables from_file writes
def init_v3_client():
    # Init the database
    try:
        client = influx3.InfluxDBClient3(host=host, database=bucket, token=token, org=org)
        # TODO: write and read options, config; batch write may be of interest
        return client
    except Exception as ex:
        print("Could not initialize connection:", ex)

# Close the client object if it exists
def close_client(client):
    # Sanity check that client exists
    if client:
        # TODO: is there anything else we should run first?
        client.close()
        return "Success"
    else:
        return "Database client does not exist"

# Return real_power data for a given building between two dates, or all real_power data if dates not specified
# TODO: return different data depending on privacy profile settings
def read_points_in_range(
        client, 
        building_id,
        start_datetime: Optional[datetime] = None, 
        end_datetime: Optional[datetime] = None,
        ):
    # Setup read api object
    query_api = client.query_api()
    if start_datetime == None and end_datetime == None: # Return all data
        # Roughly equivalent to
        # "SELECT time, building_id, real_power FROM POWER WHERE building_id == {building_id})
        query = f'from(bucket:"{bucket}") \
|> range(start: {data_startdate}, stop: {data_enddate}) \
|> filter(fn:(r) => r._measurement == "power" and r._field == "real_power"'
        if building_id != None:
            try:
                building_id = int(building_id)
            except:
                return "Cannot query: building id must be an integer"
            # TODO: parameterized, not fstring
            query = query + f' and r.building_id == "{building_id}"'
        query = query + ")" # Close the open paren
        query = query + ' |> keep(columns: ["_time", "_field", "_value", "building_id"])'
        query = query + ' |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")' # For performance
        results = query_api.query_data_frame(query=query)
        del results["result"] # It's just full of "_result", not needed data
        del results["table"] # Client doesn't need to know which table it came from
        return results
    # Return subset of data between two dates
    # Sanity checks on date range come first
    if validate_date_range(start_datetime, end_datetime) == "Valid date range":
        # Query for data between the points
        # TODO: parameterized, not fstring
        # fstring is known injection vulnerability
        #query = f"SELECT * FROM POWER WHERE timestamp BETWEEN '{start_datetime}' AND '{end_datetime};"
        query = f'from(bucket:"{bucket}")\
        |> range(start: {start_datetime}, stop: {end_datetime})\
        |> filter(fn:(r) => r._measurement == "power" and r._field == "real_power" and r.building_id == "{building_id}")\
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
        results = query_api.query_data_frame(query=query)
        return results

# Import data into database from a compatible file or raw JSON
# Currently, only file imports are functional
def import_from_json(
        filename: Optional[str] = None,
        json_data: Optional[str] = None):
    # Setup APIs
    client = init_v3_client()
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
                          tag_columns=["building_id", "privacy"], timestamp_column="timestamp")
        client.close()
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

def delete_building_data(client):
    delete_api = client.delete_api()
    start = "1970-01-01T00:00:00Z"
    stop = "2025-02-01T00:00:00Z"
    delete_api.delete(start, stop, '_measurement="real_power"', bucket=bucket, org=org)
    print("Data successfully cleared.")

# If this is run on its own, assume we're just importing data and act accordingly
if __name__ == "__main__":
    # Remove old data
    client = init_database()
    delete_building_data(client)
    close_client(client)
    # Read data into database
    from dct_backend import list_files
    client = init_database()
    read_from_dir = "./import-to-database/"
    for file in list_files.list_files_in_dir(read_from_dir, append_path=True):
        print("Reading", file)
        # TODO: incorporate metadata (in its own bucket?)
        if "metadata" not in file:
            import_from_json(filename=file)
        else: # metadata file
            pass
    client.close()