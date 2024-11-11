from openfhe import *

#from lightphe import LightPHE
import pandas as pd
from os.path import exists
from os import makedirs
from numpy import random
from typing import Optional
from time import perf_counter, mktime
from datetime import datetime
import pickle

#import processor.pullMains as pulldb
from processor.commonDB import DBConn
from logger_config import config_logger
from config import DATABASE, ENCRYPT_COLS, BATCH_SIZE, BATCH_SIZE, BUILDING_COUNT, \
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
    if MIN_SIZE == MAX_SIZE:
        count = MIN_SIZE
    else:
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
            # TODO: deal with date being after data ends
            # TODO: parameterized query, not fstring
            query = query + f" AND day_zero_dt <= '{START_DATE}'"
        query = query + ";"
        results = conn.execute(query)
        ids = results.fetchall()
        cursor_obj = conn.cursor()
        # Select a random set from the results
        building_ids = randomizer.choice(ids, count, replace=True)
        # Verify that chosen IDs have results
        building_ids = list([id[0] for id in building_ids])
        valid_ids = []
        # Used to validate that data exists for period
        start = mktime(datetime.strptime(START_DATE, '%Y-%m-%d').timetuple())
        end = mktime(datetime.strptime(END_DATE, '%Y-%m-%d').timetuple())
        # Validate that data exists for period
        while len(valid_ids) < count:
            for id in building_ids:
                    # TODO: parameterized query, not fstring
                    # Check if data exists for this site
                    query = f"SELECT P REAL FROM POWER WHERE point_id={id}" 
                    if LIMIT_DATE == True:
                        # We checked start date above with the day_zero_dt check; this checks if it exists for long enough
                        query = query + f" AND timestamp BETWEEN {start} AND {end}" # BETWEEN {START_DATE} AND {END_DATE}"
                    query = query + ";"
                    results = conn.execute(query)
                    testresult = results.fetchone()
                    if testresult == [] or testresult == None or testresult == "None": # AKA: no data for that point in this time period
                        new_id = randomizer.choice(ids, 1, replace=True)[0][0]
                        del building_ids[building_ids.index(id)] # ID is invalid for period; drop it from options
                        try:
                            if id in ids:
                                del ids[ids.index(id)]
                            building_ids.append(new_id)
                            print(id, "replaced with", new_id)
                        except Exception as ex:
                            print("No valid ids for time period:", ex)
                            raise SystemExit
                    else:
                        if len(valid_ids) < count:
                            valid_ids.append(id)
                        else:
                            break
        # "it is recommended that applications run "PRAGMA optimize" (with no arguments) 
        # just before closing each database connection."
        # https://www.sqlite.org/pragma.html#pragma_optimize
        cursor_obj.execute("PRAGMA optimize;")
        cursor_obj.close()
    print("Valid IDs:", valid_ids)
    building_ids = tuple(valid_ids) # Format the selections into a tuple of ids
    return building_ids, randomizer

