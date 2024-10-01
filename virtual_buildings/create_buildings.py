import pandas as pd
from lightphe import LightPHE
from os.path import exists
from os import makedirs, environ
import multiprocessing as mp
from numpy import random
from typing import Optional
from math import floor
from time import perf_counter

#import processor.pullMains as pulldb
from processor.commonDB import DBConn
from logger_config import config_logger
from config import DATABASE, ENCRYPT_COLS, PORTION_OF_CPU, ENCRYPT, OUTPUT_DIR, FIRST_BUILDING_ID, MIN_SIZE, MAX_SIZE, LIMIT_DATE, START_DATE, END_DATE

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

# Set up logger
logger = config_logger()

# Initialize with seed
def set_seed(seed: Optional[str] = None):
    randomizer = random.default_rng(seed)
    return randomizer

# Ensure trailing slash
if OUTPUT_DIR[-1] != "/":
    OUTPUT_DIR += "/"

# Building distribution
from scipy.stats import rv_discrete, lognorm, halfcauchy
class building_dist(rv_discrete):
    def _pmf(self, x, loc1, scale1, loc2, scale2, s):
        return halfcauchy.pdf(x, scale=scale1, loc=loc1) + lognorm.pdf(x, s, scale=scale2, loc=loc2)
    def get_equation(x, s, loc1, scale1, loc2, scale2):
        return halfcauchy.pdf(x, scale=scale1, loc=loc1) + lognorm.pdf(x, s, scale=scale2, loc=loc2)

# Gets a set of random building ids; used to create buildings
def choose_random_ids(seed: Optional[int] = None):
    randomizer = set_seed(seed)
    print("Generating building size.")
    # Get the building size
    loc1 = 1.83202980
    scale1 = 7.28441947e-03
    loc2 = 2.99999936
    scale2 = 2.72075073e+01
    s = 3.28533426
    count = -1 # Obviously invalid placeholder to initiate while loop
    dist = building_dist(name="building_dist")
    while count < MIN_SIZE or count > MAX_SIZE:
        count = int(dist.rvs(loc1=loc1, scale1=scale1, loc2=loc2, scale2=scale2, s=s, size=1)[0]) # Generate building size
    # Get possible IDs to choose from

    # Query times:
    # 6 units (26444, 27168, 33342, 51837, 25838, 26836): ~90 mins
    # 4 units (35390, 33789, 25973, 25291): ~30 mins
    # 3 units (26620, 59489, 47757); (26962, 33354, 51908): 5-10 mins, 22 w/encryption
    # 2 units (35390, 33789): ~1-2 mins

# TEMP FOR QUICK ENCRYPTION/AGGREGATION TESTING
    #count = 2
# TEMP

    print("Selecting building IDs.")
    with DBConn.create_connection(DATABASE) as conn:
        # TODO: what if site has no Mains? Is this ever the case in the data?
        # TODO: Buildings have different reading start dates; this needs to be accounted for
        # TODO: Add optional time range selection to limit output size
        query = "SELECT DISTINCT point_id FROM LABELS WHERE LABELS.circuit_label_type_id IN (15,16)" # Only mains
        if LIMIT_DATE == True:
            # Buildings don't always start on the first available day. Only include those that do start
            # before or on the start date to avoid large missing chunks of data
            # TODO: deal with provided date being before any data exists
            query = query + f" AND day_zero_dt <= '{START_DATE}'"
        query = query + ";"
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

def make_buildings(
        count, 
        pickle: bool,
        seed: Optional[int] = None):
    timer_start = perf_counter()
    for i in range(FIRST_BUILDING_ID, FIRST_BUILDING_ID + count):
        ids = choose_random_ids(seed)
        print("Creating building", i)
        building = Building(ids, encrypt=ENCRYPT, building_id=i, pickle=pickle)
        print("Building", i, "created.")
        #print(building.get_data())
    timer_end = perf_counter()
    time_taken = timer_end - timer_start
    print("Time taken to create", FIRST_BUILDING_ID + count, "buildings with encryption setting", ENCRYPT, ": ", time_taken, "seconds")

