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
def init_client():
    # Init the database
    try:
        client = influx.InfluxDBClient(url=influx_host, org=influx_org, token=influx_token)
        # TODO: write and read options, config; batch write may be of interest
        return client
    except Exception as ex:
        print("Could not initialize connection:", ex)

# Can only write, not read; may write more quickly, enables from_file writes
def init_v3_client():
    # Init the database
    try:
        client = influx3.InfluxDBClient3(host=influx_host, database=influx_bucket, token=influx_token, org=influx_org)
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
    
def query(query):
    import warnings
    from influxdb_client.client.warnings import MissingPivotFunction
    warnings.simplefilter("ignore", MissingPivotFunction)
    
    conn = init_client()
    query_api = conn.query_api()
    results = query_api.query_data_frame(query=query)
    conn.close()
    return results

# Return real_power data for a given building between two dates, or all real_power data if dates not specified
# TODO: return different data depending on privacy profile settings
def read_points_in_range(
        client: object, 
        building_id: int,
        privacy_tag: str,
        start_datetime: Optional[datetime] = None, 
        end_datetime: Optional[datetime] = None,
        ):
    # Setup read api object
    query_api = client.query_api()
    if start_datetime == None and end_datetime == None: # Return all data
        # Roughly equivalent to
        # "SELECT time, building_id, real_power FROM POWER WHERE building_id == {building_id})
        # Paren will be closed in a few lines! Left open in case we need to add a building id
        query = f'from(bucket:"{influx_bucket}") \
|> range(start: {data_startdate}, stop: {data_enddate}) \
|> filter(fn:(r) => r._measurement == "power" and r._field == "real_power" and r.privacy == "{privacy_tag}"'
        if building_id != None:
            try:
                building_id = int(building_id)
            except:
                return "Cannot query: building id must be an integer"
            # TODO: parameterized, not fstring
            query = query + f' and r.meter_id == "{building_id}"'
        query = query + ")" # Close the open paren
        query = query + ' |> keep(columns: ["_time", "_field", "_value", "building_id"])'
        query = query + ' |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")' # For performance
        results = query_api.query_data_frame(query=query)
        if not results.empty: # Clean up formatting before returning it
            if "result" in results.columns:
                del results["result"] # It's just full of "_result", not needed data
            if "table" in results.columns:
                del results["table"] # Client doesn't need to know which table it came from
            results.rename(columns={"_time": "time"}, inplace=True)
            # Commented- setting as index means it doesn't show up in json returns
            #results.set_index("time", inplace=True)
        # TODO: should meter_id, privacy_tag be included in output?
        return results
    # Return subset of data between two dates
    # Sanity checks on date range come first
    if validate_date_range(start_datetime, end_datetime) == "Valid date range":
        # Query for data between the points
        # TODO: parameterized, not fstring
        # fstring is known injection vulnerability
        #query = f"SELECT * FROM POWER WHERE timestamp BETWEEN '{start_datetime}' AND '{end_datetime};"
        query = f'from(bucket:"{influx_bucket}")\
        |> range(start: {start_datetime}, stop: {end_datetime})\
        |> filter(fn:(r) => r._measurement == "power" and r._field == "real_power" and r.building_id == "{building_id}")\
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
        results = query_api.query_data_frame(query=query)
        return results

# Import data into database from a compatible file
def import_from_json(filename):
    # Setup APIs
    client = init_v3_client()
    # Accepted filetypes: .feather, .parquet, .csv, .json, .orc
    # Sanity check that file exists
    if exists(filename):
        # Sanity check that file is right type
        name, file_extension = splitext(filename)
        if file_extension not in [".json", ".feather", ".parquet", ".csv", ".orc"]:
            return "Cannot import: invalid filetype"
        # Setup point config
        measurement = "power"
        # Retrieve the file data
        # TODO error handling
        client.write_file(file=filename, measurement_name=measurement, write_precision="s", \
                          tag_columns=["meter_id", "privacy", "meter_type"], timestamp_column="timestamp")
        return "Success"
    else:
        return "File not found"

def write_from_pandas(client2, data):
    with client2.write_api(write_options=write_options) as write_client:
        write_client.write(influx_bucket, influx_org, record=data, data_frame_measurement_name='power', \
                       data_frame_tag_columns=["meter_id", "privacy", "meter_type"], timestamp_column="timestamp")
    #print("Done processing")
    return "Success"

def delete_building_data():
    client = init_client()
    delete_api = client.delete_api()
    start = "1970-01-01T00:00:00Z"
    stop = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    delete_api.delete(start, stop, '_measurement="power"', bucket=influx_bucket, org=influx_org)
    print("Data successfully cleared.")
    close_client(client)

# If this is run on its own, assume we're just importing data and act accordingly
if __name__ == "__main__":
    # Remove old data
    delete_building_data()
    # Read data into database
    from dct_backend import list_files
    client = init_client()
    read_from_dir = "./import-to-database/raw"
    for file in list_files.list_files_in_dir(read_from_dir, append_path=True):
        # TODO: incorporate metadata (in its own bucket?)
        if "metadata" not in file:
            print("Reading", file)
            import_from_json(filename=file)
        else: # metadata file
            pass
    client.close()
    print("Data read successfully")