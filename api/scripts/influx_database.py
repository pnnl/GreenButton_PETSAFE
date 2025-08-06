import influxdb_client as influx
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

# These are the suggested defaults in the documentation and should work well for our purposes.
write_options = influx.WriteOptions(batch_size=500,
                            flush_interval=10_000,
                            jitter_interval=2_000,
                            retry_interval=5_000,
                            max_retries=10,
                            max_retry_delay=30_000,
                            exponential_base=2)

# Determine whether a provided date range:
# 1. is formatted in ISO format: YYYY-mm-dd
# 2. is correctly ordered (end is after start)
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
        return False
    # TODO sanity check: do we HAVE these dates available? If not, 404
    return True


# Create a client object for use in reading and writing data.
# Returns the client object
# NOTE: reading data using this object requires initializing an additional query API object from the client object
# see: https://docs.influxdata.com/influxdb/v2/api-guide/client-libraries/python/#query-data-from-influxdb-with-python
# NOTE: client object should be closed with close_client() when finished using it
def init_client():
    # Init the database
    try:
        client = influx.InfluxDBClient(url=influx_host, org=influx_org, token=influx_token)
        return client
    except Exception as ex:
        print("Could not initialize connection:", ex)

# Can only write, not read; primarily here because it allows writing from file and may write more quickly
# in that case, and being able to directly read JSON files into the database is definitely desirable
def init_v3_client():
    # Init the database
    try:
        client = influx3.InfluxDBClient3(host=influx_host, database=influx_bucket, token=influx_token, org=influx_org)
        return client
    except Exception as ex:
        print("Could not initialize connection:", ex)

# Close the client object if it exists
def close_client(client):
    # Sanity check that client exists
    if client:
        # If any extra operations ever need to be performed before closing clients, add them here.
        client.close()
        return "Success"
    else:
        return "Database client does not exist"

# Run a query and return the results. Handles client creation and closing to minimize potential error
# with forgetting to close a client
def query(query):    
    conn = init_client()
    query_api = conn.query_api()
    results = query_api.query_data_frame(query=query)
    conn.close()
    return results

# Return real_power data for a given meter between two dates, or all real_power data if dates not specified
# TODO: take privacy tag into account once we have more than one version of data to work with
def read_points_in_range(
        client: object, 
        meter_id: int,
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
|> filter(fn:(r) => r._measurement == "power" and r._field == "real_power"'# and r.privacy == "{privacy_tag}"'
        if meter_id != None:
            try:
                meter_id = int(meter_id)
            except:
                return "Cannot query: building id must be an integer"
            # TODO: parameterized, not fstring
            query = query + f' and r.meter_id == "{meter_id}"'
        query = query + ")" # Close the open paren
        query = query + ' |> keep(columns: ["_time", "_field", "_value", "meter_id"])' #, "privacy"])'
        query = query + ' |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")' # For performance
        results = query_api.query_data_frame(query=query)
        if not results.empty: # Clean up formatting before returning it
            if "index" in results.columns:
                del results["index"]
            if "result" in results.columns:
                del results["result"] # It's just full of "_result", not needed data
            if "table" in results.columns:
                del results["table"] # Client doesn't need to know which table it came from
            results.rename(columns={"_time": "timestamp"}, inplace=True)
        else:
            print("No results found for configured date range.")
        return results
    # Return subset of data between two dates
    # Sanity checks on date range come first
    if validate_date_range(start_datetime, end_datetime) == True:
        # Query for data between the points
        # TODO: parameterized, not fstring
        # fstring is possibly an injection vulnerability
        #query = f"SELECT * FROM POWER WHERE timestamp BETWEEN '{start_datetime}' AND '{end_datetime};"
        query = f'from(bucket:"{influx_bucket}")\
        |> range(start: {start_datetime}, stop: {end_datetime})\
        |> filter(fn:(r) => r._measurement == "power" and r._field == "real_power" and r.meter_id == "{meter_id}")\
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
        try:
            client.write_file(file=filename, measurement_name=measurement, write_precision="s", \
                          tag_columns=["meter_id", "privacy", "meter_type"], timestamp_column="timestamp")
            return "Success"
        except Exception as ex:
            print("Error writing to database:", ex)
            return "Write error"
    else:
        return "File not found"

# Take a pandas DataFrame and write it to Influx
def write_from_pandas(client2, data):
    with client2.write_api(write_options=write_options) as write_client:
        write_client.write(influx_bucket, influx_org, record=data, data_frame_measurement_name='power', \
                       data_frame_tag_columns=["meter_id", "privacy", "meter_type"], timestamp_column="timestamp")
    return "Success"

# Remove all data from Influx database for a fresh start
# WARNING: irreversable!
def delete_building_data():
    confirmation = input("Are you sure you want to delete all Influx data? This cannot be reversed. y/n: ")
    if confirmation.lower() in ["y", "yes"]:
        client = init_client()
        delete_api = client.delete_api()
        start = "1970-01-01T00:00:00Z" # Way before the data set actually starts
        stop = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        print("Clearing old data...")
        try:
            delete_api.delete(start, stop, '_measurement="power"', bucket=influx_bucket, org=influx_org)
            print("Data successfully cleared.")
            close_client(client)
        except Exception as ex:
            print("Deletion error:", ex)
    else:
        print("Deletion canceled.")

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