import pandas
from scipy.stats import pareto
from lightphe import LightPHE
from os.path import exists
from os import environ
from multiprocessing import Lock
from numpy import random
from typing import Optional
from scipy.stats import halfcauchy

import processor.pullMains as pulldb
from processor.commonDB import DBConn
from logger_config import config_logger

from config import DATABASE, SEED

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pandas.options.mode.copy_on_write = True

# Set up logger
logger = config_logger()
# Initialize with seed
randomizer = random.default_rng(SEED)

# Gets a set of random building ids; used to create buildings
def choose_random_ids():
    # Get the building size
    dist_loc = 2
    dist_scale = 2.1624533028540704
    count = -1 # Obviously invalid placeholder to initiate while loop
    while count < 2:
        count = int(halfcauchy.rvs(loc=dist_loc, scale=dist_scale, size=1)[0]) # Generate building size
    # Get possible IDs to choose from
    conn = DBConn.create_connection(DATABASE)
    query = "SELECT ee_site_id FROM POWER"
    results = conn.execute(query)
    ids = results.fetchall()
    # Select a random set from the results
    building_ids = randomizer.choice(ids, count, replace=False)
    return building_ids

# The building class
class Building:
    def __init__(
        self,
        database: str = DATABASE,
        ids: list = None,
        encrypt: bool = True, # Whether or not to encrypt the building
    ):
        self.__ids = ids
        self.__database = database
        self.__encryption_enabled = encrypt

        if self.__encryption_enabled == True:
            self.__keys = self.__setup_encryption()

    # Sets up and exports encryption keys; returns
    # a LightPHE Keys object
    def __setup_encryption(self):
        # Value obtained from print(str(logging.ERROR))
        environ['LIGHTPHE_LOG_LEVEL'] = "40" # Errors and critical only
        # Set encryption parameters
        self.__ALGORITHM = "EllipticCurve-ElGamal"
        self.__KEY_LENGTH = 521
        self.__KEY_LOCATION = "./keys/"
        # Make and export keys
        try:
            if "keys" not in globals() and not exists(self.__KEY_LOCATION + "public.txt"):
                keys = LightPHE(algorithm_name = self.__ALGORITHM, key_size = self.__KEY_LENGTH)
                try:
                    keys.export_keys(target_file = self.__KEY_LOCATION + "public.txt", public = True)
                    keys.export_keys(target_file = self.__KEY_LOCATION + "private.txt", public = False)
                except Exception as ex:
                    with Lock():
                        logger.error("Unable to export keys. Decryption may fail. Reason: " + str(ex))
                return keys
            elif exists(self.__KEY_LOCATION + "private.txt"):
                privkey = LightPHE(algorithm_name = self.__ALGORITHM, key_file=self.__KEY_LOCATION + "private.txt")
                return privkey
            else:
                with Lock():
                    logger.critical("Encryption setup failed.")
                raise SystemExit
        except:
            with Lock():
                logger.critical("Key generation failure. Aborting.")
                raise SystemExit
            
    def __get_data(self):
        conn = DBConn.create_connection(self.__database)
        # TODO: finish this so the data is in a complete pandas frame
        for id in self.__ids:
            # TODO: narrow this to just mains?
            query = f"SELECT * FROM POWER WHERE ee_site_id={id} ORDER BY timestamp"
            results = conn.execute(query)
            data = results.fetchall()
        # Place into the same frame
        self.__data = None # Will be the final

    # Run after functions that change power factor (sum functions); recalculates it to be correct
    def __correct_power_factor(self, building):
        # Fix the power factor
        building["pf"] = building["power"] / building["apparent_power"]
        return building

    def aggregate(self, resolution): # resolution should be a valid resample value
        siteids = self.__data["sites"]
        self.__data = self.__data.drop("sites") # Str type doesn't work with resample
        try:
            self.__data = self.__data.resample(resolution).sum()
            self.__data = self.__correct_power_factor(self.__data)
        except Exception as ex:
            with Lock():
                logger.error("Building " + self.__bid + ": Could not resample: " + ex)
        self.__data["sites"] = siteids # replace when done
        self.resolution = resolution
        # Make sure it's a pandas frame

    def save_data(self):
        # TODO: save building to table in database
        # Structure: two tables? Building-site mapping and buildings data?
        pass