# The building class
class Building:
    def __init__(
        self,
        ids: list,
        database: Optional[str] = DATABASE,
        encrypt: Optional[bool] = True, # Whether or not to encrypt the building
        building_id: Optional[int] = 0, # Building ID, used for saving to file
        pickle: Optional[bool] = False # Whether to pickle the building to its own individual file
    ):
        # Set up variables
        self.__ids = ids
        self.__database = database
        self.__bid = building_id
        self.__encryption_enabled = encrypt
        self.__pickle = pickle
        self.__OUTPUT_DIR = OUTPUT_DIR

        # Check if we're limiting the date range for data retrieval;
        # if yes, prep for that and sanity check the date range provided
        if LIMIT_DATE == True:
            self.__limit_date = True
            # TODO: More involved sanity checks, such as "end date is after start date"
            if START_DATE != END_DATE:
                self.__start_date = START_DATE
                self.__end_date = END_DATE
        else:
            self.__limit_date = False

        # Sanity check for id list length (makes no sense to aggregate <2 buildings; there's
        # nothing to aggregate for size = 1, and 0 or negative sizes should not be possible
        # for this use-case)
        if len(self.__ids) < 2:
            print("Building must have at least two units.")
        else:
            print("Encryption status:", str(self.__encryption_enabled))
            self.__query_database() # Get data from the database
            self.__data = self.aggregate("15min") # Ensure we have all data in 15min intervals
            print(self.__data[self.__data["real_power"] > 0]) # Show proof that it worked

            # TODO: when changing resolution-
            # Make sure the aggregation interval is greater than the interval in the data-
            # reference duration column

            # If requested, encrypt the building.
            if self.__encryption_enabled == True:
                self.__keys = self.__setup_encryption() # Make or retrieve keys
                self.__data = self.encrypt_building() # Perform encryption

            # If requested, save the building to a pickle/binary file (.pkl)
            if self.__pickle == True:
                self.save_data()
                print("Building", self.__bid, "saved to pickle file.")
    
    def __str__(self):
        return self.__data.to_string(max_rows=20)

    # Sets up and exports or retrieves encryption keys;
    # returns a LightPHE Keys object
    def __setup_encryption(self) -> object:
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
        
    # Used to encrypt values; because we're doing this with multiprocessing to speed up
    # multi-column encryption, we need a worker process to encrypt each column.
    def worker(self, column):
        # The function used to encrypt a single value; needs to exist so that
        # pandas apply() can be used for better efficiency
        def encrypt_value(
            target # the value to encrypt
            ) -> int:
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
            query = f"SELECT * FROM POWER WHERE point_id IN {unique_ids}"
            if self.__limit_date == True:
                from datetime import datetime
                # Convert provided times to unix timestamps to match database format
                self.__start_date = datetime.strptime(self.__start_date, '%Y-%m-%d').timestamp()
                self.__end_date = datetime.strptime(self.__end_date, '%Y-%m-%d').timestamp()
                # Only retrieve values between the provided timestamps
                query = query + f" AND timestamp BETWEEN '{self.__start_date}' AND '{self.__end_date}'"
            query = query + ";"
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
        # Fill in missing timestamps
        # timestamp should be index
        start_datetime = target.index[0]
        end_datetime = target.index[-1] + pd.Timedelta(1, "d") # one day ahead for date_range to work properly
        fifteen_min_increments = pd.date_range(start=start_datetime, end=end_datetime, freq="15min", normalize=True, inclusive="left")
        new_index = pd.Index(fifteen_min_increments, name="timestamp")
        target = target.reindex(new_index)
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
                pass
                # Get similar data from one week ago
                # TODO: expand to check other potentially similar days in the recent past- same day of week, similar temp, season, etc.
                # Procedural way to know this?
                #week_ago_date = (target["timestamp"].iloc[row] - pd.Timedelta(7, "d")).date()
                #week_ago_data = target[target["timestamp"] == week_ago_date]
                # TODO: Fill with prev data from year if available
                #print("One week ago:", week_ago_date)
                # Figure out what timestamp is supposed to be

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
                #print(sitedata)
                self.__data[self.__data["site"] == site] = sitedata
            except Exception as ex:
                print("Building " + self.__bid + ": Could not resample: " + ex)
        return self.__data

    def aggregate(self, resolution):
        # For each matching timestamp, sum values at all sites
        print("Aggregating.")
        mains = self.__data
        # For each timestamp in the ids list, sum all values
        mains = mains.resample(resolution, on="timestamp").sum()
        mains = mains.groupby(by="timestamp").sum()
        # Fill in missing timestamps now that timestamps are unique
        mains = self.__impute(mains)
        #print(mains[mains["point_id"] == 0])
        # Set ID columns
        # point_id is repurposed to hold a tuple of point_ids in the building
        # ee_site_id is renamed to building_id and repurposed for that in case it winds up
        # in a frame with other buildings
        mains["point_id"] = str(self.__ids) # TODO: assign per row based on presence in aggregation?
        mains = mains.rename(columns={"ee_site_id": "building_id"}) 
        mains["building_id"] = self.__bid
        return mains
    

    def save_data(self):
        # TODO: save building to table in database?
        # Right now, we pickle it
        filename = "Building-" + str(self.__bid) + ".pkl"
        # Set directory path of output- output directory in config + "buildings" subdirectory
        # or "encrypted-buildings" if encryption enabled
        if self.__encryption_enabled == False:
            dirpath = self.__OUTPUT_DIR + "/buildings/"
        else:
            dirpath = self.__OUTPUT_DIR + "/encrypted-buildings/"
        if not exists(dirpath):
            makedirs(dirpath)
        # Save as file to output dir
        self.__data.to_pickle(dirpath + filename)

    def get_data(self):
        return self.__data

