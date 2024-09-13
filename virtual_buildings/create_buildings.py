import pandas as pd
from lightphe import LightPHE
from os.path import exists
from os import environ
import multiprocessing as mp
from numpy import random
from typing import Optional
from scipy.stats import halfcauchy
from math import floor

#import processor.pullMains as pulldb
from processor.commonDB import DBConn
from logger_config import config_logger
from config import DATABASE, SEED, ENCRYPT_COLS, PORTION_OF_CPU

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

# TEMP FOR QUICK ENCRYPTION TESTING
    count = 50
# TEMP

    print("Selecting building IDs.")
    with DBConn.create_connection(DATABASE) as conn:
        # TODO: what if site has no Mains? Is this ever the case in the data?
        # TODO: Buildings have different reading start dates; this needs to be accounted for
        # TODO: Add optional time range selection to limit output size
        query = "SELECT DISTINCT point_id FROM LABELS WHERE LABELS.circuit_label_type_id IN (15,16)" # Only mains
        results = conn.execute(query)
        ids = results.fetchall()
        cursor_obj = conn.cursor()
        # "it is recommended that applications run "PRAGMA optimize" (with no arguments) 
        # just before closing each database connection."
        # https://www.sqlite.org/pragma.html#pragma_optimize
        cursor_obj.execute("PRAGMA optimize;")
        cursor_obj.close()
    # Select a random set from the results
    building_ids = randomizer.choice(ids, count, replace=True)
    building_ids = tuple([id[0] for id in building_ids])
    return building_ids

