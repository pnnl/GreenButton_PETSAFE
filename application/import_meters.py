import influx_database as idb
import pandas as pd
from dct_backend.list_files import iterate
from database_config import *
from datetime import datetime as dt
from time import mktime

from multiprocessing import Pool

# Reads a CSV file into a pandas frame
# Used by prepare_data_from_csv() to read from source files
def data_worker_read(file):
    data = pd.read_csv(file)
    # Add column marking these readings as raw meter data (non-aggregated)
    data["privacy"] = "raw_meter"
    return data

# If no SQLlite database is available, use this
# MUCH slower than using the database, however. Set aside a few hours to let it run
def prepare_data_from_csv():
    print("Preparing data for import")
    # Get all electrical usage files from the data set
    data_root = "../data/2023-Full_v8.1/"
    # Iterate over subdirectories of the root to find power CSV files
    source_files = [] # list to store files
    iterate(data_root, source_files)
    # Read files to pandas
    # Multiprocessing is used to make the time significantly less
    # File reading takes forever for even one year otherwise
    with Pool(processes=4) as pool:
        partials = pool.map(data_worker_read, source_files)
    # Combine the partial sets
    data = pd.concat(partials, axis=0)
    # TODO: limit to MAINS?
    return data

# IF data are already in a SQLlite database, use this
# Faster, but still relatively slow; give it a few minutes to run
def prepare_data_from_sql():
    from sql import commonDB as db
    database = "../data/records.db"
    with db.DBConn.create_connection(database) as conn:
        # Get list of MAINS meters
        query = "SELECT DISTINCT point_id FROM LABELS WHERE LABELS.circuit_label_type_id IN (15,16);"
        results = conn.execute(query)
        ids = results.fetchall()
        ids = tuple([id for result in ids for id in result])
        ids = (47612, 50838) # For testing purposes
        # Get power data for these meters
        # Format datetimes for query
        start = dt.strptime(data_startdate, "%Y-%m-%dT%H:%M:%SZ").date() # to dt
        end = dt.strptime(data_enddate, "%Y-%m-%dT%H:%M:%SZ").date() # to dt
        start = mktime(start.timetuple()) # to unix (stored format)
        end = mktime(end.timetuple()) # to unix (stored format)
        query = f"SELECT * FROM POWER WHERE point_id IN {ids} AND timestamp BETWEEN '{start}' AND '{end}';"
        print("Querying")
        results = conn.execute(query)
        # Retrieve; there's too much data for fetchall to reliably handle, so break it up
        data = []
        cursor_obj = conn.cursor()
        # Retrieve the rows queried. This is the relative slow step in querying; it runs quickly
        # for 2 units but slows down as more units are added to the building and more rows must be
        # retrieved.
        print("Retrieving results (please wait, this will take a few minutes)")
        cursor_obj.arraysize = 10000 # May speed up retrieval; sets how many rows are fetched by fetchmany()
        while True:
            # Fetchmany allows both performance improvements over fetchall() and prevents MemoryError for invalid id values
            chunk = results.fetchmany()
            if chunk == []: # fetchmany returns empty list if there are no more results
                break
            else:
                data = data + chunk # Append to list of records
        # "it is recommended that applications run "PRAGMA optimize" (with no arguments) 
        # just before closing each database connection." This should be very fast or a no-op.
        # https://www.sqlite.org/pragma.html#pragma_optimize
        print("Retrieved. Cleaning up (do not interrupt)...")
        cursor_obj.execute("PRAGMA optimize;")
    # Format data for writing (write_from_pandas())
    columns = ['ee_site_id', 'point_id', 'timestamp', 'duration', 'real_power', 'apparent_power', 'pf'] # used for frame creation
    framed_data = pd.DataFrame.from_records(data=data, columns=columns)
    # Set up index column
    framed_data['timestamp'] = pd.to_datetime(framed_data['timestamp'],unit='s') # To datetime
    #framed_data["timestamp"] = framed_data["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ") # Format as desired by influx
    framed_data = framed_data.set_index("timestamp") # Influx relies on this
    # Add tags
    framed_data["privacy"] = "raw" # Distingishes from modified data for privacy purposes
    framed_data["meter_type"] = "raw" # Distingishes from aggregates
    # Ensure format conforms to existing database schema
    framed_data = framed_data.rename(columns={"point_id": "meter_id"}) # Uniformity with aggregate building meter_id
    metadata = pd.DataFrame(framed_data, columns=["meter_id, ee_site_id"]) # In case we need it later
    framed_data = framed_data.drop(columns=["duration", "ee_site_id"]) # These belong in another table
    return framed_data, metadata

# Write data to the database
# Takes a pandas frame as input
def write_data(data):
    print("Importing data")
    # Init database connection for writing
    conn = idb.init_client()
    # Write from pandas
    try: # Write
        # TODO: SPECIFY TAGS
        idb.write_from_pandas(conn, data)
    except Exception as ex: # Writing fails; alert the user
        print(ex)
        return ex
    # We're done; close the connection
    idb.close_client(conn)
    # Return okay
    return "Success"

def main():
    data, metadata = prepare_data_from_sql()
    print(data)
    status = write_data(data)
    print(status)

if __name__ == "__main__":
    main()
    