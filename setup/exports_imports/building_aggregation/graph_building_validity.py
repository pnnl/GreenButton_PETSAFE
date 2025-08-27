import pandas as pd
from numpy import random
from typing import Optional
from time import mktime
from datetime import datetime
from math import floor
import multiprocessing
import pickle
from os.path import exists
from zoneinfo import ZoneInfo
from processor.commonDB import DBConn
import config
import plotly.express as px
from create_buildings import Building
from random import sample

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

# Used to validate that data exists within this period;
# dates are stored as Unix timestamps, so start/end datetimes need to match formats to compare
start = mktime(datetime.strptime(config.START_DATE, '%Y-%m-%d').timetuple())
end = mktime(datetime.strptime(config.END_DATE, '%Y-%m-%d').timetuple())

# Initialize with seed for deterministic rng
def set_seed(seed: Optional[str] = None):
    if seed == None:
        seed = random.randint(100000000, 999999999)
        #print("Random seed generated. Seed:", seed)
    randomizer = random.default_rng(seed)
    return randomizer

# Ensure trailing slash
if config.OUTPUT_DIR[-1] != "/":
    config.OUTPUT_DIR += "/"

# Explicit cast to UTC; it's already in UTC but this makes it aware
def replace_timezone(x):
    return x.replace(tzinfo=ZoneInfo("UTC"))
        
def test_id(id):
    UTC = ZoneInfo("UTC")
    try:
        with open(f"./pickled-meters/{id}-data.pkl", "rb") as infile:
            id_records = pickle.load(infile)
        if id_records.empty:
            return None
        else:
            id_records = id_records.rename({0: "ee_site_id", 1: "point_id", 2: "timestamp", 3: "n", 4: "real_power", 5: "apparent_power", 6: "pf"}, axis=1)
    except Exception as ex:
        print("Error getting this ID's records:", ex)
    try:
        # Filter down to the specified time range's records
        start_datetime = datetime.strptime(config.START_DATE, '%Y-%m-%d').replace(tzinfo=ZoneInfo("UTC"))
        end_datetime = datetime.strptime(config.END_DATE, '%Y-%m-%d').replace(tzinfo=ZoneInfo("UTC")) + pd.Timedelta(1, "d") - pd.Timedelta(15, "min")
        # timestamp should be index for this to work
        id_records['timestamp'] = pd.to_datetime(id_records['timestamp'],unit='s').apply(replace_timezone)
        old_index = id_records["timestamp"].copy() # For comparison of imputation
        id_records = id_records.set_index("timestamp")
        # Do the actual filtering
        id_records = id_records[start_datetime:end_datetime].drop_duplicates()
        naframe = id_records["real_power"].notna()
    except Exception as ex:
        print("Failed to filter date range:", ex)
    try:
        # Easiest way to test without small gaps being included: impute it
        # Fill in missing timestamps
        if config.PERMITTED_GAP_RECORDS != 0:
            fifteen_min_increments = pd.date_range(start=start_datetime, end=end_datetime, freq="15min", tz=UTC, normalize=True, inclusive="left")
            new_index = pd.Index(fifteen_min_increments, name="timestamp")
            id_records = id_records.reindex(index=new_index, method="nearest", limit=config.PERMITTED_GAP_RECORDS)
            id_records["duration"] = 15 # Mark the time interval of the fills
            id_records["raw_data_present"] = new_index.isin(old_index)
    except Exception as ex:
        print(f"Error mock-imputing for id {id}:", ex)
    try:
        naframe = id_records["real_power"].notna()
        existing_records = naframe[naframe == True].count() # Supposedly excludes NA rows
        readings_per_day = 24 * 4 # 96 intervals in a day- 24 hours, 4 intervals per hour
        max_readings_in_period = readings_per_day * int((datetime.strptime(config.END_DATE, '%Y-%m-%d') \
                                                             - datetime.strptime(config.START_DATE, '%Y-%m-%d')).days) + 1
        min_valid_results = floor(max_readings_in_period * config.REQUIRED_PORTION) # Number required to accept the site
        # Finally, validate that enough data exists in the site for usage
        if existing_records < min_valid_results: # AKA: not enough data for that point in this time period
            #print(id, f"is invalid: {existing_records} records, which is less than {min_valid_results} required.")
            return None
        else:
            #print(id, f"is valid: {existing_records} records, which is greater than or equal to {min_valid_results} required.")
            return id # ID is valid
    except Exception as ex:
        print(f"Error testing validity for id {id}:", ex)
        return None