def make_buildings(count):
    for i in range(0, count):
        ids = choose_random_ids()
        print("Creating building", i)
        building = Building(ids, encrypt=True, building_id=i, pickle=True) # encryption false to check this works
        print("Building", i, "created.")
        print(building.get_data())

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
            self.__query_database()
            self.__data = self.aggregate("15min")

            # TODO: when changing resolution-
            # Make sure the aggregation interval is greater than the interval in the data-
            # reference duration column

            if self.__encryption_enabled == True:
                self.__keys = self.__setup_encryption()
                self.__data = self.encrypt_building()

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
                    print("Unable to export keys. Decryption may fail. Reason: " + str(ex))
                return keys
            elif exists(self.__KEY_LOCATION + "private.txt"):
                privkey = LightPHE(algorithm_name = self.__ALGORITHM, key_file=self.__KEY_LOCATION + "private.txt")
                return privkey
            else:
                print("Encryption setup failed.")
                raise SystemExit
        except:
            print("Key generation failure. Aborting.")
            raise SystemExit
        
    def worker(self, column):
        def encrypt_value(
            target # the value to encrypt
            ):
            if type(target) == int or type(target) == float:
            # HE doesn't always play nicely with floats; conversion to INT is needed
            # This conversion will be removed if we switch to CKKS
                decimal_places = 8 # How many decimal places to keep; needs to be the same when decrypted
                CONVERSION_SCALAR = 10**decimal_places
                if target not in self.__value_map: # Encrypt and add to value map
                    encrypted_value = self.__keys.encrypt(int(float(target) * CONVERSION_SCALAR))
                    self.__value_map[target] = encrypted_value
                    return encrypted_value
                else: # We've encrypted this value already. Return it.
                    return self.__value_map[target]
            else:
                raise TypeError("Column to encrypt must only contain floats and/or integers.")
            
        # Worker main function starts here
        try:
            if column in ENCRYPT_COLS and column in self.__data.columns:
                print("Encrypting", column)
                encrypted_column = self.__data[column].apply(encrypt_value)
                return (encrypted_column, column)
            elif column in ENCRYPT_COLS:
                print("Column", column, "does not exist in data frame.")
                return ("Column does not exist:  " + column, column)
            elif column in self.__data.columns:
                print(column, "not in list of columns to encrypt.")
                return (self.__data[column], column)
            else:
                print("No columns to encrypt and/or column", column, "not in data frame.")
                return ("Encryption failed for " + column, column)
        except Exception as ex:
            print("Could not encrypt", column + ":", ex)
            return ("Encryption failed for " + column, column)
                        
    # Encrypt all sensitive columns defined in config
    def encrypt_building(self):
        # Took about 90 mins for 4 sites over whole time period
        processors = mp.cpu_count()
        processors = floor(processors * PORTION_OF_CPU)
        results = {}
        self.__value_map = {} # Used to speed encryption by only encrypting each value once
        with mp.Pool(processes=processors) as pool:
            try:
                encrypted_outputs = pool.map(self.worker, self.__data.columns)
            except KeyboardInterrupt:
                pool.terminate()
        for result in encrypted_outputs:
                print(result)
                column = result[1]
                data = result[0]
                results[column] = data
        for column in results:
            self.__data[column] = results[column]
        print(self.__data)
        del self.__value_map
        return self.__data
            
    # Retrieves data for component sites via SQL query
    # stores in self.__data
    # returns updated self.__data
    def __query_database(self):
        with DBConn.create_connection(self.__database) as conn:
            print("Connected to database.")
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
            print("Query done. Retrieving (this may take a while)...")
            data = []
            cursor_obj = conn.cursor()
            # Retrieve the rows queried. This is the relative slow step in querying; it runs quickly
            # for 2 units but slows down as more units are added to the building and more rows must be
            # retrieved.
            # TODO: Test values for best speed. 10000 better than 100000; will smaller help even more?
            cursor_obj.arraysize = 10000 # May speed up retrieval; sets how many rows are fetched by fetchmany()
            while True:
                # Fetchmany allows both performance improvements over fetchall() and prevents MemoryError for invalid id values
                chunk = results.fetchmany()
                if chunk == []: # fetchmany returns empty list if there are no more results
                    break
                else:
                    data = data + chunk # Append to list of records
            # "it is recommended that applications run "PRAGMA optimize" (with no arguments) 
            # just before closing each database connection." This should be very fast or a no-op.
            # https://www.sqlite.org/pragma.html#pragma_optimize
            print("Retrieved. Cleaning up (do not interrupt)...")
            try:
                cursor_obj.execute("PRAGMA optimize;")
                cursor_obj.close()
            except KeyboardInterrupt:
                cursor_obj.close()

        # Needed to concatenate frames properly because from_records() needs a list of columns
        columns = ['ee_site_id', 'point_id', 'timestamp', 'duration', 'real_power', 'apparent_power', 'pf'] # used for frame creation
        # Transfer records into a data frame for easier processing
        if not hasattr(self, '__data'): # Frame does not exist yet
            self.__data = pd.DataFrame.from_records(data=data, columns=columns)
        else: # Frame exists; add new data to existing frame
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
        # Timestamps need to be datetime for resample to work for aggregation
        self.__data['timestamp'] = pd.to_datetime(self.__data['timestamp'],unit='s')
        # TODO: Save the site IDs so they can be identified later
        # TODO: account for different start dates when including site IDs in rows
        return self.__data

    # Run after functions that change power factor (sum functions); recalculates it to be correct
    def __correct_power_factor(self, building):
        # Fix the power factor
        building["pf"] = building["real_power"] / building["apparent_power"]
        return building
    
    def __impute(
            self,
            target, # The frame to impute on
            outage_threshold: Optional[int] = 6 # Minimum # of missed consecutive readings to consider it an outage, not a meter failure
            ):
        print("Imputing missing data.") # TODO: only display after checking this is necessary
        # We need to zero any N/A PF values; many of these should be zero to begin with, but for those corresponding
        # to outages, it'll be recalculated after real and apparent power are imputed. We don't want the
        # should-be-zero PF values to be included when finding N/A rows.
        target["pf"] = target["pf"].fillna(0)
        # Simple fills first: chains of less than the outage_threshold can be forward or backward filled.
        max_fills = floor(outage_threshold / 2)
        target = target.infer_objects(copy=False)
        target = target.ffill(limit=max_fills)
        target = target.bfill(limit=max_fills)
        # TODO: log that fills took place
        # TODO: Account for missing starts and ends; sites do not always have the same start/end dates
        # Find any remaining rows containing N/A that need more involved imputation
        na_rows = target.loc[pd.isna(target["real_power"]), :].index
        if not na_rows.empty: # If we have N/A rows
            for row in na_rows:
                # Get similar data from one week ago
                # TODO: expand to check other potentially similar days in the recent past- same day of week, similar temp, season, etc.
                # Procedural way to know this?
                week_ago_date = (target["timestamp"].iloc[row] - pd.Timedelta(7, "d")).date()
                week_ago_data = target[target["timestamp"] == week_ago_date]
                # TODO: Fill with prev data from year if available
                print("One week ago:", week_ago_date)
        target = target.fillna(0) # Catch anything the fill methods missed. TODO: Make sure to log this!
        return target

    def change_resolution(self, resolution): # resolution should be a valid resample value
        # Do each point separately to avoid duplicate timestamp issues
        siteids = self.__data["ee_point_id"]
        for site in siteids:
            try:
                sitedata = self.__data[self.__data["site"] == site]
                # Resample to desired time resolution
                sitedata = sitedata.resample(resolution, on="timestamp").sum()
                # Power factor will be inaccurate; should be 1 or less. Recalculate it.
                sitedata = self.__correct_power_factor(self.__data)
                # Place aggregated site back into sitedata
                print(sitedata)
                self.__data[self.__data["site"] == site] = sitedata
            except Exception as ex:
                print("Building " + self.__bid + ": Could not resample: " + ex)
        return self.__data

    def aggregate(self, resolution):
        # For each matching timestamp, sum values at all sites
        print("Aggregating.")
        mains = self.__data
        mains = self.__impute(mains)
        # For each timestamp in the ids list, sum all values
        # TODO: Impute BEFORE doing this
        mains = mains.resample(resolution, on="timestamp").sum()
        return mains
    

    def save_data(self):
        # TODO: save building to table in database?
        # Right now, we pickle it
        filename = "Building-" + str(self.__bid) + ".pkl"
        self.__data.to_pickle(filename)

    def get_data(self):
        return self.__data

