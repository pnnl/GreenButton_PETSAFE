import pandas as pd
from pathlib import Path

csv_folder = 'interpolated-csv-files'
csv_path = Path(csv_folder)
files = [file for file in csv_path.iterdir() if file.is_file()]


def filter_zeros():
    bad = [] 
    good = []
    threshold = 96
    for file in files: 
        df = pd.read_csv(file.resolve(), usecols=['real_power'])['real_power']
        
        is_zero = df['real_power'] == 0
        
        consecutive_groups = (is_zero != is_zero.shift()).cumsum()
        zero_counts = df[is_zero].groupby(consecutive_groups).count()
        max_zeros = zero_counts.max() if not zero_counts.empty else 0

        if max_zeros >= threshold:
            bad.append(file.name)
        else:
            good.append(file.name)

    
    print(good)
    print()
    print(bad)



filter_zeros()