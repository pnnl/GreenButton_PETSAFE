import pandas
import multiprocessing
import logging
import numpy
from scipy.stats import pareto
from lightphe import LightPHE
from os.path import exists
from os import makedirs, environ
from math import floor
from typing import Optional
from virtual_buildings.building import Building
from config import AGG_TEMPORAL_RESOLUTION, OUTPUT_DIR, PORTION_OF_CPU
from logger_config import config_logger

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pandas.options.mode.copy_on_write = True

# Set up logger
logger = config_logger()

# Value obtained from print(str(logging.ERROR))
environ['LIGHTPHE_LOG_LEVEL'] = "40" # Errors and critical only

# Takes a data file, aggregates it into buildings
class MeterDataParser:
    def __init__(
            self,
            file: str = None, # the filepath to read from
            seed: Optional[int] = None, # seed for rng
            building_size: Optional[int] = 8, # how many sites go in one building; ignored if distribution is provided
            building_count: Optional[int] = -1, # how many buildings to generate. Warning: setting this may mean that sites are reused
            distribution: Optional[bool] = False, # If using a distribution instead of a single value, set True
            key_location: Optional[str] = "./keys/", # output location for keyfiles, should have a trailing slash
            algorithm: Optional[str] = "EllipticCurve-ElGamal", # algorithm to use for encryption
            key_length: Optional[int] = 521, # key size for encryption
            decimal_places: Optional[int] = 5, # decimal places to keep for encryption
            encrypt: Optional[bool] = True # whether or not to encrypt
    ):
        try: # handle keyboard interrupts nicely
            if file is None:
                print("File not provided. Expected relative or absolute filepath.")
                raise SystemExit
            elif seed is None:
                seed = numpy.random.randint(100000000, 999999999)
                with multiprocessing.Lock():
                    logger.warning("Random seed generated. Seed: " + str(seed))
                    logger.info("If you need your seed, run MeterDataParser's get_seed() method during processing.")

            # Check if processed file exists
            self.resolution = AGG_TEMPORAL_RESOLUTION
            date = file[-12:]
            name = date[:4]
            match self.resolution:
                    case "f":
                        name += "-15mins"
                    case "h":
                        name += "-hourly"
                    case "d":
                        name += "-daily"
            # Check whether the file already exists (eg. data already processed)
            # if it doesn't exist, then continue.
            name = OUTPUT_DIR + name + "/" + date[:4] + "-" + date[4:6] + "-" + date[6:] # the output filename
            if not exists(name):
                # Initialize variables
                self.seed = seed
                self.rd = numpy.random.default_rng(self.seed)
                self.__file = file
                self.__decimal_places = decimal_places
                self.__encryption_enabled = encrypt
                self.__building_count = building_count

                # Building size or distribution length must be larger than minimum value specified below
                self.__MIN_BUILDING_SIZE = 3
                self.__BUILDING_SIZE = building_size
                if self.__BUILDING_SIZE < self.__MIN_BUILDING_SIZE:
                    with multiprocessing.Lock():
                        logger.critical("Building size too small.")
                    raise SystemExit
                if distribution == True:
                    self.__distribution = self.createDistribution()
                # TODO: alter for customizable distribution

                # Path should have a trailing slash
                if key_location[-1] != "/":
                    key_location += "/"
                self.__readData() # Read data into memory
                self.__dist = self.createDistribution()
                print("Aggregating for", self.__file)
                self.__makeBuildings() # Aggregate into buildings
                with multiprocessing.Lock():
                    logger.info("Building processing done for " + self.__file)

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
                    processors = floor(processors * PORTION_OF_CPU)
                    results = []
                    with multiprocessing.Pool(processes=processors) as pool:
                        for result in pool.map(self.encrypt_frames, self.__building_list):
                            try:
                                results.append(result)
                            except KeyboardInterrupt:
                                pool.terminate()
                    for i in range(0, len(self.__building_list)):
                        self.__building_list[i] = results[i]
            else:
                print(name, "exists, continuing to next file.")
                self.status = "File exists."
        except KeyboardInterrupt:
            print("Stopping.")
            raise SystemExit

    # Returns the seed used to init rng. Useful if a seed was not provided
    # and you later need to recreate the sorting done by a random seed
    def get_seed(self):
        return self.seed

    # Encrypts a building
    def encrypt_frames(self, building):
        try:
            building.encrypt(self.__keys)
        except Exception as ex:
            with multiprocessing.Lock():
                logger.error("Unable to encrypt: " + ex)
        return building

    # Reads a file's data into memory
    def __readData(self):
        try:
            print("Reading", self.__file)
            with open(self.__file, "r") as csv_file:
                self.__dataframe = pandas.read_csv(csv_file, parse_dates=True)
            self.__dataframe = self.__extractMains() # Remove non-mains circuits
            # TODO: can we detect missing sites here and fill them?
            self.status = "File read."
            return self.__dataframe
        except Exception as ex:
            with multiprocessing.Lock():
                logger.critical("Unable to read file. Aborting. Reason: " + str(ex))
            raise SystemExit

    # Reduces data to only Mains circuits
    def __extractMains(self):
        try:
            return self.__dataframe[["Mains" in r for r in self.__dataframe["regname"]]]
        except KeyError:
            with multiprocessing.Lock():
                logger.error("File does not contain Mains. Check filepath.")
        except Exception as ex:
            with multiprocessing.Lock():
                logger.error("Unable to extract Mains: " + str(ex))

    def createDistribution(self):
        # Parameters and distribution obtained in ../tools/fit-curve.py with fitter library
        #             sumsquare_error          aic          bic  kl_div  ks_statistic     ks_pvalue
        # lomax             0.000146  1644.025381  1655.521029     inf      0.155425  1.165421e-07
        # genpareto         0.000146  1644.025778  1655.521426     inf      0.155425  1.165421e-07
        # pareto            0.000146  1644.027669  1655.523316     inf      0.155425  1.165421e-07
        # levy              0.000148  1650.078976  1657.742741     inf      0.144518  1.116687e-06
        # nct               0.000150  1647.454892  1662.782422     inf      0.124782  4.363519e-05
        self.__dist_c = 0.5335371308758773
        self.__dist_loc = -0.16241563710448093
        self.__dist_scale = 2.1624156371044805
        #self.__dist = pareto(self.__dist_c); see actual function in generate_building_size()
        return True

    # Gets a list of random ids, with len(list) = BUILDING_SIZE
    # TODO: refactor so id selection isn't altered by missing sites for a day-
    # including the first day. Current approach can handle it, but the sites
    # will be sorted differently and that could be a problem for analysis
    # depending on how this is used.
    def __get_random_ids(self, count):
        # We only need as many ids as our building size value
        if len(self.__site_ids) > count: # We have enough sites to make a building
            self.__building_ids = self.rd.choice(self.__site_ids, count, replace=False)
            try:
                if self.__building_count == -1: # if we just want to make as many buildings as the set allows
                    rm = numpy.in1d(self.__site_ids, self.__building_ids) # remove building ids from site id
                    self.__site_ids = self.__site_ids[~rm]
            except Exception as ex:
                print(ex)
        else: # We don't have enough sites left to fill a building-
            # chuck all remaining sites into a building together
            self.__building_ids = numpy.array(self.__site_ids)
            self.__site_ids = numpy.array([]) # Cleared so this doesn't get run again
        return self.__building_ids
    
    def generate_building_size(
            self,
            min_size = int # smallest allowable building size
            ):
        if min_size < 1: # sanity check; buildings must have at least one site
            min_size = 1
        max_size = self.__site_count # TODO: should this be limited to something smaller to ensure more than one building is made?
        count = 0 # placeholder to kickstart while loop; buildings can't have no sites
        while count < min_size or count > max_size: # Exclude values that are too small or too large
            count = int(floor(pareto.rvs(self.__dist_c, loc=self.__dist_loc, scale=self.__dist_scale, size=1, random_state=self.rd)))
        with multiprocessing.Lock():
            logger.debug("Generated building count: " + str(count)) # for debugging of building sizes
        return count

    # Outputs a list of virtual buildings made from data
    def __makeBuildings(self):
        # List all sites by id number
        self.__site_ids = pandas.unique(self.__dataframe["ee_site_id"])
        self.__site_count = self.__site_ids.size
        self.__building_list = [] # will hold a list of Building objects
        # Decide when to stop; set True at end of loop if stop conditions triggered
        stop = False
        # Make buildings until stop condition triggered
        id = 1 # the building id; passed to building for logging purposes
        while stop == False:
            # Get a random set of site ids for a building
            try:
                if self.__dist:
                    count = self.generate_building_size(2) # min size of 2; we need 2+ sites to aggregate them
                else:
                    count = self.__BUILDING_SIZE
                self.__random_ids = self.__get_random_ids(count)
            except Exception as ex:
                with multiprocessing.Lock():
                    logger.critical("Unable to construct buildings: site id randomization failed. Cause: " + str(ex))
                raise SystemExit
            # Make a building (as long as we have ids to give it)
            if self.__random_ids.any():
                try:
                    building = Building(self.__random_ids, self.__dataframe, decimal_places=self.__decimal_places, logging_id=id)
                except Exception as ex:
                    with multiprocessing.Lock():
                        logger.error("unable to create building " + str(id) + ": " + str(ex))
                try:
                    # Aggregate to temporal resolution
                    bsize = building.get_size() # grab site count before agg to avoid summing it
                    building = self.aggregate_to_resolution(building)
                    # Append the site count of the building
                    building["site_count"] = bsize
                    # Add the building to the list of buildings
                    self.__building_list.append(building)
                    self.__building_count -= 1 if self.__building_count > 0 else 0
                    id += 1 # increment ID for logging
                except Exception as ex:
                    with multiprocessing.Lock():
                        logger.error("unable to aggregate building " + str(id - 1) + ": " + str(ex))
            # Decide whether to stop
            if self.__building_count < 0: # if we're making as many sites as the set allows
                stop = True if len(self.__site_ids) < self.__BUILDING_SIZE else False
            elif self.__building_count >= 0: # if we want a specific number of buildings, possibly w/ duplicate sites in buildings
                stop = True if self.__building_count <= 0 else False
        # Deal with leftovers- when we have fewer sites left than the building size
        if self.__site_ids.any() and self.__building_count is None:
            self.__spare_building = Building(self.__site_ids, self.__dataframe, self.__decimal_places)
        self.status = "Buildings made."
        return self.__building_list
    
    def aggregate_to_resolution(self, building):
        # This is currently only able to aggregate up to the daily level because we read
        # files one at a time- one day per file
        match AGG_TEMPORAL_RESOLUTION:
            case "f":
                data = building.get_data() # No intervention needed for f, data is already at that resolution
            case "h":
                data  = building.aggregate_hourly()
            case "d":
                data = building.aggregate_daily()
            case _:
                with multiprocessing.Lock():
                    logger.info(AGG_TEMPORAL_RESOLUTION + " resolution not implemented. Using 15min resolution.")
                data = building.get_data()
        self.status = "Buildings aggregated."
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
                except Exception as ex:
                    with multiprocessing.Lock():
                        logger.error("Unable to export keys. Decryption may fail. Reason: " + str(ex))
                return keys
            elif exists(self.__KEY_LOCATION + "private.txt"):
                privkey = LightPHE(algorithm_name = self.__ALGORITHM, key_file=self.__KEY_LOCATION + "private.txt")
                return privkey
            else:
                with multiprocessing.Lock():
                    logger.critical("Encryption setup failed.")
                raise SystemExit
        except:
            with multiprocessing.Lock():
                logger.critical("Key generation failure. Aborting.")
            raise SystemExit

    # Puts individual building frames together to output as one frame
    # containing all buildings
    def __concat_frames(self):
        try:
            i = 1
            frame = self.__building_list[0]
            frame["ee_site_id"] = i
            # Handle all other frames
            for building in self.__building_list[1:]:
                # TODO: robust checking to make sure the id doesn't exist yet
                i += 1
                building["ee_site_id"] = i
                concat_args = (frame, building)
                frame = pandas.concat(concat_args)
            self.concatenated_frame = frame
            self.__frame_prepared = True
            self.status = "Frames concatenated."
            return frame
        except Exception as ex:
            with multiprocessing.Lock():
                logger.error("Unable to concatenate buildings: " + str(ex))

    # Outputs the aggregated data to the terminal
    def output_to_terminal(self):
        if self.__frame_prepared not in locals() or self.__frame_prepared == False:
            self.__concat_frames()
        print(self.concatenated_frame)

    # Outputs the aggregated data
    def get_data(self):
        if self.__frame_prepared not in locals() or self.__frame_prepared == False:
            self.__concat_frames()
        return self.concatenated_frame
    
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
            # Add encryption folder marker if needed
            if self.__encryption_enabled == True:
                target_folder = target_folder + "-encrypted"
            filename = target_folder + "/" + filename + ".csv"
            # Make sure we have an output dir
            try:
                if not exists(target_folder):
                    makedirs(target_folder)
            except:
                with multiprocessing.Lock():
                    logger.critical("No output folder.")
                raise SystemExit
            # TODO: Also make this check earlier in the process and skip processing
            # for existing files. Save time.
            if not exists(filename):
                with open(filename, "w") as filepath:
                    frame.to_csv(filepath)
            else:
                print(filename, "exists. Continuing...")
        except Exception as ex:
            with multiprocessing.Lock():
                logger.error("Unable to save data to file: " + str(ex))