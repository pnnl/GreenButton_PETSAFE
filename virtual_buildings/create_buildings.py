import pandas as pd
from lightphe import LightPHE
from os.path import exists
from os import environ
from multiprocessing import Lock
from numpy import random
from typing import Optional
from scipy.stats import halfcauchy
from math import floor

#import processor.pullMains as pulldb
from processor.commonDB import DBConn
from logger_config import config_logger
from config import DATABASE, SEED, ENCRYPT_COLS

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

# Set up logger
logger = config_logger()
# Initialize with seed
randomizer = random.default_rng(SEED)

# Gets a set of random building ids; used to create buildings
def choose_random_ids():
    print("Generating building size.")
    # Get the building size
    dist_loc = 2
    dist_scale = 2.1624533028540704
    count = -1 # Obviously invalid placeholder to initiate while loop
    while count < 2:
        count = int(halfcauchy.rvs(loc=dist_loc, scale=dist_scale, size=1, random_state=SEED)[0]) # Generate building size
    # Get possible IDs to choose from
    print("Selecting building IDs.")
    with DBConn.create_connection(DATABASE) as conn:
        query = "SELECT DISTINCT point_id FROM LABELS"
        results = conn.execute(query)
        ids = results.fetchall()
    # Select a random set from the results
    building_ids = randomizer.choice(ids, count, replace=True)
    building_ids = tuple([id[0] for id in building_ids])
    return building_ids

def make_buildings(count):
    for i in range(0, count):
        ids = choose_random_ids()
        print("Creating building", i)
        building = Building(ids, encrypt=False, building_id=i, pickle=True) # encryption false to check this works
        print("Building", i, "created.")

