import pandas as pd
import sys
import traceback
sys.path.append('/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation/processor')
sys.path.append('/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation')

from numpy import random
from typing import Optional
import datetime as dt
from collections import defaultdict 
# from datetime import datetime
from math import floor, isnan
import multiprocessing
import pickle
from os.path import exists
from zoneinfo import ZoneInfo
from processor.commonDB import DBConn
import config
import plotly.express as px
from random import sample
from json import dump

# Script written to determine where/when gaps occur in data after imputation.
# Allows the creation of graphs and JSON to record gap locations.
# Intended to be run directly.

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

# Help filter real power column for zeros and determine if they are valid or not 
def majority_true(window):
    return window.sum() > (len(window) // 2)

def filter_zeros(df):
    df['is_zero'] = df['real_power'] < .1
    df['true_zero'] = df['is_zero'].rolling(window = 5, center = True, min_periods = 5).apply(majority_true, raw = False).astype(bool)
    true_zero_list = df['true_zero'].to_list()  
    index = 0 
    zero_gaps = []
    total_zero_gaps = 0

    while index < len(true_zero_list): 
        if true_zero_list[index] == True:
            start = index 

            while index < len(true_zero_list) and true_zero_list[index] == True: 
                index += 1 
            
            end = index - 1 
            length = end - start + 1 
            zero_gaps.append(length) 
            total_zero_gaps += length
        else:
            index += 1 

    return zero_gaps, total_zero_gaps


# Help process site ids for gaps, allowed gaps are configured in config.py file. 
def process_id_gaps(real_power_list): 
    gap_map = defaultdict(list)
    index = 0 

    while index < len(real_power_list):
        if isnan(real_power_list[index]):
            start_index = index
            while index < len(real_power_list) and isnan(real_power_list[index]):
                index += 1 
            
            end_index = index - 1 
            length = end_index - start_index + 1

            if length > config.GAP_PARAMETER:
                # row_string = f'{start_index}-{end_index}'
                gap_map[length].append((start_index, end_index))
            else:
                continue
        else:
            index += 1

    return gap_map


# Explicit cast to UTC; it's already in UTC but this makes it aware
def replace_timezone(x):
    return x.replace(tzinfo=ZoneInfo("UTC"))

# Used to validate that data exists within this period;
# dates are stored as Unix timestamps, so start/end datetimes need to match formats to compare
start = replace_timezone(dt.datetime.strptime(config.START_DATE, '%Y-%m-%d'))
end = replace_timezone(dt.datetime.strptime(config.END_DATE, '%Y-%m-%d'))

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

def get_records(id):
    try:
        with open(f"/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation/pickled-meters/{id}-data.pkl", "rb") as infile:
            id_records = pickle.load(infile)
        if id_records.empty:
            return None
        id_records = id_records.rename({0: "ee_site_id", 1: "point_id", 2: "timestamp", 3: "n", 4: "real_power", 5: "apparent_power", 6: "pf"}, axis=1)
    except Exception as ex:
        print("Error getting this ID's records:", ex)
    try:
        id_records['placeholder-timestamp'] = id_records['timestamp']
        # timestamp should be index for this to work
        if "timestamp" in id_records.columns:
            id_records['timestamp'] = pd.to_datetime(id_records['timestamp'],unit='s').apply(replace_timezone)
        #id_records = id_records.set_index("timestamp")
    except:
        print("Could not prepare records.")
        return None
    return id_records
        
# IF THE TEST_ID IN CREATE_BUILDINGS FAILS:
# try porting this one over. Confirmed it works 2025-08-29
def test_id(id):
    UTC = ZoneInfo("UTC")
    id_records = get_records(id)
    try:
        if type(id_records) == "NoneType" or id_records is None:
            return None
        old_index = id_records["timestamp"].copy() # For comparison of imputation
        # id_records['placeholder-timestamp'] = id_records['timestamp']
        id_records['timestamp'] = pd.to_datetime(id_records['timestamp'],unit='s').apply(replace_timezone)
        
        

        id_records = id_records.set_index("timestamp")

        # Important, setting index first and then dropping duplicates leads to relying on column p
        # Drop before setting index 
        if not id_records.empty:
            if id == 25291:
                id_records = id_records[start:end].drop_duplicates()
        else:
            return None

        id_records.drop('placeholder-timestamp', axis = 1, inplace = True)
        
        # Do the actual filtering
        
    except Exception as ex:
        print("Failed to filter date range:", ex)
        return None
    try:
        # Easiest way to test without small gaps being included: impute it
        # Fill in missing timestamps
        if config.PERMITTED_GAP_RECORDS != 0:
            id_records_copy_pd = id_records.copy()
            id_records_copy_pd = id_records_copy_pd.reset_index()
            id_records_copy_pd['epoch'] = (id_records_copy_pd['timestamp'] - dt.datetime(1970,1,1, tzinfo = dt.timezone.utc)).dt.total_seconds()
            id_records_copy_pd['epoch'] = id_records_copy_pd['epoch'].astype('Int64')
            all_time_entries = pd.date_range(start=start, end=end, freq="15min", tz=UTC, inclusive = "left") #Ensures that the start date is included, but the end date is not
            all_time_entries_pd = pd.DataFrame({'timestamp' : all_time_entries})
            all_time_entries_pd['epoch'] = (all_time_entries_pd['timestamp'] - dt.datetime(1970,1,1, tzinfo = dt.timezone.utc)).dt.total_seconds()
            all_time_entries_pd['epoch'] = all_time_entries_pd['epoch'].astype('Int64')

            start_epoch=int(min(all_time_entries_pd['epoch']))
            end_epoch=int(max(all_time_entries_pd['epoch']))
            available_entries_by_minmax = id_records_copy_pd[(id_records_copy_pd['epoch'] >= start_epoch) & (id_records_copy_pd['epoch'] <= end_epoch)]
            print(id, start_epoch, end_epoch)
            #raw_records_df = id_records[id_records.index.isin(raw_records)].copy()
            available_entries = pd.merge(left=all_time_entries_pd, right=id_records_copy_pd, on = ['epoch'], how = 'inner')

            if len(available_entries_by_minmax)!=len(available_entries):
                print("error!!")

            available_slots= pd.merge(left=all_time_entries_pd,right= id_records_copy_pd, on = ['epoch'], how = 'left' )
            
            # raw_records_df = id_records.loc[raw_records]
            # raw_records_df = pd.DataFrame(raw_records)
            fifteen_min_increments = pd.date_range(start=start, end=end, freq="15min", tz=UTC, normalize=True, inclusive="left")
            new_index = pd.Index(fifteen_min_increments, name="timestamp")
            id_records = id_records.reindex(index=new_index, method="nearest", limit=config.PERMITTED_GAP_RECORDS)
            id_records["duration"] = 15 # Mark the time interval of the fills
            id_records["raw_data_present"] = new_index.isin(old_index)
    except Exception as ex:
        print(f"Error mock-imputing for id {id}:", ex)
        return None
    try:
        naframe = id_records["real_power"].notna()
        naframe_copy = naframe.copy()
        naframe_df = naframe_copy[naframe_copy == True]
        existing_records = naframe[naframe == True].count() # Supposedly excludes NA rows
        

        # Checking na count before and after update
        available_slots_na = available_slots['real_power'].notna()
        available_slots_na = available_slots_na[available_slots_na == False].count()
        available_slots_copy = available_slots.copy()
        print(f'id={id}, slots={len(all_time_entries_pd)}, seats={len(available_entries)}, syd={existing_records}, NA count={available_slots_na}')

        # After update  
        # # available_slots_copy.update(available_entries)

        # Checking after update 
        # # available_slots_na = available_slots_copy['real_power'].notnull()
        # # available_slots_na = available_slots_na[available_slots_na == False].count()

        # real_power_array = available_slots_copy['real_power']
        # real_power_array.to_csv('real_power.csv')

        # # print(f'After update, na count : {available_slots_na}')

        # Returns a map whose keys represent the length of the gap, and values are the row numbers
        pointid_gap_map = process_id_gaps(available_slots_copy['real_power'].to_list())
        zero_gap_list, total_zero_gaps = filter_zeros(available_slots_copy)
        

        if len(available_entries) != len(available_slots):
            #raw_records_df.to_csv('raw.csv')
            print(pointid_gap_map)
            print(f'total zero list : {zero_gap_list}')
            print(f'biggest gap : {max(zero_gap_list)}')
            print(f'total zeros gaps : {total_zero_gaps}')

            if len(available_entries) + available_slots_na != len(available_slots):
                pointid_gap_map = process_id_gaps(available_slots_copy['real_power'].to_list())
                zero_gap_list, total_zero_gaps = filter_zeros(available_slots_copy)
                print(f'total zero list : {zero_gap_list}')
                print(f'total zeros gaps : {total_zero_gaps}')

                # available_entries.to_csv('available_entries.csv')
                # available_slots.to_csv('available_slots.csv')
                # all_time_entries_pd.to_csv('all_time_entries.csv')
                # naframe_df.to_csv('naframe.csv')
                print('ERROR WE GET HERE')
        readings_per_day = 24 * 4 # 96 intervals in a day- 24 hours, 4 _pdintervals per hour
        max_readings_in_period = readings_per_day * int((dt.datetime.strptime(config.END_DATE, '%Y-%m-%d') \
                                                             - dt.datetime.strptime(config.START_DATE, '%Y-%m-%d')).days) + 1
        min_valid_results = floor(max_readings_in_period * config.REQUIRED_PORTION) # Number required to accept the site
        # Finally, validate that enough data exists in the site for usage
        

        # if id == 25665:
        #     print(1)

        if existing_records >= min_valid_results: # ID is valid
            if max(zero_gap_list) <= 100 and total_zero_gaps <= 96:
                print(zero_gap_list)
                print('*' * 40 + '\n')
                return id,id, available_slots_na, pointid_gap_map
            else: 
                return None
        else:
            if max(zero_gap_list) <= 100 and total_zero_gaps <= 96:
                print(zero_gap_list)
                print('*' * 40 + '\n')
                return None,id, available_slots_na, pointid_gap_map  # AKA: not enough data for that point in this time period
            else:
                return None 
    except Exception as ex:
        print(f"Error testing validity for id {id}:", ex)
        traceback.print_exc()
        print()
        return None,None,None
# Get records for those IDs so we can test them
def pickle_data(id):
    try:
        if not exists(f"/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation/pickled-meters/{id}-data.pkl"):
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
            meter_records.to_pickle(f"/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation/pickled-meters/{id}-data.pkl")
        else:
            print(id, "exists, continuing...")
    except Exception as ex:
        print(f"Could not read or pickle meter {id}: {ex}")

def get_valid_ids(threshold, id_list):
    print(f"Threshold: {threshold}%")
    threshold = threshold / 100
    config.REQUIRED_PORTION = threshold
    try:
        mp=True
        if mp==True:
            with multiprocessing.Pool(processes=1) as pool:
                results = pool.map(test_id, id_list)
        else:
            results=[]
            for id in id_list:
                results+=[test_id(id)]
            # print(results)
    except KeyboardInterrupt:
        print("Stopping.")
    except Exception as ex:
        print("Error initializing pool:", ex)
    # valid_ids = [x for x in valid_ids if x is not None] # Removing failed ids
    valid_ids = [] 
    id_count_map = {} 
    total_gap_map = {}
    for result in results:
        if result is not None:
            valid, id, records, pointid_gap_map = result
            total_gap_map[id] = pointid_gap_map
            valid_ids.append(id)
            id_count_map[id] = records

    return valid_ids, id_count_map, total_gap_map

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
            for threshold in [900]:
                threshold = threshold / 10
            #for threshold in range(0,50,10):
            #for threshold in range(50, 90, 5):
                valid_ids, id_count_map, total_gap_map = get_valid_ids(threshold, ids)
                # print(total_gap_map)

                result = {} 

                # print(f'Threshold : {threshold} : {valid_ids}')
                
                cleaned_map = {k : int(v) for k, v in id_count_map.items()}
                sorted_map = sorted(cleaned_map.items(), key = lambda x : x[1], reverse = False)
                top_100_map = dict(sorted_map[:100])

                new_result = {}

                for key,value in total_gap_map.items():
                    flag = True 
                    for length in value:
                        if length != 4:
                            flag = False
                            break

                    if flag:
                        new_result[key] = value 

                
                print(f'Length of new result : {len(new_result)}')
                print(new_result)
                print()


                for key in top_100_map.keys():
                    keep_flag = True
                    gap_list = total_gap_map[key]

                    for gap in gap_list.keys():
                        if gap != 4:
                            keep_flag = False 
                            break
                    
                    if keep_flag:
                        result[key] = total_gap_map[key]                

                print()
                print(f'Length of result : {result}')
                for key,value in result.items():
                    print(key,value)

                gap_key_list = list(new_result.keys())

                with open('valid-keys.pkl', 'wb') as file:
                    pickle.dump(gap_key_list, file)

                # print(top_100_map)
                filename = f'/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation/valid-outputs/{config.START_DATE}-{config.END_DATE}.json'
                with open(filename, 'w') as file:
                    dump(top_100_map, file, indent = 4)
                
                with open(f"valid-ids-{threshold}.pkl", "wb") as file:
                    pickle.dump(valid_ids, file)
                valid_ids_per_threshold[threshold] = len(valid_ids)
            return valid_ids_per_threshold, result
        elif mode == "sample":
            sample_size = 50 # Must be <= total number of meters in valid meter set
            threshold = 0.995 # Must be between 0 and 1
            if exists(f"valid-ids-{threshold}.pkl"): # Save some processing time
                with open(f"valid-ids-{threshold}.pkl", "rb") as infile:
                    valid_ids = pickle.load(infile)
            else:
                valid_ids = get_valid_ids(threshold * 100, ids)
                with open(f"valid-ids-{threshold}.pkl", "wb") as file:
                    pickle.dump(valid_ids, file)
            chosen_ids = sample(valid_ids, k=sample_size)
            print(f"Selected IDs: {chosen_ids}")
            return chosen_ids
        else:
            threshold = 0.995 # Must be between 0 and 1
            if exists(f"valid-ids-{threshold}.pkl"): # Save some processing time
                with open(f"valid-ids-{threshold}.pkl", "rb") as infile:
                    valid_ids = pickle.load(infile)
            else:
                valid_ids = get_valid_ids(threshold * 100, ids)
                with open(f"valid-ids-{threshold}.pkl", "wb") as file:
                    pickle.dump(valid_ids, file)
            return valid_ids
    except Exception as ex:
        print("Error:", ex)
        return {}

# Used to chart how many IDs are valid at different threshold values
def graph_valid_id_counts(valid_id_counts):
    count_frame = pd.Series(valid_id_counts)
    print(count_frame)
    # I'm so sorry, but you need to change the title's year manually right now
    # Easy tweak, just didn't have time
    title = f"Number of Valid Meters by Percent Data Existing (Maximum Ignored Missing Consecutive Records = {config.PERMITTED_GAP_RECORDS}), 2023"
    fig = px.bar(count_frame, title=title)
    fig.show()

# Graphs and exports to JSON information about gaps post-imputation
def graph_random_sample_valid_ids(sample, graph: Optional[bool] = True):
    # Retrieve ID energy usage for sampled ids
    start = datetime.strptime(config.START_DATE, '%Y-%m-%d').replace(tzinfo=ZoneInfo("UTC"))
    end = datetime.strptime(config.END_DATE, '%Y-%m-%d').replace(tzinfo=ZoneInfo("UTC")) + pd.Timedelta(1, "d") - pd.Timedelta(15, "min")
    # Fill in any missing times
    fifteen_min_increments = pd.date_range(start=start, end=end, freq="15min", tz=ZoneInfo("UTC"), normalize=True, inclusive="left")
    new_index = pd.Index(fifteen_min_increments, name="timestamp")
    # For each record, impute and save as a column to graph
    counter = 0
    for id in sample:
        this_id = get_records(id)
        this_id = this_id.set_index("timestamp")
        this_id = this_id[start:end].drop_duplicates()
        this_id = this_id.reindex(index=new_index, method="nearest", limit=config.PERMITTED_GAP_RECORDS)
        if "graphdata" not in locals():
            graphdata = pd.DataFrame()
        graphdata[id] = this_id["real_power"]
        counter += 1
        # PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, 
        # which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. 
        # To get a de-fragmented frame, use `newframe = frame.copy()`
        if counter > 50:
            graphdata = graphdata.copy()
    # Get data, make graph in Plotly, compile it all
    if graph:
        title = "Random sample of valid meters"
        fig = px.line(graphdata, title=title)
        fig.update_traces(opacity=.4)
        fig.show()
        fig.write_html("random_valid_ids.html")
    else:
        # Save missing times to a JSON file
        with open("sampled-gaps.json", "a") as outfile:
            output = {}
            for col in graphdata.columns:
                id = str(col)
                output[id] = {}
                output[id]["maxGapSizeImputed"] = str(config.PERMITTED_GAP_RECORDS)
                naframe = graphdata[col].notna()
                output[id]["recordCount"] = str(naframe[naframe == True].count())
                output[id]["gapTimes"] = []
                gaps = naframe[naframe == False].index.to_list()
                for x in gaps:
                    output[id]["gapTimes"].append(x.isoformat())
            dump(output, outfile)

def main():
    print("This script can either graph the number of valid IDs per threshold or graph a random sample of valid ids.")
    print("To view the count of valid IDs per threshold, enter 1.")
    print("To view a random sample of valid ids, enter 2.")
    print("To output text files describing gap characteristics of all meters, enter 3.")
    #mode = input("Enter selection: ")
    mode='1'
    if str(mode) == "1":
        valid_id_counts = get_valid_id_counts(mode="count")
        graph_valid_id_counts(valid_id_counts)
    elif str(mode) == "2":
        valid_id_sample = get_valid_id_counts(mode="sample")
        graph_random_sample_valid_ids(valid_id_sample)
    elif str(mode) == "3":
        valid_ids = get_valid_id_counts(mode="all")
        graph_random_sample_valid_ids(valid_ids, graph=False)

if __name__ == "__main__":
    main()
