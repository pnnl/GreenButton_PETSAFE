import pandas
import matplotlib as plt
import plotly.express as px
import datetime as dt
from os import listdir
import os.path
from typing import Optional
from config import OUTPUT_DIR, STAT_TEMPORAL_RESOLUTION, DECRYPT

# Time periods should be in the form yyyy-mm-dd HH:mm
# HH:mm may be missing if time is midnight
class Reader:
    def __init__(
            self,
            start_date: str, # the datetime of the start of the period to read, YY-MM-DD HH-MM expected
            end_date: Optional[str] = None, # the datetime of the start of the period to read, YY-MM-DD HH-MM expected
            resolution: Optional[str] = "15mins" # the resolution to return data at
    ):
        self.__start_datetime = start_date
        self.__end_datetime = end_date
        self.__resolution = resolution
        # TODO: deal with None end datetime
        self.validate_date_range()
        self.__files = self.__get_files_for_date_range(STAT_TEMPORAL_RESOLUTION)
        self.data = self.__build_data_frame()
        self.data = self.change_time_resolution(self.data, self.__resolution)

    # TODO: add more checks for privacy concerns
    def validate_date_range(self):
        if self.__start_datetime > self.__end_datetime:
            print("Start date must be after end date.")
            raise SystemExit

    # Compiles all days within the date range into a single frame for processing
    def __build_data_frame(self):
        frame = pandas.DataFrame()
        print("Building frame (may take a moment for large date ranges)...")
        for file in self.__files:
            try:
                with open(file, "r") as csv_file:
                    data = pandas.read_csv(csv_file)
                data["min_t"] = pandas.to_datetime(data["min_t"])
                data = data.set_index(["min_t"])
            except:
                print("Reader: File not found.")
                data = pandas.DataFrame()
            frame = pandas.concat((frame, data))
        print("Frame built.")
        return frame
    
    # Returns all data in the date range
    def get_data(self):
        return self.data
    
    # Change input resolution string into a consistent format for use in resampling
    def check_resolution(
            self,
            resolution: str # the resolution string
    ):
        resolution = resolution.replace(" ", "").lower() # remove spacing/case differences
        resolution = ''.join(ch for ch in resolution if ch.isalpha()) # isalpha() removes numbers for consistency (1hr -> hr)
        if resolution in ["minutes", "min", "f"]:
            return "15min"
        elif resolution in ["hourly", "hour", "hr","h"]:
            return "60min"
        elif resolution in ["daily", "day", "d"]:
            return "D"
        elif resolution in ["weekly", "week", "w"]:
            return "W"
        elif resolution in ["monthly", "month", "m"]:
            return "M"
        elif resolution in ["yearly", "year", "y"]:
            return "Y"
        else:
            print("Resolution not implemented. Options:")
            print("- 15min")
            print("- hourly")
            print("- daily")
            print("- weekly")
            print("- monthly")
            print("- yearly")
            return None # Resolution not implemented
        
    def change_time_resolution(
            self,
            data, # the dataframe to resample
            resolution: str # the resolution to resample to
    ):
        resolution = self.check_resolution(resolution)
        if (resolution is not None) and (DECRYPT == False):
            # TODO SANITY CHECK: if encrypted w/partial HE, reject this
            try:
                frame = pandas.DataFrame()
                # Work in chunks to preserve site IDs
                for site in pandas.unique(data["ee_site_id"]):
                    chunk = data[data["ee_site_id"] == site]
                    chunk_id = chunk["ee_site_id"].iloc[0]
                    chunk = chunk.resample(resolution).sum()
                    chunk["ee_site_id"] = chunk_id
                    frame = pandas.concat([frame, chunk])
                data = frame
                data["pf"] = data["power"] / data["apparent_power"]
            except Exception as error:
                print("Could not change resolution:", error)
        elif DECRYPT == False:
            print("Resolution not implemented.")
        else:
            print("Resolution not implemented or data encrypted.")
        return data

    def graph_building_power(
            self,
            building_id: int, # The integer ID of the building to work with
            resolution: str # the resolution to graph at.
    ):
        # TODO: Check that data is decrypted; graphing encrypted data makes no sense
        # TODO: if resolution = supplied data, graphing won't work as expected
        try:
            building = self.data[self.data["ee_site_id"] == building_id]
        except KeyError as error:
            print("Key does not exist:", error)
            return None
        building = self.change_time_resolution(building, resolution)
        title = "Real Power for Building " + str(building_id)
        fig = px.line(building, y="power", title=title)
        fig.show()
        return fig
    
    # Returns the sum of power for a building with ee_site_id of building_id
    def get_building_power_sum(
            self, 
            building_id: int # The integer ID of the building to work with
            ):
        try:
            building = self.data[self.data["ee_site_id"] == building_id]
        except KeyError as error:
            print("Key does not exist:", error)
            return None
        # TODO: per time period instead of whole provided period
        return building["power"].sum()
    
    # Gets average power usage for the selected time resolution
    # e.g. a resolution of 1 month returns average total usage for a month of time
    # TODO: Check this works as expected with larger time resolutions
    def get_building_power_avg(
            self, 
            building_id: int # The integer ID of the building to work with
            ):
        sum = self.get_building_power_sum(building_id)
        site_count = self.data[self.data["ee_site_id"] == building_id]["site_count"].iloc[0]
        # Done with multiplication to allow it to be done homomorphically- plaintext scalars
        # are okay for multiplication, not division.
        avg = sum * 1/site_count # scale down to a "site" of usage
        avg = round(avg, 4) # Keep size reasonable for output
        return avg
    
    def get_max(
            self, 
            building_id: int # The integer ID of the building to work with
            ):
        data = self.get_data()
        data = data[data["ee_site_id"] == building_id]
        # encryption sanity check
        if DECRYPT == False:
            return data.max()
        else:
            print("Cannot calculate max on homomorphically encrypted data.")

    def get_min(
            self, 
            building_id: int # The integer ID of the building to work with
            ):
        data = self.get_data()
        data = data[data["ee_site_id"] == building_id]
        # encryption sanity check
        if DECRYPT == False:
            return data.min()
        else:
            print("Cannot calculate min on homomorphically encrypted data.")

    # Converts a datetime string to an object
    def convert_datestr_to_dateobj(self, target):
        return dt.datetime.strptime(target, '%Y-%m-%d')
    
    # Lists files in a given directory. Used to get a list of existing files within
    # the given date range to process
    def __list_files_in_dir(
            self, 
            dir_path: str, # The directory to list
            prepend_path: bool # whether or not to prepend the filepath to the files
            ):
        # TODO: Prevent path traversal by cleaning dir_path
        try:
            files = listdir(dir_path)
            # Format files with directory in front
            if prepend_path == True:
                for file in files:
                    if dir_path[-1] != "/":
                        dir_path += "/"
                    files[files.index(file)] = dir_path + file
                    # Remove directories, just in case
                    if not os.path.isfile(os.path.join(dir_path + file)):
                        files.remove(file)
            return files
        # TODO: Catch specific exception for no files existing
        except:
            print("Could not list files.")

    # Returns a list of files for the selected date range-
    # refines from list_files_in_dir()
    def __get_files_for_date_range(
            self,
            resolution: str, # resolution is used to find processed file directories
            recurse: Optional[bool] = False # Whether function is being called recursively
            ):
        # Convert to datetimes to enable use of .year
        self.__start_date = self.convert_datestr_to_dateobj(self.__start_datetime)
        self.__end_date = self.convert_datestr_to_dateobj(self.__end_datetime)
        # Get years (used to look inside the correct folders)
        start_year = self.__start_date.year
        end_year = self.__end_date.year
        # Deal with different resolution effects on directory name
        resolution = self.check_resolution(resolution)
        match resolution: # Only check for those implemented
            case "15min":
                resolution = "-15mins"
            case "60min":
                resolution = "-hourly"
            case "D":
                resolution = "-daily"
            case __:
                print("Aggregation resolution not implemented. Using daily default.")
                resolution = "-daily"
        # Deal with encryption's effects on directory name
        if DECRYPT == True:
            append = "-encrypted"
        else:
            append = ""
        # TODO: validate that date range size does not violate privacy
        all_dates = pandas.date_range(self.__start_date, self.__end_date, freq="d")
        date_paths = []
        for date in all_dates:
            # In case date was passed as a datetime object
            if not isinstance(date, str):
                date = date.strftime('%Y-%m-%d')
            # Format date into the path to its corresponding file
            # /output/yyyy/yyyy-mm-dd.csv
                date_paths.append(OUTPUT_DIR + date[:4] + resolution + append + "/" + date + ".csv")
        if start_year != end_year:
        # Get a list of files that actually exist
        # Files are sorted by year, so we need to get the years to compile
        # Pandas has us covered for creating a range of dates, but it outputs the full datetime
            all_years_raw = pandas.date_range(self.__start_date, self.__end_date, freq="YE")
            all_years_raw = all_years_raw.append(pandas.date_range(self.__start_date, self.__end_date, freq="YS"))
            all_years = [] # Holds just the years
            for year in all_years_raw:
                all_years.append(year.strftime('%Y'))
        else: # Start and end year are the same
            all_years = [start_year]
        # List files for all years being queried
        existing_files = []
        try:
            for year in all_years:
                existing_files += self.__list_files_in_dir("./output/" + str(year) + resolution + append, True)
            # Get the files that actually exist in the output dir
            # Only return ones that actually exist- we don't want to call files that aren't there
            date_set = frozenset(date_paths)
            available_file_paths = [path for path in date_set if path in existing_files]
            available_file_paths = sorted(available_file_paths) # makes it easier to debug
            self.days = len(available_file_paths) # used for average calculation
        except TypeError:
            print("No files found in output dir. Has", year, "been processed at the", resolution, "resolution?")
            print("Trying to find files at 15min resolution (will be used to reproduce preferred resolution).")
            available_file_paths = self.__get_files_for_date_range("15min", True)
            if recurse == True:
                print("Files not found in output directory. Process files for entire date range and try again.")
                raise SystemExit
        return available_file_paths
    
    # TODO: time parsing within a range, eg. select records between 3am and 7pm
    #def select_time_period(self, start, end):
        # ensure that start and end are a minimum distance apart
        # Select start row
        # Select end row
        # Return the rows between start_row and end_row (inclusive)
        # return self.data