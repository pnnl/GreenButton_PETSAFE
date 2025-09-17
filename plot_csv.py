import random 
import os
import plotly.express as px
import pandas as pd

output_path = 'csv-plot-output'
input_path = '/home/ubuntu/PETSAFE/interpolated-csv-files/'

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

    search_negative_values(csv_files)

    
    # for csv in csv_files: 
    #     name = csv.split('.')[0]
    #     df = pd.read_csv(input_path + csv)
    #     new_df = df[['timestamp_x', 'real_power']]

    #     figure = px.line(new_df, x = 'timestamp_x', y = 'real_power', title = name + ' Plot')
    #     filename = output_path + f"/{name}.html"
    #     figure.write_html(filename)

    
main()