# Get records for those IDs so we can test them
def pickle_data(id):
    try:
        if not exists(f"./pickled-meters/{id}-data.pkl"):
            query = f"SELECT * FROM POWER WHERE point_id == {id};"
            print(f"Fetching {id}...")
            with DBConn.create_connection(config.DATABASE) as conn:
                results = conn.execute(query)
                fetched_records = results.fetchall() # ID count is small enough for fetchall() to be non-issue
            meter_records = pd.DataFrame(fetched_records)
            # Avoid having to do this again
            # NOTE: columns correspond to the following:
            # 0: ee_site_id
            # 1: point_id
            # 2: timestamp, Unix time
            # 3: number of readings in time interval
            # 4: real_power
            # 5: apparent_power
            # 6: power factor
            meter_records.to_pickle(f"./pickled-meters/{id}-data.pkl")
        else:
            print(id, "exists, continuing...")
    except Exception as ex:
        print(f"Could not read or pickle meter {id}: {ex}")

def get_valid_ids(threshold, id_list):
    print(f"Threshold: {threshold}%")
    threshold = threshold / 100
    config.REQUIRED_PORTION = threshold
    try:
        with multiprocessing.Pool() as pool:
            valid_ids = pool.map(test_id, id_list)
    except KeyboardInterrupt:
        print("Stopping.")
    except Exception as ex:
        print("Error initializing pool:", ex)
    valid_ids = [x for x in valid_ids if x is not None] # Removing failed ids
    return valid_ids

# Gets a set of random building ids; used to create buildings
# rng: randomizer object used to select ids 
def get_valid_id_counts(mode):
    # Get possible IDs to choose from
    print("Selecting mains building IDs.")
    if not exists("ids.pkl"):
        try:
            with DBConn.create_connection(config.DATABASE) as conn:
                query = "SELECT DISTINCT point_id FROM LABELS WHERE LABELS.circuit_label_type_id IN (15,16)" # Only mains
                if config.LIMIT_DATE == True:
                    # Buildings don't always start on the first available day. Only include those that do start
                    # before or on the start date to avoid large missing chunks of data
                    query = query + f" AND day_zero_dt <= '{config.START_DATE}'"
                results = conn.execute(query + ";")
                ids = results.fetchall() # ID count is small enough for fetchall() to be non-issue
                ids = tuple([x for xx in ids for x in xx])
                with open("ids.pkl", "wb") as outfile:
                    pickle.dump(ids, outfile)
                # Read in the files
                with multiprocessing.Pool() as pool:
                    mapped = pool.map(pickle_data, ids)
                # "it is recommended that applications run "PRAGMA optimize" (with no arguments) 
                # just before closing each database connection."
                # https://www.sqlite.org/pragma.html#pragma_optimize
                cursor_obj = conn.cursor()
                cursor_obj.execute("PRAGMA optimize;")
                cursor_obj.close()
            # Avoid having to do this again
            print("Fetched.")
        except Exception as ex:
            print("Data could not be fetched:", ex)
    else:
        with open("ids.pkl", "rb") as infile:
            ids = pickle.load(infile)
            # 390 mains IDs total
    try:
        if mode == "count":
            # Test validity of IDs
            print("Testing IDs.")
            valid_ids_per_threshold = {}
            # Alas, range does not allow 0.5 steps
            for threshold in [950, 1000, 5]:
                threshold = threshold / 10
            #for threshold in range(0,50,10):
            #for threshold in range(50, 90, 5):
                valid_ids = list(get_valid_ids(threshold, ids))
                valid_ids_per_threshold[threshold] = len(valid_ids)
            return valid_ids_per_threshold
        elif mode == "sample":
            sample_size = 3
            threshold = 0.99
            valid_ids = get_valid_ids(threshold, ids)
            chosen_ids = sample(valid_ids, k=sample_size)
            print(f"Selected IDs: {chosen_ids}")
            return chosen_ids
    except Exception as ex:
        print("Error:", ex)
        return {}

def graph_valid_id_counts(valid_id_counts):
    count_frame = pd.Series(valid_id_counts)
    print(count_frame)
    title = f"Number of Valid Meters by Percent Data Existing (Maximum Ignored Missing Consecutive Records = {config.PERMITTED_GAP_RECORDS}), 2023"
    fig = px.bar(count_frame, title=title)
    fig.show()

def graph_random_sample_valid_ids(sample):
    # Retrieve ID energy usage for sampled ids
    data = Building.query_for_sites(config.DATABASE, sample, config.START_DATE, config.END_DATE)
    print(data)
    graphdata = data["real_power"]
    graphdata["timestamp"] = data["timestamp"]
    for id in sample:
        pass # Get data, make graph in Plotly, compile it all

def main():
    print("This script can either graph the number of valid IDs per threshold or graph a random sample of valid ids.")
    print("To view the count of valid IDs per threshold, enter 1.")
    print("To view a random sample of valid ids, enter 2.")
    mode = input("Enter selection: ")
    if str(mode) == "1":
        valid_id_counts = get_valid_id_counts(mode="count")
        graph_valid_id_counts(valid_id_counts)
    elif str(mode) == "2":
        valid_id_sample = get_valid_id_counts(mode="sample")
        graph_random_sample_valid_ids(valid_id_sample)

if __name__ == "__main__":
    main()
