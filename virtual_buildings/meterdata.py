import pandas
from lightphe import LightPHE
from os.path import exists
from os import makedirs
from os import environ
from sys import exit
from math import floor
from typing import Optional
import multiprocessing
#import random as rd
import numpy
from virtual_buildings.building import Building
from config import AGG_TEMPORAL_RESOLUTION

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pandas.options.mode.copy_on_write = True

# Value obtained from print(str(logging.ERROR))
environ['LIGHTPHE_LOG_LEVEL'] = "40" # Errors and critical only

# Takes a data file, aggregates it into buildings
class MeterDataParser:
    def __init__(
            self,
            file: str = None, # the filepath to read from
            seed: Optional[int] = None, # seed for rng
            building_size: Optional[int] = 8, # how many sites go in one building; ignored if distribution is provided
            distribution: Optional[list] = None, # If using a distribution instead of a single value, this is the distribution
            key_location: Optional[str] = "./keys/", # output location for keyfiles, should have a trailing slash
            algorithm: Optional[str] = "EllipticCurve-ElGamal", # algorithm to use for encryption
            key_length: Optional[int] = 521, # key size for encryption
            decimal_places: Optional[int] = 5, # decimal places to keep for encryption
            encrypt: Optional[bool] = True # whether or not to encrypt
    ):
        if file == None:
            print("File not provided. Expected relative or absolute filepath.")
            exit()
        elif seed == None:
            print("Warning: random seed generated. Building assignment may not be repeatable!")
            seed = numpy.random.randint(100000000, 999999999)
            print("If you need your seed, run this object's get_seed() method.")

        # Initialize variables
        self.seed = seed
        self.rd = numpy.random.default_rng(self.seed)
        self.__file = file
        self.__decimal_places = decimal_places
        self.__encryption_enabled = encrypt

        # Building size or distribution length must be larger than minimum value specified below
        self.__MIN_BUILDING_SIZE = 3
        if distribution == None:
            self.__BUILDING_SIZE = building_size
        else:
            self.__distribution = distribution
        # TODO: alter to check distribution does not compromise information privacy
        if self.__BUILDING_SIZE < self.__MIN_BUILDING_SIZE:
            print("Building size too small.")
            exit()

        # Path should have a trailing slash
        if key_location[-1] != "/":
            key_location += "/"

        self.__readData() # Read data into memory
        self.__prepared_data = self.__extractMains() # Remove non-mains circuits
        print("Aggregating for", self.__file)
        self.__makeBuildings() # Aggregate into buildings
        print("Building processing done for", self.__file)

        # Encrypt buildings
        if self.__encryption_enabled == True:
            self.__KEY_LOCATION = key_location
            self.__ALGORITHM = algorithm
            self.__KEY_LENGTH = key_length

            self.__keys = self.__setup_encryption()
            # Use multiprocessing to cut processing times significantly
            # Nothing is written to file or alters a global, so there should
            # be no race condition
            processors = multiprocessing.cpu_count()
            processors = floor(processors / 2)
            results = []
            with multiprocessing.Pool(processes=processors) as pool:
                for result in pool.map(self.encrypt_frames, self.__building_list):
                    results.append(result)
            for i in range(0, len(self.__building_list)):
                self.__building_list[i] = results[i]

    # Returns the seed used to init rng. Useful if a seed was not provided
    # and you later need to recreate the sorting done by a random seed
    def get_seed(self):
        return self.seed

    # Encrypts a building
    def encrypt_frames(self, building):
        try:
            building.encrypt(self.__keys)
        except Exception as error:
            print("Unable to encrypt:", error)
        return building

    # Reads a file's data into memory
    def __readData(self):
        try:
            print("Reading", self.__file)
            with open(self.__file, "r") as csv_file:
                self.__dataframe = pandas.read_csv(csv_file)
            return self.__dataframe
        except Exception as error:
            print("Unable to read file. Aborting.") 
            print("Reason:", error)
            exit()

    # Reduces data to only Mains circuits
    def __extractMains(self):
        # TODO: edit this to "contains Mains" since there are edge cases
        # of "mains + something" or "Mains_right"
        try:
            return self.__dataframe[self.__dataframe["regname"] == "Mains"]
        except KeyError:
            print("File does not contain Mains. Check filepath.")

    # Gets a list of random ids, with len(list) = BUILDING_SIZE
    # TODO: refactor so id selection isn't altered by missing sites for a day-
    # including the first day. Current approach can handle it, but the sites
    # will be sorted differently and that could be a problem for analysis
    # depending on how this is used.
    def __get_random_ids(self):
        # We only need as many ids as our building size value
        if len(self.__site_ids) > self.__BUILDING_SIZE:
            self.__building_ids = self.rd.choice(self.__site_ids, self.__BUILDING_SIZE, replace=False)
            try:
                rm = numpy.in1d(self.__site_ids, self.__building_ids) # remove building ids from site id
                self.__site_ids = self.__site_ids[~rm]
            except Exception as error:
                print(error)
        else:
            # We don't have enough sites left to fill a building-
            # chuck all remaining sites into a building together
            self.__building_ids = self.__site_ids
            self.__site_ids = [] # Cleared so this doesn't get run again
        return self.__building_ids

    # Outputs a list of virtual buildings made from data
    def __makeBuildings(self):
        # List all sites by id number
        self.__site_ids = pandas.unique(self.__prepared_data["ee_site_id"])
        self.__building_list = [] # will hold a list of Building objects
        # Until we run out of sites to make buildings from
        while len(self.__site_ids) >= self.__BUILDING_SIZE:
            # Get a random set of site ids for a building
            try:
                self.__random_ids = self.__get_random_ids()
            except:
                print("Unable to construct buildings: site id randomization failed.")
                print("Check building size parameter.")
                exit()
            # Make a building (as long as we have ids to give it)
            if self.__random_ids.any():
                building = Building(self.__random_ids, self.__prepared_data, self.__decimal_places)
                try:
                    # Aggregate to temporal resolution
                    building = self.aggregate_to_resolution(building)
                    # Add the building to the list of buildings
                    self.__building_list.append(building)
                except Exception as error:
                    print("failed to aggregate building", building.get_id(), ":", error)
        # Deal with leftovers- when we have fewer sites left than the building size
        if self.__site_ids.any():
            self.__spare_building = Building(self.__site_ids, self.__prepared_data, self.__decimal_places)
        return self.__building_list
    
    def aggregate_to_resolution(self, building):
        # This is currently only able to aggregate up to the daily level because we read
        # files one at a time- one day per file
        match AGG_TEMPORAL_RESOLUTION:
            case "f":
                data = building.get_data() # No intervention needed for f, data is already at that resolution
            case "h":
                data  = building.aggregegate_hourly()
            case "d":
                data = building.aggregegate_daily()
            case _:
                print("Resolution not implemented.")
                data = None
        return data
    
    # Sets up and exports encryption keys; returns
    # a LightPHE Keys object
    def __setup_encryption(self):
        # Value obtained from print(str(logging.ERROR))
        environ['LIGHTPHE_LOG_LEVEL'] = "40" # Errors and critical only
        # Make and export keys
        try:
            if "keys" not in globals() and not exists(self.__KEY_LOCATION + "public.txt"):
                keys = LightPHE(algorithm_name = self.__ALGORITHM, key_size = self.__KEY_LENGTH)
                try:
                    keys.export_keys(target_file = self.__KEY_LOCATION + "public.txt", public = True)
                    keys.export_keys(target_file = self.__KEY_LOCATION + "private.txt", public = False)
                except Exception as error:
                    print("Unable to export keys. Decryption may fail.")
                    print(error)
                return keys
            elif exists(self.__KEY_LOCATION + "private.txt"):
                privkey = LightPHE(algorithm_name = self.__ALGORITHM, key_file=self.__KEY_LOCATION + "private.txt")
                return privkey
            else:
                print("Encryption setup failed.")
                exit()
        except:
            print("Key generation failure. Aborting.")
            exit()

    # Puts individual building frames together to output as one frame
    # containing all buildings
    def __concat_frames(self):
        try:
            i = 1
            frame = self.__building_list[0]
            frame["ee_site_id"] = i
            # Handle all other frames
            for building in self.__building_list[1:]:
                building["ee_site_id"] = i
                # TODO: robust checking to make sure the id doesn't exist yet
                i += 1
                concat_args = (frame, building)
                frame = pandas.concat(concat_args)
            self.concatenated_frame = frame
            self.__frame_prepared = True
            return frame
        except Exception as error:
            print("Unable to concatenate buildings:", error)

    # Outputs the aggregated data to the terminal
    def output_to_terminal(self):
        if self.__frame_prepared in locals() and self.__frame_prepared == True:
            pass
        else:
            self.__concat_frames()
        print(self.concatenated_frame)
    
    # Outputs a frame of all buildings to a csv file at OUTPUT_DIR
    def output_to_file(self, location):
        frame = self.__concat_frames()
        try:
            # Name the file
            filename = frame.index[0].strftime('%Y-%m-%d')
            target_folder = location + filename[:4] # Just the year
            # Append the resolution
            self.resolution = AGG_TEMPORAL_RESOLUTION
            match self.resolution:
                case "f":
                    target_folder += "-15mins"
                case "h":
                    target_folder += "-hourly"
                case "d":
                    target_folder += "-daily"
            # Encrypt if needed
            if self.__encryption_enabled == True:
                target_folder = target_folder + "-encrypted"
            filename = target_folder + "/" + filename + ".csv"
            # Make sure we have an output dir
            try:
                if not exists(target_folder):
                    makedirs(target_folder)
            except:
                print("Unable to create folder.")
                exit()
            # TODO: Also make this check earlier in the process and skip processing
            # for existing files. Save time.
            if not exists(filename):
                with open(filename, "w") as filepath:
                    frame.to_csv(filepath)
            else:
                print(filename, "exists. Continuing...")
        except Exception as error:
            print("Unable to save data to file.")
            print(error)