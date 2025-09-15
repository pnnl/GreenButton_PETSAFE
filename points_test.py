import pandas as pd 
import csv 
import numpy as np 

POINT_CSV_PATH = 'points.csv'
OUTPUT_CSV_PATH = 'updated_points.csv'


points_df = pd.read_csv(POINT_CSV_PATH)


points_df['day_zero_dt'] = points_df['day_zero_dt'].str.split(' ').str.get(0)

points_df['point_id'] = points_df['point_id'].astype('Int64')
points_df['circuit_label_type_id'] = points_df['circuit_label_type_id'].astype('Int64')

string_cols_for_quoting = [
    'regname',
    'circuit_label_type_desc',
    'circuit_label',
    'day_zero_dt' 
]
for col in string_cols_for_quoting:
    points_df[col] = points_df[col].astype(str)



points_df.to_csv(
    OUTPUT_CSV_PATH,
    index=False,
    quoting=csv.QUOTE_NONNUMERIC,
    na_rep='NA'                 
)

print(f"Processed data saved to {OUTPUT_CSV_PATH}")
