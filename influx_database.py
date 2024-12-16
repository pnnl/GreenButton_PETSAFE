import influxdb_client_3 as influx
from typing import Optional

write_options = influx.WriteOptions(batch_size=500,
                            flush_interval=10_000,
                            jitter_interval=2_000,
                            retry_interval=5_000,
                            max_retries=5,
                            max_retry_delay=30_000,
                            exponential_base=2)

def init_database():
    host = "127.0.0.1" # TODO port
    database = "buildings"
    token = "" # TODO token
    # Init the database
    try:
        database = influx.InfluxDBClient3(host, database, token)
        # TODO: write and read options, config; batch write may be of interest
        return database
    except Exception as ex:
        print("Could not initialize connection:", ex)

def close_database(database):
    # Sanity check that database exists
    if database:
        database.close()
        return "Success"
    else:
        return "Database does not exist"

def write_point(database):
    # Sanity checks on point and database validity
    pass

def read_points_in_range(database, start_datetime, end_datetime):
    # Sanity checks on date range
    pass

def import_from_json(
        database, 
        filename: Optional[str] = None,
        json_data: Optional[str] = None):
    # Accepted filetypes: .feather, .parquet, .csv, .json, .orc
    # Sanity check that file exists and is right type
    # Sanity check file quality/formatting
    if filename and json_data:
        # Should we process both? Risk of conflicts; TODO
        print("Please read from file OR json string")
    if filename and not json_data:
        # Write the file into the database if filename is supplied
        # Second precision is the broadest it lets us have
        database.write_file(file=filename, database=database, write_precision='s')
    elif json_data:
        # Write from json
        pass