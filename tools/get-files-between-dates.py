from multiprocessing import freeze_support
from config import POWER_DIR, PREP_FILES, CREATE_STATISTICS
from list_files import list_files_in_dir
from building_analysis.reader import Reader

import pandas
import datetime as dt
from datetime import timedelta

# Directory for prepped data
OUTPUT_DIR = "./output/"
#SEED = 482249327

def convert_datetime(target):
    return dt.datetime.strptime(target, '%Y-%m-%d')

# TODO: Bound dates - let user know if data does not exist for a range and 
# exclude missing time range from results
# TODO: prevent directory traversal. Watch for ".." and similar attempts to list
# files that shouldn't be listed.
def get_files_for_date_range(start_date, end_date):
    #files = list_files_in_dir()
    # Find where to start in first year
    start_date = convert_datetime(start_date)
    # Find where to end in last year
    end_date = convert_datetime(end_date)
    # Get years (used to look inside the correct folders)
    start_year = start_date.year
    end_year = end_date.year
    if start_year != end_year:
        all_dates = pandas.date_range(start_date, end_date, freq="d")
        date_paths = []
        for date in all_dates:
            # In case date was passed as a datetime object
            if not isinstance(date, str):
                date = date.strftime('%Y-%m-%d')
            # Format date into the path to its corresponding file
            # /output/yyyy/yyyy-mm-dd.csv
                date_paths.append(OUTPUT_DIR + date[:4] + "/" + date + ".csv")
    # Get a list of files that actually exist
    # Files are sorted by year, so we need to get the years to compile
    # Get a list of years by appending year ends to year starts, formatting to just the years, and keeping only unique
        all_years_raw = pandas.date_range(start_date, end_date, freq="YE").append(pandas.date_range(start_date, end_date, freq="YS"))
        all_years = []
        for year in all_years_raw:
            all_years.append(year.strftime('%Y'))
    # List files for all years being queried
    existing_files = []
    for year in all_years:
        existing_files += list_files_in_dir("./output/" + year, True)
    # Get the files that actually exist in the output dir
    # Only return ones that actually exist- we don't want to call files that aren't there
    date_set = frozenset(date_paths)
    available_file_paths = [path for path in date_set if path in existing_files]
    return sorted(available_file_paths)

def main():
    paths = get_files_for_date_range("2022-07-05", "2023-04-02")
    print(paths)

"""
        # Get a list of years by appending year ends to year starts, formatting to just the years, and keeping only unique
        all_years_raw = pandas.date_range(start_date, end_date, freq="YE").append(pandas.date_range(start_date, end_date, freq="YS"))
        all_years = []
        for year in all_years_raw:
            all_years.append(year.strftime('%Y'))
"""

    #reader = Reader(TEST_FILE)
    #data = reader.get_data().head(1)
    
# Thanks, multiprocessing
if __name__ == '__main__':
    freeze_support()
    main()