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
    ):
        self.__start_datetime = start_date
        self.__end_datetime = end_date
        # TODO: deal with None end datetime
        self.__files = self.__get_files_for_date_range()
        self.data = self.__build_data_frame()

    # TODO:
    # def validate_date_range(self):
    #    check that date range makes sense and does not violate aggregation resolution

    # Compiles all days within the date range into a single frame for processing
    def __build_data_frame(self):
        frame = pandas.DataFrame()
        print("Building frame (may take a moment for large date ranges)...")
        for file in self.__files:
            try:
                with open(file, "r") as csv_file:
                    data = pandas.read_csv(csv_file)
            except:
                print("Reader: File not found.")
                data = pandas.DataFrame()
            frame = pandas.concat((frame, data))
        print("Frame built.")
        return frame
    
    # Returns all data in the date range
    def get_data(self):
        return self.data
    
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
        return building["power"].sum()
    
    def graph_building_power(
            self,
            building_id: int # The integer ID of the building to work with
    ):
        try:
            building = self.data[self.data["ee_site_id"] == building_id]
            building = building["power"]
        except KeyError as error:
            print("Key does not exist:", error)
            return None
        title = "Real Power for Building " + building_id
        fig = px.line(building, x="power", y="min_t", title=title)
        fig.show()
        #ax = building.plot()
        # TODO: add date range to name for clarity
        #plt.savefig("./output/building_" + building_id + "_avg" + ".png")
    
    # Gets average power usage for the selected time resolution
    # e.g. a resolution of 1 month returns average total usage for a month of time
    # TODO: This assumes that data was stored in 15-minute
    # intervals. Check that (timestamps or folder name) and adjust
    # accordingly now that it can be stored at broader intervals as well.
    def get_building_power_avg(
            self, 
            building_id: int # The integer ID of the building to work with
            ):
        sum = self.get_building_power_sum(building_id)
        avg = sum * 1/8 # scale down to a "site" of usage -
            # TODO: modify this to use BUILDING_SIZE value
            # instead of using magic number 8
        if STAT_TEMPORAL_RESOLUTION != "y":
            avg = avg * 1/12 # months in a year
        if STAT_TEMPORAL_RESOLUTION in ["w", "d", "h", "f"]:
            avg = avg * 1/4.345 # weeks in a month on average
            # TODO: we can do better than average, or at least get
            # a better average for the actual date range
        if STAT_TEMPORAL_RESOLUTION in ["d", "h", "f"]:
            avg = avg * 1/7 # days in a week
        if STAT_TEMPORAL_RESOLUTION in ["h", "f"]:
            avg = avg * 1/24 # hours in a day
        if STAT_TEMPORAL_RESOLUTION == "f":
            avg = avg * 1/4 # sets of 15 mins in an hour
        # Keep size reasonable
        avg = round(avg, 4)
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
    def __get_files_for_date_range(self):
        # Convert to datetimes to enable use of .year
        self.__start_date = self.convert_datestr_to_dateobj(self.__start_datetime)
        self.__end_date = self.convert_datestr_to_dateobj(self.__end_datetime)
        # Get years (used to look inside the correct folders)
        start_year = self.__start_date.year
        end_year = self.__end_date.year
        if start_year != end_year:
            # TODO: validate that date range size does not violate privacy
            all_dates = pandas.date_range(self.__start_date, self.__end_date, freq="d")
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
        # Pandas has us covered for creating a range of dates, but it outputs the full datetime
            all_years_raw = pandas.date_range(self.__start_date, self.__end_date, freq="YE")
            all_years_raw = all_years_raw.append(pandas.date_range(self.__start_date, self.__end_date, freq="YS"))
            all_years = [] # Holds just the years
            for year in all_years_raw:
                all_years.append(year.strftime('%Y'))
        # List files for all years being queried
        existing_files = []
        try:
            # Deal with different resolution effects on directory name
            match STAT_TEMPORAL_RESOLUTION:
                case "f":
                    resolution = "-15mins"
                case "h":
                    resolution = "-hourly"
                case "d":
                    resolution = "-daily"
            # Deal with encryption's effects on directory name
            if DECRYPT == True:
                append = "-encrypted"
            else:
                append = ""
            for year in all_years:
                existing_files += self.__list_files_in_dir("./output/" + year + resolution + append, True)
        except TypeError:
            print("No files found in output dir. Has", year, "been processed at the", resolution, "resolution?")
        # Get the files that actually exist in the output dir
        # Only return ones that actually exist- we don't want to call files that aren't there
        date_set = frozenset(date_paths)
        available_file_paths = [path for path in date_set if path in existing_files]
        self.days = len(available_file_paths) # used for average calculation
        return sorted(available_file_paths)
    
    # TODO: time parsing within a range, eg. select records between 3am and 7pm
    #def select_time_period(self, start, end):
        # ensure that start and end are a minimum distance apart
        # Select start row
        # Select end row
        # Return the rows between start_row and end_row (inclusive)
        # return self.data