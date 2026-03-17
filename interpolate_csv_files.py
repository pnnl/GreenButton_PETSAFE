import setup.exports_imports.building_aggregation.graph_building_validity as gbv
import setup.exports_imports.building_aggregation.config as config
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd
from pathlib import Path
import pickle
import numpy as np

gap_key_file = 'valid-keys.pkl'
output_directory = 'interpolated-csv-files'
csv_compare = 'compare-csv'

start = "2021-01-01"
end = "2022-01-01"

# def majority_true(window):
#     return window.sum() > (len(window) // 2)

# def filter_zeros(df):
#     df['is_zero'] = df['real_power'] < .1
#     df['true_zero'] = df['is_zero'].rolling(window = 5, center = True, min_periods = 5).apply(majority_true, raw = False).astype(bool)
#     df.loc[df['true_zero'], 'real_power'] = np.nan
#     print(df.info)
#     return df

def majority_true(window):
    return window.sum() > (len(window) / 2)

def filter_zeros(df):
    df['is_zero'] = df['real_power'] < 0.1

    rolling_result = df['is_zero'].rolling(window=5, center=True, min_periods=5).apply(
        majority_true, raw=False
    )

    df['true_zero'] = rolling_result.fillna(False).astype(bool)
    df.loc[df['true_zero'], 'real_power'] = np.nan
    print(df.info())
    return df


def interpolate(df):
    df['pf'] = df['pf'].fillna(1.0)
    df['apparent_power'] = df['apparent_power'].fillna(0.0)
    # df['ee_site_id'] = df['ee_site_id'].fillna(method = 'ffill')
    # df['point_id'] = df['point_id'].fillna(method = 'ffill')
    # df['n'] = df['n'].fillna(method = 'ffill')
    
    df['ee_site_id'] = df['ee_site_id'].ffill()
    df['point_id'] = df['point_id'].ffill()
    df['n'] = df['n'].ffill()
    
    # df['ee_site_id'].ffill(inplace = True)
    # df['point_id'].ffill(inplace = True)
    # df['n'].ffill(inplace = True)

    df['timestamp_y'] = df['timestamp_y'].fillna(df['timestamp_x'])
    df['real_power'] = df['real_power'].interpolate(method = 'spline', order = 1)
    print(df.info())

def replace_timezone(x):
    return x.replace(tzinfo=ZoneInfo("UTC"))

def process_pointid(point_id):
    UTC = ZoneInfo("UTC")
    id_records = gbv.get_records(point_id)
    try:
        if type(id_records) == "NoneType" or id_records is None:
            print('No type')
        old_index = id_records["timestamp"].copy() # For comparison of imputation
        id_records['timestamp'] = pd.to_datetime(id_records['timestamp'],unit='s').apply(replace_timezone)
        id_records['placeholder-timestamp'] = id_records['timestamp']
        

        id_records = id_records.set_index("timestamp")

        # Important, setting index first and then dropping duplicates leads to relying on column p
        # Drop before setting index 
        if not id_records.empty:
            id_records = id_records[start:end].drop_duplicates()
        else:
            print('Id records is empty')

        id_records.drop('placeholder-timestamp', axis = 1, inplace = True)
        
    except Exception as ex:
        print("Failed to filter date range:", ex)
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
            print(point_id, start_epoch, end_epoch)
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

            pointid_gap_map = gbv.process_id_gaps(available_slots['real_power'].to_list())
            print(pointid_gap_map)

            available_slots_copy = available_slots.copy()
            cleaned_available_slots = filter_zeros(available_slots_copy)



            compare_csv_file = Path(f'{csv_compare}/{point_id}.csv')

            if compare_csv_file.exists():
                print(f'Making compare csv file {point_id}')
                available_slots.to_csv(f'{csv_compare}/{point_id}.csv')

            csv_file = Path(f'{output_directory}/{point_id}.csv')

            if not csv_file.exists():
                print(f'Making csv file {point_id}')
                # edited_df = interpolate(available_slots)
                # pointid_gap_map = gbv.process_id_gaps(edited_df['real_power'].to_list())
                print(pointid_gap_map)
                cleaned_available_slots.to_csv(f'{output_directory}/{point_id}.csv')
    except Exception as ex:
        print(f"Error mock-imputing for id {id}:", ex)


def main(): 
    with open(gap_key_file, 'rb') as file:
        gap_list = pickle.load(file)
    

    directory_path = Path(output_directory)

    if not directory_path.exists():
        directory_path.mkdir(parents = True, exist_ok = True)

    directory_path = Path(csv_compare)

    if not directory_path.exists():
        directory_path.mkdir(parents = True, exist_ok = True)

    for point_id in gap_list: 
        process_pointid(point_id)

main()