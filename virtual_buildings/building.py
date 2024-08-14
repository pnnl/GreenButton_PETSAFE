import pandas
import numpy
from os import environ
from typing import Optional
from config import PORTION_OF_CPU

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pandas.options.mode.copy_on_write = True

# Value obtained from print(str(logging.ERROR))
# LightPHE needs to be reminded not to spam the terminal sometimes
environ['LIGHTPHE_LOG_LEVEL'] = "40" # Errors and critical only

# TODO: store building site count to enable accurate average calculation later
# Doubly important for implementing variable building sizes

class Building:
    def __init__(
            self,
            ids: list, # a list of ids to place in the building
            data, # a data frame of meter readings including (at minimum) the ids in ids
            decimal_places: Optional[int] = 5 # The number of decimal places to preserve
            ):
        self.__DROP_COLUMNS = ['regname', 'max_t']
        self.__data = data
        self.__ids = ids
        self.resolution = "fifteen minutes"

        # Used to convert floats to int so encryption works as expected.
        # Floats will be multiplied by this amount to ensure conversion doesn't
        # lose precision- e.g. 10,000 covers 4 decimal places of precision.
        # DECIMAL_PLACES contains the number of places expected at most.
        # Must be greater than 0.
        self.__CONVERSION_SCALAR = 10**decimal_places
        # Aggregate data into buildings
        self.__data = self.__define_building()

    # Aggregates sites into a building.
    # Takes a list of site id numbers and a data frame containing (at minimum)
    # the data associated with those id numbers (ee_site_id)
    # Combines the data associated with those id numbers to form one frame
    # that's the sum of all its component sites. Outputs that frame.
    def __define_building(self):
        dataframe = self.__data
        ids = self.__ids
        # Get a building to start the frame
        # Check for an empty id list
        #if len(ids) > 0:
        if ids.any():
            building = self.__clean_frame(dataframe[dataframe["ee_site_id"] == ids[0]])
            ids = numpy.delete(ids, 0)
            # Add the rest in
            for id in ids:
                site = self.__clean_frame(dataframe[dataframe["ee_site_id"] == id])
                try:
                    building = building.add(site, fill_value=0) # There shouldn't be NAs, but just in case...
                except TypeError as error:
                    print("Could not create building due to incompatible data types:", error)
        else:
            print("No building ids supplied.")
            return None
        building = self.__correct_power_factor(building)
        # Returns empty frame if none of the supplied ids match the data supplied
        return building
    
    def __resample_data(self, period, resolution):
        self.__data = self.__data.resample(period).sum()
        self.__data = self.__correct_power_factor(self.__data)
        self.resolution = resolution
    
    def aggregate_hourly(self):
        self.__resample_data('60min', 'hourly')
        return self.__data

    def aggregate_daily(self):
        self.__resample_data('1440min', 'daily')
        return self.__data
    
    # TODO: calculate signature to prove data accuracy/validity
    # def __calculate_signature(self):

    # TODO: return signature
    # def get_signature(self):
    
    # A wrapper for encrypt_column() that calls it for each column to encrypt.
    # Directly modifies site data; returns nothing, but encrypts self.__data's values.
    def encrypt(self, keys):
        self.__keys = keys
        for column in self.__data.columns:
            if column in ["power", "apparent_power", "pf"]:
                self.__data[column] = self.__data[column].apply(self.__encrypt_column)

    # Encrypts a single column of a data frame.
    # Takes the column as input.
    # Returns the encrypted column.
    def __encrypt_column(self, target):
        # TODO: consider importing floor to deal with poorly-chosen scalar values
        return self.__keys.encrypt(int(float(target) * self.__CONVERSION_SCALAR))
    
    # Prepares a data frame for processing; sets the indices, drops
    # indicated columns, and deals with any missing values.
    # Takes a frame as input.
    # Returns a cleaned frame.
    def __clean_frame(self, frame):
        try:
            # Drop unnecessary columns
            frame = frame.drop(self.__DROP_COLUMNS, axis=1)
            # Used to fill in missing values with 0s
            # Get a list of 15-min increments for an entire day
            list_min_t_times = [f'{i:02d}:{j:02d}' for i in range(24) for j in range(0, 60, 15)]
            # Add the day to the list of times to create a complete datetime
            # The building object should only ever receive one day of data at a time, so snagging the date
            # from the first datetime is acceptable
            day = frame["min_t"].iloc[0]
            day = day[:11]
            for time in list_min_t_times:
                this_datetime = str(day) + " " + str(time)
                list_min_t_times[list_min_t_times.index(time)] = this_datetime
            try:
                min_t_series = pandas.Series(data=list_min_t_times).apply(pandas.to_datetime) # Easier than strptime
            except Exception as error:
                print("Could not format frame datetime:", error)
                min_t_series = list_min_t_times
            # Fill missing intervals with NA using the 15-min increment list to create a complete index
            # (if 02:15-02:29 is missing, then this creates this interval with NA values in its columns)
            new_index = pandas.Index(min_t_series, name="min_t")
            frame["min_t"] = frame["min_t"].apply(pandas.to_datetime)
            frame = frame.set_index(["min_t"])
            frame = frame.reindex(new_index)
            # Forward-fill any missing values (NA) with the previous existing value
            # eg. a sequence of [4, NA, 5] becomes [4, 4, 5]
            frame = frame.infer_objects(copy=False)
            # TODO: what if the first value is NA?
            try:
                frame = frame.ffill()
            except Exception as error:
                print("Could not forward fill:", error)
                print("Filling with zeroes instead.")
            frame = frame.fillna(0) # Catch anything forward fill missed (e.g. first value = 0)
        except KeyError:
            #print("Frame already clean.")
            pass
        return frame
    
    def __correct_power_factor(self, building):
        # Fix the power factor
        building["pf"] = building["power"] / building["apparent_power"]
        return building

    # Returns the data frame for the building.
    def get_data(self):
        return self.__data
    
    # Returns the building id number.
    def get_id(self):
        return self.__data["ee_site_id"].iloc[0]
    
    # Sets the building id number.
    # Returns the new id.
    def change_id(self, id):
        self.__data["ee_site_id"] = id
        return id
    
    # Returns the sum of the building's power (should be resolution of one day)
    def get_power_sum(self):
        return self.__data["power"].sum()
    
    # Returns the resolution of the building
    def get_resolution(self):
        return self.resolution