#from openfhe import *

#from lightphe import LightPHE
import pandas as pd
from os.path import exists
from os import makedirs
import multiprocessing as mp
from numpy import random
from typing import Optional
from math import floor
from time import perf_counter

#import processor.pullMains as pulldb
from processor.commonDB import DBConn
from logger_config import config_logger
from config import DATABASE, ENCRYPT_COLS, PORTION_OF_CPU, ENCRYPT, \
    OUTPUT_DIR, FIRST_BUILDING_ID, MIN_SIZE, MAX_SIZE, LIMIT_DATE, START_DATE, END_DATE

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

# Set up logger
logger = config_logger()

# Initialize with seed
def set_seed(seed: Optional[str] = None):
    if seed == None:
        seed = random.randint(100000000, 999999999)
        print("Random seed generated. Seed:", seed)
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
def choose_random_ids(randomizer: Optional[int] = None):
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
    building_ids = tuple([id[0] for id in building_ids]) # Format the selections into a tuple of ids
    return building_ids, randomizer

def make_buildings(
        count, 
        pickle: bool,
        seed: Optional[int] = None):
    timer_start = perf_counter()
    randomizer = set_seed(seed)
    for i in range(FIRST_BUILDING_ID, FIRST_BUILDING_ID + count):
        ids, randomizer = choose_random_ids(randomizer)
        print("Creating building", i)
        building = Building(ids, encrypt=ENCRYPT, building_id=i, pickle=pickle)
        print("Building", i, "created.")
    timer_end = perf_counter()
    time_taken = timer_end - timer_start
    print("Time taken to create", count, "buildings with encryption setting", ENCRYPT, ": ", time_taken, "seconds")
    print("Average time:", time_taken / BUILDING_COUNT)

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
            self.__ids = [id.item() for id in self.__ids] # Fix from numpy to native ints
            self.query_database() # Get data from the database

            # Fill in missing data
            imputed_data = pd.DataFrame()
            for meter in self.__ids:
                meter_data = self.__data[self.__data["point_id"] == int(meter)]
                meter_data = self.impute(meter_data)
                imputed_data = pd.concat([imputed_data, meter_data])
            self.__data = imputed_data

            # If requested, encrypt the building.
            if self.__encryption_enabled == True:
                self.__cc, self.__keys = self.__setup_encryption() # Make or retrieve keys
                self.__data = self.encrypt_building() # Perform encryption

            self.__data = self.aggregate("15min") # Ensure we have all data in 15min intervals
            #print(self.__data[self.__data["real_power"] > 0]) # Show proof that it worked

            # TODO: when changing resolution-
            # Make sure the aggregation interval is greater than the interval in the data-
            # reference duration column

            # If requested, save the building to a pickle/binary file (.pkl)
            if self.__pickle == True:
                self.save_data()
                print("Building", self.__bid, "saved to pickle file.")
    
    def __str__(self):
        return self.__data.to_string(max_rows=20)

    # Sets up and exports or retrieves encryption keys;
    # returns a LightPHE Keys object
    def __setup_encryption(self):
        self.__KEY_LOCATION = "./keys/"
        # Set parameters
        parameters = CCParamsCKKSRNS()
        parameters.SetMultiplicativeDepth(3)
        parameters.SetScalingModSize(50)
        # TODO: SET BATCH SIZE DYNAMICALLY
        batchSize = 2 # Smallest power of 2 that contains a point (1024 would be a full week)
        parameters.SetBatchSize(batchSize)

        # Enable relevant features
        cc = GenCryptoContext(parameters)
        cc.Enable(PKE)
        cc.Enable(KEYSWITCH)
        cc.Enable(LEVELEDSHE)
        cc.Enable(ADVANCEDSHE)
        cc.Enable(MULTIPARTY)
        # TODO: retrieve keys if they already exist
        # Generate keys
        keypairs = {}
        multkeys = {}
        sumkeys = {}
        for meter in self.__ids:
            print("Preparing keys for meter", meter)
            if meter == self.__ids[0]:
                # Leader meter generates key independently
                keypair = cc.KeyGen()
                keypairs[meter] = keypair
                # Evalmult key init
                evalMultKey = cc.KeySwitchGen(keypair.secretKey, keypair.secretKey)
                multkeys[meter] = evalMultKey
                # Evalsum key init
                cc.EvalSumKeyGen(keypair.secretKey)
                evalSumKeys = cc.GetEvalSumKeyMap(keypair.secretKey.GetKeyTag())
                sumkeys[meter] = evalSumKeys
            else: # Follower meters behave differently from leader meter
                # Generate key using prev meter key as input
                keypair = cc.MultipartyKeyGen(keypairs[prev_meter].publicKey)
                keypairs[meter] = keypair
                # Generate multkey
                multkeys[meter] = cc.MultiKeySwitchGen(keypair.secretKey, keypair.secretKey, evalMultKey)
                # Generate sumkey
                sumkeys[meter] = cc.MultiEvalSumKeyGen(keypair.secretKey, evalSumKeys, keypair.publicKey.GetKeyTag())
            # Setup for next meter
            prev_meter = meter

        # Generate the combined EvalMult key
        for meter in self.__ids:
            # Multkey round 1: MultiAdd
            meter_key = keypairs[meter]
            meter_multkey = multkeys[meter]
            if meter == self.__ids[0]:
                wip_multkey = meter_multkey
            else:
                wip_multkey = cc.MultiAddEvalKeys(wip_multkey, meter_multkey, meter_key.publicKey.GetKeyTag())
        # Multkey round 2: MultiMult
        multimult_keys = []
        for meter in self.__ids:
            meter_key = keypairs[meter]
            wip_multkey = cc.MultiMultEvalKey(meter_key.secretKey, wip_multkey, meter_key.publicKey.GetKeyTag())
            multimult_keys.append(wip_multkey)
        # Round 3: MultiAdd all the MultiMults together
        for key in multimult_keys:
            if "final_multikey" not in locals():
                final_multikey = key
            else:
                final_multikey = cc.MultiAddEvalMultKeys(key, final_multikey, key.GetKeyTag())
        # Multkey generation done
        cc.InsertEvalMultKey([final_multikey])

        # Generate the combined EvalSum key
        eval_sum_keys = []
        # Round 1: Add the keys together
        for meter in self.__ids:
            # Multkey round 1: MultiAdd
            meter_key = keypairs[meter]
            meter_sumkey = sumkeys[meter]
            if meter == self.__ids[0]:
                final_sumkey = meter_sumkey
            else:
                final_sumkey = cc.MultiAddEvalSumKeys(final_sumkey, meter_sumkey, meter_key.publicKey.GetKeyTag())
        # Sumkey done
        cc.InsertEvalSumKey(final_sumkey)
        # Save to object
        self.__cc = cc
        self.__keypairs = keypairs
        return cc, keypairs
                        
    # Encrypt all sensitive columns defined in config
    def encrypt_building(self):
        # Used for pandas.apply() to speed the process
        def encrypt_value(
            target, # the value to encrypt
            keys # The keypair to use
            ) -> int:
            if type(target) == int or type(target) == float:
                if target not in self.__value_map: # Encrypt and add to value map
                    plaintext = self.__cc.MakeCKKSPackedPlaintext([target])
                    ciphertext = self.__cc.Encrypt(keys.publicKey, plaintext)
                    self.__value_map[target] = ciphertext
                    return ciphertext
                else: # We've encrypted this value already. Return it.
                    return self.__value_map[target]
            else:
                raise TypeError("Column to encrypt must only contain floats and/or integers.")
            
        # The main function
        for meter in self.__ids:
            self.__value_map = {} # Used to speed encryption by only encrypting each value once
            meter_keys = self.__keypairs[meter]
            meter_data = self.__data[self.__data["point_id"] == meter]
            for column in meter_data.columns:
                if column in ENCRYPT_COLS and column in self.__data.columns:
                    print("Encrypting", column)
                    meter_data[column] = meter_data[column].apply(encrypt_value, keys=meter_keys)
            del self.__value_map
            self.__data[self.__data["point_id"] == meter] = meter_data
        return self.__data
            
    # Retrieves data for component sites via SQL query
    # stores in self.__data
    # returns updated self.__data
    def query_database(self):
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

    # Staticmethod version of the query sites method
    @staticmethod
    def query_for_sites(database_path, ids, start_date, end_date):
        with DBConn.create_connection(database_path) as conn:
            print("Connected to database.")
            # We only need to query each id once. Convert to set to get unique.
            print("Building IDs:", ids)
            unique_ids = tuple(set(ids))
            print("Unique IDs:", unique_ids)
            query = f"SELECT * FROM POWER WHERE point_id IN {unique_ids}"
            from datetime import datetime
            # Convert provided times to unix timestamps to match database format
            start_date = datetime.strptime(start_date, '%Y-%m-%d').timestamp()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').timestamp()
            # Only retrieve values between the provided timestamps
            query = query + f" AND timestamp BETWEEN '{start_date}' AND '{end_date}';"
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
        if 'bdata' not in locals(): # Frame does not exist yet
            bdata = pd.DataFrame.from_records(data=data, columns=columns)
        else: # Frame exists; add new data to existing frame
            newframe = pd.DataFrame.from_records(data=data, columns=columns)
            bdata = pd.concat([bdata, newframe])
        # Duplicate entries that are listed more than once in ids
        id_counts = pd.Series(data=ids).value_counts() # Find how many times IDs are duplicated
        all_ids = list(unique_ids) # Needs to be separate so we can append without affecting for loop
        for id in all_ids:
            if id_counts[id] > 1:
                print(id, "is duplicated", id_counts[id], "times.")
                for i in range(1, id_counts[id]):
                    # Duplicate ID into a new fake site
                    dupesite = bdata[bdata["point_id"] == id]
                    # Point ID of dupe needs to be changed; index must be unique
                    while id in unique_ids:
                        id += 1
                    all_ids = all_ids.append(id)
                    dupesite["point_id"] = id
                    bdata = pd.concat((bdata, dupesite))
        # Timestamps need to be datetime for resample to work for aggregation
        bdata['timestamp'] = pd.to_datetime(bdata['timestamp'],unit='s')
        return bdata

    # Run after functions that change power factor (sum functions); recalculates it to be correct
    def __correct_power_factor(self, building):
        # Fix the power factor
        building["pf"] = building["real_power"] / building["apparent_power"]
        return building
    
    @staticmethod
    def impute(
            target, # The frame to impute on
            outage_threshold: Optional[int] = 6 # Minimum # of missed consecutive readings to consider it an outage, not a meter failure
            ):
        print("Imputing missing data.") # TODO: only display after checking this is necessary
        if target.empty:
            print("Cannot impute on an empty frame.")
            return target
        # We need to zero any N/A PF values; many of these should be zero to begin with, but for those corresponding
        # to outages, it'll be recalculated after real and apparent power are imputed. We don't want the
        # should-be-zero PF values to be included when finding N/A rows.
        # Used to replace 0 values later- target should always have the same point_id, which is always
        # associated with the same ee_site_id
        ee_site_id = target["ee_site_id"].iloc[0]
        point_id = target["point_id"].iloc[0]
        # Fill in missing timestamps
        # timestamp should be index
        if "timestamp" in target.columns:
            target = target.set_index("timestamp")
        start_datetime = target.index[0]
        end_datetime = target.index[-1] + pd.Timedelta(1, "d") # one day ahead for date_range to work properly
        fifteen_min_increments = pd.date_range(start=start_datetime, end=end_datetime, freq="15min", normalize=True, inclusive="left")
        new_index = pd.Index(fifteen_min_increments, name="timestamp")
        target = target.reindex(index=new_index, method="nearest", limit=outage_threshold)
        # TODO: log that fills took place
        # TODO: Account for missing starts and ends; sites do not always have the same start/end dates
        # Find any remaining rows containing N/A that need more involved imputation
        #na_rows = target.loc[pd.isna(target["real_power"]), :].index
        target = target.fillna(0) # Catch anything the fill methods missed. TODO: Make sure to log this!
        # Fix ID columns for added rows
        target["ee_site_id"] = ee_site_id
        target["point_id"] = point_id
        print(target)
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
        #mains = mains.resample(resolution, on="timestamp").sum()

        """
        batchSize = 2
        for timestamp in mains["timestamp"].unique():
            if timestamp == mains["timestamp"].unique()[0]:
                aggregate = mains[mains["timestamp"] == timestamp] # one per building
            else:
                aggregate = cc.EvalAdd(aggregate, ciphertext2)
            ciphertextAdd12 = cc.EvalAdd(ciphertext1, ciphertext2)
            ciphertextSum = cc.EvalSum(ciphertextAdd12, batchSize)
        """
        if self.__encryption_enabled == False:
            mains = mains.groupby(by="timestamp").sum()
        else:
            # Aggregating is harder
            pass
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


if __name__ == "__main__":
    from config import BUILDING_COUNT, SEED
    make_buildings(BUILDING_COUNT, pickle=False, seed=SEED)