# The building class
class Building:
    def __init__(
        self,
        ids: list,
        database: Optional[str] = DATABASE,
        building_id: Optional[int] = 0, # Building ID, used for saving to file
        encrypt: Optional[bool] = True, # Whether or not to encrypt the building
        pickle: Optional[bool] = False # Whether to pickle the building to its own individual file
    ):
        self.__ids = ids
        self.__database = database
        self.__bid = building_id
        self.__encryption_enabled = encrypt
        self.__pickle = pickle

        # Sanity check for id length
        if len(self.__ids) < 2:
            print("Building must have at least two units.")
        else:
            self.__get_data()
            # Make sure the aggregation interval is greater than the interval in the data-
            # reference duration column
            #self.aggregate("1h") # Temporary, allow this to be passed

            if self.__encryption_enabled == True:
                self.__keys = self.__setup_encryption()

            if self.__pickle == True:
                self.save_data()
                print("Building", self.__bid, "saved to pickle file.")
    
    def __str__(self):
        return self.__data.to_string(max_rows=20)

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
            
    # Encrypt all sensitive columns defined in config
    def encrypt_building(self):
        for column in self.__data.columns:
            if column in ENCRYPT_COLS:
                self.__data[column] = self.__data[column].apply(self.__encrypt_value)
        return self.__data
            
    # Encrypt one column. Called by encrypt() during multiprocessing to speed things up
    def __encrypt_value(
            self,
            target: str # the name of the value to encrypt
            ):
        # HE doesn't always play nicely with floats; conversion to INT is needed
        # This conversion will be removed if we switch to CKKS
        decimal_places = 8 # How many decimal places to keep; needs to be the same when decrypted
        CONVERSION_SCALAR = 10**decimal_places
        return self.__keys.encrypt(int(float(target) * CONVERSION_SCALAR))
            
    # Retrieves data for component sites via SQL query
    # stores in self.__data
    # returns updated self.__data
    def __get_data(self):
        # TODO: if number of sites needed is larger than number in database (site duplication needed),
        # make sure to only query for them once, then duplicate them (will need to change ID for index)
        with DBConn.create_connection(self.__database) as conn:
            print("Connected to database.")

            # TODO: narrow this to just mains?
            # We only need to query each id once. Convert to set to get unique.
            print("Building IDs:", self.__ids)
            unique_ids = tuple(set(self.__ids))
            query = f"SELECT * FROM POWER WHERE point_id IN {unique_ids};"
            results = conn.execute(query)
            # TODO: figure out why parameterized query gets no results
            # in_statement = str(set(self.__ids))[1:-1]
            # print("Building IDs:", in_statement)
            # Parameterized query mitigates injection vector as per Python docs
            #query = "SELECT * FROM POWER WHERE point_id IN (?);"
            #results = conn.execute(query, (in_statement,))
            print("Query done. Retrieving...")

            data = []
            while True:
                chunk = results.fetchmany(50000) # fetchall() results in MemoryError for invalid id value
                if chunk == []: # fetchmany returns empty list if there are no more results
                    break
                else:
                    data = data + chunk
            # Needed to concatenate frames properly because from_records() needs a list of columns
            columns = ['ee_site_id', 'point_id', 'timestamp', 'duration', 'real_power', 'apparent_power', 'pf'] # used for frame creation
            # Place into the same frame
            if not hasattr(self, '__data'): # Frame does not exist yet
                self.__data = pd.DataFrame.from_records(data=data, columns=columns)
            else: # Frame exists
                newframe = pd.DataFrame.from_records(data=data, columns=columns)
                self.__data = pd.concat([self.__data, newframe])

            # Duplicate entries that are listed more than once in ids
            id_counts = pd.Series(data=self.__ids).value_counts() # Find how many times IDs are duplicated
            all_ids = list(unique_ids) # Needs to be separate so we can append without affecting for loop
            for id in unique_ids:
                if id_counts[id] > 1:
                    print(id, "is duplicated", id_counts[id], "times.")
                    for i in range(1, id_counts[id]):
                        # Duplicate ID into a new fake site
                        dupesite = self.__data[self.__data["point_id"] == id]
                        # Point ID of dupe needs to be changed; index must be unique
                        while id in unique_ids:
                            id += 1
                        all_ids = all_ids.append(id)
                        dupesite["point_id"] = id
                        self.__data = pd.concat((self.__data, dupesite))
        # TODO: problem: duped data is doubled. It should not be doubled. Sum is doubled but mean is normal- duped twice?
        print("Sum:", self.__data.groupby(["point_id"]).sum()) # TODO: Consider using this to assert that sites were duped correctly
        print("Mean:", self.__data.groupby(["point_id"]).mean()) # TODO: Consider using this to assert that sites were duped correctly
        return self.__data

    # Run after functions that change power factor (sum functions); recalculates it to be correct
    def __correct_power_factor(self, building):
        # Fix the power factor
        building["pf"] = building["power"] / building["apparent_power"]
        return building
    
    def __impute(
            self,
            outage_threshold: Optional[int] = 6 # Minimum # of missed consecutive readings to consider it an outage, not a meter failure
            ):
        max_fills = floor(outage_threshold / 2)
        self.__data = self.__data.infer_objects(copy=False)
        self.__data = self.__data.ffill(limit=max_fills)
        self.__data = self.__data.bfill(limit=max_fills)
        # TODO: log that fills took place
        na_rows = frame.loc[pd.isna(frame["power"]), :].index
        if not na_rows.empty:
            for row in na_rows:
                # TODO: Log it
                # Get similar data from one week ago
                # TODO: expand to check other potentially similar days in the recent past- same day of week, similar temp, season, etc.
                week_ago_date = (self.__data["timestamp"].iloc[row] - pd.Timedelta(7, "d")).date()
                week_ago_data = self.__data[self.__data["timestamp"] == week_ago_date]
                # Fill with prev data from year if available
                print("One week ago:", week_ago_date)
                # TODO: historical fill goes here
        frame = frame.fillna(0) # Catch anything the fill methods missed

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
        # TODO: save building to table in database?
        # Right now, we pickle it
        filename = "Building-" + str(self.__bid) + ".pkl"
        self.__data.to_pickle(filename)

