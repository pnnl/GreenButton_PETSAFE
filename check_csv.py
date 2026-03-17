import pandas as pd 
import pickle
from collections import defaultdict
import datetime as dt 
from pathlib import Path
import math
import setup.exports_imports.building_aggregation.graph_building_validity as gbv
import setup.exports_imports.building_aggregation.processor.commonDB as db
import setup.exports_imports.building_aggregation.config as config

file_idpkl = '/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation/ids.pkl'
file_realpower = 'real_power.csv'
rename_map = {0: "ee_site_id", 1: "point_id", 2: "timestamp", 3: "n", 4: "real_power", 5: "apparent_power", 6: "pf"}

def query_id(point_id):
    query = f'SELECT * FROM POWER WHERE point_id == {point_id};'  
    with db.DBConn.create_connection(config.DATABASE) as conn: 
        results = conn.execute(query)
        fetched_records = results.fetchall()
    
    meter_df = pd.DataFrame(fetched_records)
    meter_df = meter_df.rename(columns = rename_map)
    meter_df = meter_df.sort_values(by = 'timestamp')
    return meter_df

def validate_csv_files():
    valid_id = []
    invalid_id = []

    with open(file_idpkl, 'rb') as file: 
        id_list = pickle.load(file)

    for point_id in id_list:
        print(f'Processing point id: {point_id}')
        pickle_df = gbv.get_records(point_id) 
        if pickle_df is not None:
            pickle_df['timestamp'] = pd.to_datetime(pickle_df['timestamp'])
            pickle_df['timestamp'] = pickle_df['timestamp'].astype('int64') // 10 ** 9
            pickle_df = pickle_df.sort_values(by = 'timestamp') 
            sqlite_df = query_id(point_id) 

            if sqlite_df.equals(pickle_df):
                valid_id.append(point_id)
            else:
                invalid_id.append(point_id)

        print(f'Finished processing point id: {point_id}')

    print(f'Valid ids: {valid_id}')
    print(f'Invalid ids: {invalid_id}')

def majority_true(window):
    return window.sum() > (len(window) // 2)

def filter_zeros(df):
    df['is_zero'] = df['real_power'] < .1
    df['true_zero'] = df['is_zero'].rolling(window = 5, center = True).apply(majority_true, raw = False).astype(bool)
    true_zero_list = df['true_zero'].to_list()  
    index = 0 
    zero_gaps = []

    while index < len(true_zero_list): 
        if true_zero_list[index] == True:
            start = index 

            while index < len(true_zero_list) and true_zero_list[index] == True: 
                index += 1 
            
            end = index - 1 
            length = end - start + 1 
            zero_gaps.append(length) 

    return max(zero_gaps)


def process_gap_id(real_power_list, gap_parameter): 
    gap_map = defaultdict(list)

    index = 0
    nan_counter = 0 
    while index < len(real_power_list):
        if math.isnan(real_power_list[index]):
            start_index = index 
            while index < len(real_power_list) and math.isnan(real_power_list[index]):            
                index += 1 

            end_index = index - 1
            length = end_index - start_index + 1

            if length > gap_parameter:
                if start_index == end_index:
                    row_string = start_index
                else:
                    row_string = f'{start_index}-{end_index}'
                gap_map[length].append(row_string)
            else:
                continue
        else:
            index += 1

    for key,value in gap_map.items():
        print(key, value)
        print()

if __name__ == '__main__':
    real_power_df = pd.read_csv(file_realpower, index_col=0)
    filter_zeros(real_power_df)
    # gap_parameter = 0

    # # validate_csv_files()

    # # Map, key contains length of the gap, value contains string that shows row numbers e.g (1245) or (1200-1222)
    # process_gap_id(real_power_df['real_power'].to_list(), gap_parameter)

    

    


        