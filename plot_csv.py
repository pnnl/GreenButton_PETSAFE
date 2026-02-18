import random 
import os
import plotly.express as px
import pandas as pd

output_path = 'interpolated-output'
input_path = '/home/ubuntu/PETSAFE/interpolated-csv-files/'

def improved_find_gaps(df):
    """Improved gap finding with better debugging"""
    power_col = 'real_power' if 'real_power' in df.columns else 'power'
    
    if df[power_col].dtype == 'object':
        print("Converting object column to numeric...")
        df[power_col] = pd.to_numeric(df[power_col], errors='coerce')
    
    is_nan = df[power_col].isnull()
    print(f"Total NaN values found: {is_nan.sum()}")
    
    if is_nan.sum() == 0:
        print("No gaps found!")
        return []
    
    nan_indices = df.index[is_nan].tolist()
    print(f"NaN indices: {nan_indices[:10]}..." if len(nan_indices) > 10 else f"NaN indices: {nan_indices}")
    
    nan_diff = is_nan.diff()
    gap_starts = df.index[nan_diff & is_nan].tolist()
    gap_ends = df.index[nan_diff.shift(-1) & is_nan].tolist()
    
    if len(df) > 0 and is_nan.iloc[0]:
        gap_starts.insert(0, df.index[0])
    if len(df) > 0 and is_nan.iloc[-1]:
        gap_ends.append(df.index[-1])
    
    print(f"Gap starts: {gap_starts}")
    print(f"Gap ends: {gap_ends}")
    
    gaps = []
    for start, end in zip(gap_starts, gap_ends):
        try:
            start_idx = df.index.get_loc(start)
            end_idx = df.index.get_loc(end)
            gaps.append((start_idx, end_idx))
            print(f"Gap found: indices {start_idx} to {end_idx}")
        except KeyError as e:
            print(f"Error getting location for gap: {e}")
    
    return gaps

def search_negative_values(csv_files): 
    for csv in csv_files:
        df = pd.read_csv(input_path + csv, usecols=['real_power'])
        mask = df['real_power'] < 0 
        if len(df[mask]) != 0: 
            print(csv)
            

def main():
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    csv_files = [f for f in os.listdir(input_path)
             if f.endswith('.csv') and os.path.isfile(os.path.join(input_path, f))]

    # search_negative_values(csv_files)

    
    for csv in csv_files: 
        name = csv.split('.')[0]
        df = pd.read_csv(input_path + csv)
        print(name)
        gaps = improved_find_gaps(df)
        print('-' * 60)
        print(gaps)
        # new_df = df[['timestamp_x', 'real_power']]

        # figure = px.line(new_df, x = 'timestamp_x', y = 'real_power', title = name + ' Plot')
        # filename = output_path + f"/{name}.html"
        # figure.write_html(filename)

    
main()