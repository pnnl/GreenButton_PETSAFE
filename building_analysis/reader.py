import pandas as pd
import pickle
import plotly.express as px
import datetime as dt
from os import listdir
import os.path
from typing import Optional
from config import OUTPUT_DIR, DECRYPT

# Time periods should be in the form yyyy-mm-dd HH:mm
# HH:mm may be missing if time is midnight
class Reader:
    def __init__(
            self,
            start_date: str, # the datetime of the start of the period to read, YY-MM-DD HH-MM expected
            end_date: Optional[str] = None, # the datetime of the start of the period to read, YY-MM-DD HH-MM expected
            resolution: Optional[str] = "15mins", # the resolution to return data at
            read_dir: Optional[str] = OUTPUT_DIR + "buildings/"
    ):
        self.__start_datetime = start_date
        self.__end_datetime = end_date
        self.__resolution = resolution
        self.__read_dir = read_dir
        # TODO: deal with None end datetime
        self.validate_date_range()
        self.data = self.unpickle_buildings()
        self.data = self.change_time_resolution(self.data, self.__resolution)

    # TODO: add more checks for privacy concerns
    def validate_date_range(self):
        if self.__start_datetime > self.__end_datetime:
            print("Start date must be after end date.")
            raise SystemExit
    
    # Returns all data in the date range
    def get_data(self):
        return self.data
    
    def get_all_site_ids(self):
        return pd.unique(self.data["point_id"])
    
    def get_building_site_ids(self, building_id):
        return self.data[self.data["building_id"] == building_id]["point_id"].iloc[0]
    
    def get_building_ids(self):
        return pd.unique(self.data["building_id"])
    
    # Change input resolution string into a consistent format for use in resampling
    @staticmethod
    def check_resolution(
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
        if resolution is not None:
            # TODO Original resolution IS saved. Check it. If it matches, do nothing to save time.
            try:
                frame = pd.DataFrame()
                # Work in chunks to preserve building IDs; one building at a time
                for site in pd.unique(data["building_id"]):
                    chunk = data[data["building_id"] == site] # Get the building to work on
                    # Get information that needs to stay constant (no summing it!)
                    chunk_site_ids = chunk["point_id"]
                    chunk_id = chunk["building_id"].iloc[0]
                    # Resample to new time frame
                    chunk = chunk.resample(resolution).sum()
                    # Replace columns that should not change
                    chunk["building_id"] = chunk_id
                    chunk["point_id"] = chunk_site_ids
                    # Add to the processed frame
                    frame = pd.concat([frame, chunk])
                data = frame
                if DECRYPT == False:
                    # This doesn't work under partial HE
                    data["pf"] = data["real_power"] / data["apparent_power"]
                else:
                    # Let the user know this needs to be recalculated to be useful
                    print("If resolution is changed on encrypted data, then the power factor (pf) will be inaccurate if decrypted.")
                    print("Please recalculate by dividing real power by apparent power.")
            except Exception as error:
                print("Could not change resolution:", error)
        else:
            print("Resolution not implemented.")
        return data
    
    def get_building(self, building_id):
        try:
            building = self.data[self.data["building_id"] == building_id]
            if building.empty:
                raise Exception("Building has no data or does not exist (empty frame).")
            return building
        except Exception as error:
            print("Building could not be retrieved:", error)
            return None

    def graph_building_power(
            self,
            building_id: int, # The integer ID of the building to work with
            resolution: str, # the resolution to graph at.
            show_graph: Optional[bool] = True # whether to show the graph
    ):
        # TODO: Check that data is decrypted; graphing encrypted data makes no sense
        # TODO: if resolution = supplied data, graphing won't work as expected
        building = self.get_building(building_id)
        building = self.change_time_resolution(building, resolution)
        title = "Real Power for Building " + str(building_id)
        fig = px.line(building, y="real_power", title=title)
        if show_graph == True:
            fig.show()
        return fig
    
    def get_building_with_sites(
            self,
            building_id: int, # The integer ID of the building to work with
            resolution: str, # the resolution to graph at.
    ):
        from virtual_buildings.create_buildings import Building
        from config import DATABASE, START_DATE, END_DATE
        print("________\nRetrieving sites for", building_id, ". This may take several minutes.")
        building = self.get_building(building_id)
        building = self.change_time_resolution(building, resolution)
        building_and_sites = building[["real_power"]].copy().rename(columns={"real_power": "Building Aggregate"})
        ids = building["point_id"].iloc[0].split(", ") # TODO: eventually site ids will be per row. Account for that.
        ids[0] = ids[0][1:] # Remove parentheses from string
        ids[-1] = ids[-1][:-1] # Remove parentheses from string
        sites = Building.query_for_sites(database_path=DATABASE, ids=ids, start_date=START_DATE, end_date=END_DATE)
        sites = sites.set_index(["timestamp"])
        print(pd.unique(sites["point_id"]))
        for site_id in pd.unique(sites["point_id"]):
            site_power = sites[sites["point_id"] == site_id]
            if site_power.empty:
                print("Site", site_id, "has no records.")
            else:
                # TODO: deal with duplicate sites
                site_power = Building.impute(site_power)
                site_power = site_power.rename(columns={"ee_site_id": "building_id"})
                site_power = self.change_time_resolution(site_power, resolution)
            colname = "Site " + str(site_id)
            building_and_sites[colname] = site_power["real_power"].groupby(by="timestamp").sum()
        return building_and_sites
    
    def graph_building_power_with_sites(
            self,
            building_id: int, # The integer ID of the building to work with
            resolution: str, # the resolution to graph at.
            show_graph: Optional[bool] = True # whether to show the graph
    ):
        graph_frame = self.get_building_with_sites(building_id, resolution)
        print(graph_frame)
        title = "Daily Real Power for Building " + str(building_id) + " vs Site Real Power"

        fig = px.line(graph_frame, title=title, labels={"value": "Real Power", "timestamp": "Date"})
        fig.data[0].line.color = "red"
        for line in fig.data[1:]:
            line.line.color = "#A9A9A9" # Gray
        # Lines of sites of interest go here
        #fig.data[1].line.color = "blue"
        if show_graph == True:
            fig.show()
        return fig
    
    # Returns the sum of power for a building with ee_site_id of building_id
    def get_building_power_sum(
            self, 
            building_id: int # The integer ID of the building to work with
            ):
        building = self.get_building(building_id)
        # TODO: per time period instead of whole provided period
        return building["real_power"].sum()
    
    # Gets average power usage for the selected time resolution
    # e.g. a resolution of 1 month returns average total usage for a month of time
    # TODO: Check this works as expected with larger time resolutions
    def get_building_power_avg(
            self, 
            building_id: int # The integer ID of the building to work with
            ):
        try:
            sum = self.get_building_power_sum(building_id)
            site_count = len(tuple(pd.unique(self.data[self.data["building_id"] == building_id]["point_id"])[0].split()))
            # Done with multiplication to allow it to be done homomorphically- plaintext scalars
            # are okay for multiplication, not division.
            scalar = 1/site_count
            avg = sum * scalar # scale down to a "site" of usage
            #avg = round(avg, 4) # Keep size reasonable for output
            return avg
        except IndexError:
            print("Cannot average: building", building_id, "does not exist.")
            return None
    
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
                        files.remove(dir_path + file)
            return files
        # TODO: Catch specific exception for no files existing
        except Exception as ex:
            print("Could not list files:", ex)
            return None

    def unpickle_buildings(self):
        buildings_frame = pd.DataFrame()
        # Get all buildings from files and place in one big frame for processing
        try:
            for file in self.__list_files_in_dir(self.__read_dir, prepend_path=True):
                with open(file, "rb") as file:
                    building = pickle.load(file)
                buildings_frame = pd.concat((buildings_frame, building))
            return buildings_frame
        except Exception as ex:
            print("Could not unpickle buildings:", ex)
            raise SystemExit # For now
    
    # TODO: time parsing within a range, eg. select records between 3am and 7pm
    #def select_time_period(self, start, end):
        # ensure that start and end are a minimum distance apart
        # Select start row
        # Select end row
        # Return the rows between start_row and end_row (inclusive)
        # return self.data