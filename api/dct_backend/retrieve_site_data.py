import pandas as pd
from datetime import datetime
from random import sample

#from data_querying.commonDB import DBConn
import database_config as config

def get_site_real(point_id, start_date, end_date):
    with DBConn.create_connection(config.METER_DATABASE_PATH) as conn:
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

def get_building(id, all_buildings_frame):
    return all_buildings_frame[all_buildings_frame["building_id"] == id]

# Retrieve data for randomly-selected days in the sample
def get_random_day_in_sample(
        start_date: datetime, # First day in range to sample from
        end_date: datetime, # Last day in range to sample from
        # random_day_count: int, # How many random days to return
        building_data: pd.DataFrame # The data to source from
        ):
    random_day_count = 1

    # Get range of all dates for this building's sample
    all_days =  pd.date_range(start=start_date, end=end_date, freq="d", normalize=True, inclusive="left").tolist()
                
    # Sanity check day count
    if random_day_count > len(all_days):
        # Old: days_to_select = len(all_days)
        return 404, None
    random_days = sample(all_days, random_day_count)
    random_days.sort() # Ensures dates are in chronological order
    # Get the data for the randomly sampled days
    # Old ver: random_data = building_data.query(f"index in {random_days}")
    # Reworked because type mismatches in isin will be deprecated, but we can't coerce index
    # to a string within a query fstring, and adding a whole column just to remove it later
    # seems unnecessary. There probably is still a better way to handle this: TODO find it.
    # For now, this works.
    for date in random_days:
        date = date.date()
        next_day = date+pd.Timedelta(1, "d")
        if "random_data" not in locals():
            random_data = building_data[date:next_day].iloc[:-1] # No right inclusion
        else:
            slice = building_data[date:next_day].iloc[:-1] # No right inclusion
            random_data = random_data._append(slice)
    random_data["Date"] = random_data.index.date
    # Set a date column for easy sorting of days if we need to extract a specific date's data
    for day in random_days:   
        day = day.date()
        day_data = random_data[random_data["Date"] == day]
        if "actual_building_data" not in locals():
            actual_building_data = pd.DataFrame()
            # Likewise with a separate time column
            actual_building_data["Time"] = day_data.index.time
        day_data = day_data.reset_index()
        # Used for multiple days: actual_building_data[day] = pd.DataFrame(day_data["real_power"])
        actual_building_data["real_power"] = pd.DataFrame(day_data["real_power"])
    # Use time as an index to allow graphing more easily
    actual_building_data = actual_building_data.set_index("Time")
    return random_days, actual_building_data