import pandas as pd
from datetime import datetime

from processor.commonDB import DBConn
from config import METER_DATABASE_PATH

def get_site_real(point_id, start_date, end_date):
    with DBConn.create_connection(METER_DATABASE_PATH) as conn:
        print("Connected to database.")
        # We only need to query each id once. Convert to set to get unique.
        query = f"SELECT * FROM POWER WHERE point_id == {point_id}"
        if start_date is not None and end_date is not None:
            # Convert provided times to unix timestamps to match database format
            start_date = datetime.strptime(start_date, '%Y-%m-%d').timestamp()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').timestamp()
            # Only retrieve values between the provided timestamps
            query = query + f" AND timestamp BETWEEN '{start_date}' AND '{end_date}';"
        query = query + ";"
        results = conn.execute(query)
        print("Query done. Retrieving (this may take a while)...")
        data = []
        cursor_obj = conn.cursor()
        # Retrieve the rows queried. This is the relative slow step in querying; it runs quickly
        # for small resolutions but slows down as more rows must be retrieved.
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
        cursor_obj.close()
    columns = ['ee_site_id', 'point_id', 'timestamp', 'duration', 'real_power', 'apparent_power', 'pf']
    data = pd.DataFrame.from_records(data=data, columns=columns)
    return data

def list_component_sites(id):
    # Retrieve building from database
    # TODO: implement Influx database or FOSS alternative (Influx has Open Source repository; can it be operated freely?)
    # building = frame, results of querying building id (id variable)
    sites = building["point_id"].iloc[0] # Should be the same for all rows
    return sites