from pathlib import Path
import pandas as pd

dir = Path('imputed-csv-files')
files = [file for file in dir.iterdir() if file.is_file()]

for file in files:
    df = pd.read_csv(file, usecols=['real_power'])
    if (df['real_power'] < 0).any():
        print(1)