def make_buildings(
        count, 
        pickle: bool,
        seed: Optional[int] = None,
        encrypt: Optional[bool] = True):
    buildings = []
    timer_start = perf_counter()
    randomizer = set_seed(seed)
    for i in range(FIRST_BUILDING_ID, FIRST_BUILDING_ID + count):
        ids, randomizer = choose_random_ids(randomizer)
        print("Creating building", i)
        buildings.append(Building(ids, encrypt=encrypt, building_id=i, pickle=pickle))
        print("Building", i, "created.")
    timer_end = perf_counter()
    time_taken = timer_end - timer_start
    print("Time taken to create", count, "buildings with encryption setting", encrypt, ": ", time_taken, "seconds")
    print("Average time:", time_taken / BUILDING_COUNT)
    return buildings

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
                meter_data = self.__data[self.__data["point_id"] == meter]
                meter_data = self.impute(meter_data)
                imputed_data = pd.concat([imputed_data, meter_data])
            self.__data = imputed_data

            # If requested, encrypt the building.
            if self.__encryption_enabled == True:
                self.__cc, self.__keys, self.meter_order = self.__setup_encryption() # Make keys
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
    
    def get_keys(self):
        return self.__keypairs
    
    def get_cc(self):
        return self.__cc
    
    def get_meter_order(self):
        return self.meter_order

    # Sets up and exports or retrieves encryption keys;
    # returns a LightPHE Keys object
    def __setup_encryption(self):
        self.__KEY_LOCATION = "./keys/"
        # ----- Set parameters for cryptocontext -----
        parameters = CCParamsCKKSRNS()
        secret_key_dist = SecretKeyDist.GAUSSIAN #Gauss is best compromise between security and memory usage
        parameters.SetSecretKeyDist(secret_key_dist)
        #plaintextModulus = 65537
        #parameters.SetPlaintextModulus(plaintextModulus)
        securityLevel = SecurityLevel.HEStd_128_classic # TODO: 256-bit once this works properly
        parameters.SetSecurityLevel(securityLevel)
        sigma = 3.2
        parameters.SetStandardDeviation(sigma)
        digitSize = 30
        parameters.SetDigitSize(digitSize)

        if get_native_int()==128:
            rescale_tech = ScalingTechnique.FIXEDAUTO
            dcrt_bits = 78
            first_mod = 89
        else:
            rescale_tech = ScalingTechnique.FLEXIBLEAUTO
            dcrt_bits = 59
            first_mod = 60

        parameters.SetScalingModSize(dcrt_bits)
        parameters.SetScalingTechnique(rescale_tech)
        parameters.SetFirstModSize(first_mod)

        bootstrap_iterations = 1 # OpenFHE only supports 1 or 2; 2 has twice the precision gain
        level_budget = [1, 1]
        levels_available_after_bootstrap = 3
        depth = levels_available_after_bootstrap + FHECKKSRNS.GetBootstrapDepth(level_budget, secret_key_dist) + (bootstrap_iterations - 1)
        depth = 5
        parameters.SetMultiplicativeDepth(depth) # Higher values SIGNIFICANTLY slow encryption and risk OOM
        #parameters.SetThresholdNumOfParties(len(self.__ids))

        # Batch size needs to be a power of 2
        self.vector_length = BATCH_SIZE
        if (self.vector_length != 0) and (self.vector_length & (self.vector_length-1) != 0): # Is it NOT a power of 2?
                # Make it a power of 2. We'll zero-pad later since we're summing within a vector, and summing
                # values + 0 will equal summing the values themselves
                # Find the next power of 2 first
                for x in range(0, 100001): # TODO: set the second value sensibly
                    power_two = 2**(x-1).bit_length()
                    if power_two > BATCH_SIZE: # Found one! Set it.
                        self.vector_length = power_two
                        break
        self.__batch_size = BATCH_SIZE # Used to check for zero padding
        parameters.SetBatchSize(self.vector_length)

        # Enable relevant features
        cc = GenCryptoContext(parameters)
        cc.Enable(FHE)
        cc.Enable(PKE)
        cc.Enable(KEYSWITCH)
        cc.Enable(LEVELEDSHE)
        cc.Enable(ADVANCEDSHE)
        cc.Enable(MULTIPARTY)

        print("Checking encryption setup.")
        try:
            pass
            #cc.EvalBootstrapSetup(level_budget)
        except Exception as ex:
            print("Setup invalid:", ex, "\nCheck parameters.")
        
        # TODO: retrieve keys if they already exist
        # ---------- Generate keys ----------
        keypairs = {}
        multkeys = {}
        sumkeys = {}
        meter_order = []
        for meter in self.__ids:
            meter_order.append(meter)
            print("Preparing keys for meter", meter)
            if meter == meter_order[0]:
                print("Leader key generating.")
                # Leader meter generates key independently
                keypair = cc.KeyGen()
                keypairs[meter] = keypair
                # Evalmult key init
                leaderEvalMultKey = cc.KeySwitchGen(keypair.secretKey, keypair.secretKey)
                multkeys[meter] = leaderEvalMultKey
                # Evalsum key init
                cc.EvalSumKeyGen(keypair.secretKey)
                leaderEvalSumKeys = cc.GetEvalSumKeyMap(keypair.secretKey.GetKeyTag())
                # TODO: deal with duplicate site ids; how to differentiate which has which key?
                sumkeys[meter] = leaderEvalSumKeys
            else: # Follower meters behave differently from leader meter
                # Generate key using prev meter key as input
                print("Follower key generating.")
                keypair = cc.MultipartyKeyGen(keypairs[prev_meter].publicKey)
                keypairs[meter] = keypair
                # Generate multkey
                multkeys[meter] = cc.MultiKeySwitchGen(keypair.secretKey, keypair.secretKey, leaderEvalMultKey)
                # Generate sumkey
                sumkeys[meter] = cc.MultiEvalSumKeyGen(keypair.secretKey, leaderEvalSumKeys, keypair.publicKey.GetKeyTag())
            # Setup for next meter
            prev_meter = meter
            # If this is the last meter
            if meter == self.__ids[-1]:
                self.__shared_pubkey = keypair.publicKey

        # Generate the combined EvalMult key
        for meter in self.__ids:
            # Multkey round 1: MultiAdd
            meter_key = keypairs[meter]
            meter_multkey = multkeys[meter]
            if meter == self.__ids[0]:
                summed_multkey = meter_multkey
            else:
                summed_multkey = cc.MultiAddEvalKeys(summed_multkey, meter_multkey, meter_key.publicKey.GetKeyTag())
        # Multkey round 2: MultiMult
        multimult_keys = []
        last_key = keypairs[meter_order[-1]]
        for meter in meter_order:
            meter_key = keypairs[meter]
            meter_multimult = cc.MultiMultEvalKey(meter_key.secretKey, summed_multkey, last_key.publicKey.GetKeyTag())
            # order: [AABCDE, BABCDE, CABCDE, DABCDE, EABCDE]
            multimult_keys.append(meter_multimult)
        # Round 3: MultiAdd all the MultiMults together
        reversed_multimult_keys = multimult_keys[::-1] # Has to be done backwards; EABCDE first
        for multkey in reversed_multimult_keys:
            if "final_multikey" not in locals():
                final_multikey = multkey
            elif multkey == multimult_keys[-1]:
                final_multikey = cc.MultiAddEvalMultKeys(multkey, final_multikey, last_key.GetKeyTag())
            else:
                final_multikey = cc.MultiAddEvalMultKeys(multkey, final_multikey, multkey.GetKeyTag())
        # Multkey generation done
        cc.InsertEvalMultKey([final_multikey])

        # Generate the combined EvalSum key
        # Round 1: Add the keys together
        for meter in meter_order:
            # Multkey round 1: MultiAdd
            meter_key = keypairs[meter]
            meter_sumkey = sumkeys[meter]
            if meter == meter_order[0]:
                final_sumkey = meter_sumkey
            else:
                final_sumkey = cc.MultiAddEvalSumKeys(final_sumkey, meter_sumkey, meter_key.publicKey.GetKeyTag())
        # Sumkey done
        cc.InsertEvalSumKey(final_sumkey)
        # TODO Generate the EvalBootstrap key if needed


        # Save to object
        self.__cc = cc
        self.__keypairs = keypairs
        # Save to file
        # Keys
        #pickleable_keys = {}
        #for meter in self.__keypairs:
        #    print(meter)
        #    pickleable_keys[meter] = [self.__keypairs[meter].publicKey.GetKeyTag(), self.__keypairs[meter].secretKey]
        #pickleable_evalKeys = 0
        #with open(OUTPUT_DIR + str(self.__bid) + "-keys.pkl", "wb") as keyfile:
        #    pickle.dump(pickleable_keys, keyfile)
        # cc (needed for decryption- evalkeys)
        #with open(OUTPUT_DIR + self.__bid + "-cc.pkl", "wb") as ccfile:
        #    pickle.dump(cc, ccfile)
        return cc, keypairs, meter_order
                        
    # Encrypt all sensitive columns defined in config
    def encrypt_building(self):
        # Used for pandas.apply() to speed the process
        def encrypt_single_value(
            target, # the value to encrypt
            keys # The keypair to use
            ) -> int:
            if type(target) == int or type(target) == float:
                if target not in self.__value_map: # Encrypt and add to value map
                    plaintext = self.__cc.MakeCKKSPackedPlaintext([target, 0])
                    ciphertext = self.__cc.Encrypt(keys, plaintext)
                    self.__value_map[target] = ciphertext
                    return ciphertext
                else: # We've encrypted this value already. Return it.
                    return self.__value_map[target]
            else:
                raise TypeError("Column to encrypt must only contain floats and/or integers.")
            
        # The main function
        if BATCH_SIZE == 2: # Encrypting each reading individually
            for meter in self.__ids:
                self.__value_map = {} # Used to speed encryption by only encrypting each value once
                #meter_keys = self.__keypairs[meter]
                meter_data = self.__data[self.__data["point_id"] == meter]
                for column in meter_data.columns:
                    if column in ENCRYPT_COLS and column in self.__data.columns:
                        print("Encrypting", column)
                        if type(meter_data[column].iloc[0]) not in [Ciphertext, "object", object]: # Deals with duplicate sites
                            meter_data[column] = meter_data[column].apply(float) # Ensure data is compatible
                            meter_data[column] = meter_data[column].apply(encrypt_single_value, keys=self.__shared_pubkey)
                del self.__value_map
                self.__data[self.__data["point_id"] == meter] = meter_data

        elif BATCH_SIZE > 2: # One day of readings, together; aggregating within a meter
            for meter in self.__ids:
                self.__value_map = {} # Used to speed encryption by only encrypting each value once
                #meter_keys = self.__keypairs[meter]
                meter_keys = self.__shared_pubkey # The last pubkey is the one needed for encryption
                meter_data = self.__data[self.__data["point_id"] == meter]
                processed_columns = {}
                for column in meter_data.columns:
                    counter = 1
                    timestamp = meter_data.index[0]
                    if column in ENCRYPT_COLS and column in self.__data.columns:
                        print("Encrypting", column)
                        packed_vectors = {}
                        current_pack = []
                        index = 0
                        for reading in meter_data[column]:
                            current_pack.append(reading)
                            if counter < self.vector_length:
                                counter += 1
                            else:
                                timestamp = meter_data.index[meter_data[column].iloc(index)]
                                # Pad with zeroes if needed
                                print("Length of pre-padding pack:", len(current_pack))
                                if self.vector_length != BATCH_SIZE:
                                    while counter < self.vector_length:
                                        current_pack.append(0)
                                        counter += 1
                                packed_vectors[timestamp] = current_pack
                                counter = 1
                                print("Length of packed text:", len(current_pack))
                                current_pack = []
                            index += 1
                                
                        # ENCRYPT VECTORS HERE
                        # SUM ENCRYPTED VECTORS HERE
                        processed_columns[column] = packed_vectors
                    else: # Non-encrypted columns
                        aggregated_values = {}
                        current_value = 0
                        print("Summing pieces of", column)
                        for reading in column:
                            try:
                                int(reading)
                            except: # String columns should stay the same throughout
                                aggregated_values[timestamp] = column[0]
                                break
                            # IF all's well, then get to summing
                            current_value += reading
                            # We haven't finished adding yet
                            if counter < self.vector_length:
                                counter += 1
                            # Done adding this chunk, finish it and prep for the nect
                            else:
                                aggregated_values[timestamp] = current_value
                                timestamp = meter_data.index[meter_data[column].iloc(reading)]
                                counter = 1
                                current_value = 0
                        processed_columns[column] = aggregated_values
                # Rebuild frame
                partial_frames = []
                for column in processed_columns:
                    column_frame = pd.DataFrame(column)
                    partial_frames.append(column_frame)
                self.__data = pd.concat(partial_frames, axis=1)
                print(self.__data)
                raise SystemExit

        return self.__data
            
    # Retrieves data for component sites via SQL query
    # TODO: either eliminate this or eliminate need for static version.
    # Let's not duplicate a whole function unnecessarily
    # stores in self.__data
    # returns updated self.__data
    def query_database(self):
        with DBConn.create_connection(self.__database) as conn:
            print("Connected to database.")
            # We only need to query each id once. Convert to set to get unique.
            print("Building IDs:", self.__ids)
            unique_ids = tuple(set(self.__ids))
            if len(unique_ids) == 1:
                query = f"SELECT * FROM POWER WHERE point_id = {unique_ids[0]}"
            else:
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
                    all_ids.append(id)
                    dupesite["point_id"] = id
                    self.__data = pd.concat((self.__data, dupesite))
        # Timestamps need to be datetime for resample to work for aggregation
        self.__data['timestamp'] = pd.to_datetime(self.__data['timestamp'],unit='s')
        return self.__data

    # Staticmethod version of the query sites method;
    # here temporarily until I either no longer need to run the query outside of Building
    # or until it's established enough to become the main method for this.
    # Final should probably have only one.
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
        # For each timestamp in the ids list, sum all values
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
            aggregated_data = self.__data.groupby(by="timestamp").sum()
        else:
            # Aggregating encrypted data requires the use of EvalAdd
            aggregated_data = pd.DataFrame()
            for timestamp in pd.unique(self.__data.index):
                interval_records = self.__data[self.__data.index == timestamp]
                for record in range(0, interval_records["point_id"].size):
                    if "real_power" not in locals() or record == 0:
                        # This would work better as a loop?
                        duration = interval_records["duration"].iloc[record]
                        real_power = interval_records["real_power"].iloc[record]
                        apparent_power = interval_records["apparent_power"].iloc[record]
                        power_factor = interval_records["pf"].iloc[record]
                    else:
                        real_power = self.__cc.EvalAdd(real_power, interval_records["real_power"].iloc[record])
                        real_power = self.__cc.EvalSum(real_power, self.__batch_size)
                        duration = interval_records["duration"].iloc[record]
                        if type(apparent_power) == "object":
                            apparent_power = self.__cc.EvalAdd(apparent_power, interval_records["apparent_power"].iloc[record])
                            apparent_power = self.__cc.EvalSum(apparent_power, self.__batch_size)
                        else:
                            apparent_power += interval_records["apparent_power"].iloc[record]
                    # TODO Power factor needs to be recalculated here- rp / ap
                    # TODO build record for aggregated frame from this
                new_record = pd.DataFrame({"timestamp": interval_records.index[0], "point_id": 0, "ee_site_id": 0, "duration": duration, \
                                           "real_power": real_power, "apparent_power": apparent_power, "pf": 0}, index=["timestamp"])
                aggregated_data = pd.concat([aggregated_data, new_record])
        # Set ID columns
        # point_id is repurposed to hold a tuple of point_ids in the building
        # ee_site_id is renamed to building_id and repurposed for that in case it winds up
        # in a frame with other buildings
        aggregated_data["point_id"] = str(self.__ids) # TODO: assign per row based on presence in aggregation?
        aggregated_data = aggregated_data.rename(columns={"ee_site_id": "building_id"}) 
        aggregated_data["building_id"] = self.__bid
        print(aggregated_data)
        return aggregated_data
    

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