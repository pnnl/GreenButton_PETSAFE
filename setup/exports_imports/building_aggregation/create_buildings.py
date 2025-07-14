#from openfhe import *

import pandas as pd
from os.path import exists
from os import makedirs
from numpy import random
from typing import Optional
from time import perf_counter, mktime
from datetime import datetime, timedelta
from math import floor
from numpy import nan
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta # DST calculations

#import processor.pullMains as pulldb
from processor.commonDB import DBConn
import config

# Setting copy on write for PANDAS as recommended here:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
pd.options.mode.copy_on_write = True

# Initialize with seed for deterministic rng
def set_seed(seed: Optional[str] = None):
    if seed == None:
        seed = random.randint(100000000, 999999999)
        #print("Random seed generated. Seed:", seed)
    randomizer = random.default_rng(seed)
    return randomizer

# Ensure trailing slash
if config.OUTPUT_DIR[-1] != "/":
    config.OUTPUT_DIR += "/"

# Building distribution
from scipy.stats import rv_discrete, lognorm, halfcauchy
class building_dist(rv_discrete):
    def _pmf(self, x, loc1, scale1, loc2, scale2, s):
        return halfcauchy.pdf(x, scale=scale1, loc=loc1) + lognorm.pdf(x, s, scale=scale2, loc=loc2)
    def get_equation(x, s, loc1, scale1, loc2, scale2):
        return halfcauchy.pdf(x, scale=scale1, loc=loc1) + lognorm.pdf(x, s, scale=scale2, loc=loc2)

# Gets a set of random building ids; used to create buildings
# rng: randomizer object used to select ids 
def choose_random_ids(rng: Optional[int] = None):
    randomizer = rng
    print("Generating building size.")
    # Get the building size
    # Numbers generated using tools/fit-curve.py to fit distribution
    # to range of actual building sizes
    loc1 = 1.83202980
    scale1 = 7.28441947e-03
    loc2 = 2.99999936
    scale2 = 2.72075073e+01
    s = 3.28533426
    dist = building_dist(name="building_dist")
    if config.MIN_SIZE == config.MAX_SIZE: # If we want a building of a specific size
        count = config.MIN_SIZE
    else: # If we need to generate the building's unit count within a provided range
        count = -1
        while count < config.MIN_SIZE or count > config.MAX_SIZE or not count:
            count = int(dist.rvs(loc1=loc1, scale1=scale1, loc2=loc2, scale2=scale2, s=s, size=1)[0]) # Generate building size
    # Get possible IDs to choose from
    print("Selecting building IDs.")
    try:
        with DBConn.create_connection(config.DATABASE) as conn:
            # TODO: what if site has no Mains? Is this ever the case in the data?
            query = "SELECT DISTINCT point_id FROM LABELS WHERE LABELS.circuit_label_type_id IN (15,16)" # Only mains
            if config.LIMIT_DATE == True:
                # Buildings don't always start on the first available day. Only include those that do start
                # before or on the start date to avoid large missing chunks of data
                # TODO: parameterized query, not fstring (fstring query is injection vuln)
                query = query + f" AND day_zero_dt <= '{config.START_DATE}'"
            results = conn.execute(query + ";")
            ids = results.fetchall() # ID count is small enough for fetchall() to be non-issue
            # Select a random set of IDs (set size = count) from the results
            initial_building_ids = randomizer.choice(ids, count, replace=False)
            #print(initial_building_ids) # Debug for convenience

            # Prep to verify that chosen IDs have results for given time period
            id_test_queue = list([id[0] for id in initial_building_ids]) # Original format not malleable
            valid_ids = []
            # Used to validate that data exists within this period;
            # dates are stored as Unix timestamps, so start/end datetimes need to match formats to compare
            start = mktime(datetime.strptime(config.START_DATE, '%Y-%m-%d').timetuple())
            end = mktime(datetime.strptime(config.END_DATE, '%Y-%m-%d').timetuple())

            # Get COUNT() of readings for this time period
            # Used to check that enough data exists to use the point_id in buildings
            while len(valid_ids) < count:
                for id in id_test_queue:
                    # TODO: parameterized query, not fstring; fstring is injection vuln
                    # Check if data exists for this site
                    query = f"SELECT COUNT(*) FROM POWER WHERE point_id={id}" 
                    if config.LIMIT_DATE == True:
                        query = query + f" AND timestamp BETWEEN {start} AND {end}" # BETWEEN {START_DATE} AND {END_DATE}"
                    results = conn.execute(query + ";")
                    valid_results = results.fetchone()[0] # COUNT() of results
                    # Max possible expected number of results = readings_per_day * number of days in requested period
                    # Not worried about duplicate readings for now.
                    # TODO in long-term: validate that it's not just a long chain of the same reading repeated, just in case?
                    readings_per_day = 96
                    max_readings_in_period = readings_per_day * int((datetime.strptime(config.END_DATE, '%Y-%m-%d') \
                                                             - datetime.strptime(config.START_DATE, '%Y-%m-%d')).days)
                    min_valid_results = floor(max_readings_in_period * config.REQUIRED_PORTION) # Number required to accept the site

                    # Finally, validate that enough data exists in the site for usage
                    if valid_results < min_valid_results: # AKA: not enough data for that point in this time period
                        # Get a new ID to replace the invalid one
                        new_id = randomizer.choice(ids, 1, replace=False)[0][0] # [][] removes from default list nesting result (SQL(row()))
                        del id_test_queue[id_test_queue.index(id)] # ID is invalid for period; drop it from options
                        try:
                            if id in ids:
                                # Remove the invalid point_id for future selections
                                del ids[ids.index(id)]
                            id_test_queue.append(new_id) # Setup to check the new ID's validity
                        except Exception as ex: # We usually hit this point when running out of IDs
                            print("Could not select valid ids for time period:", ex)
                            raise SystemExit # Quit. TODO: just quit this call, not the whole program?
                    else: # Site has enough data to be usable
                        if len(valid_ids) < count and id not in valid_ids: # We still need more unique valid ids
                            valid_ids.append(id)
                            continue
                        elif len(valid_ids) >= count: # We have enough valid ids, exit loop
                            break
            # "it is recommended that applications run "PRAGMA optimize" (with no arguments) 
            # just before closing each database connection."
            # https://www.sqlite.org/pragma.html#pragma_optimize
            cursor_obj = conn.cursor()
            cursor_obj.execute("PRAGMA optimize;")
            cursor_obj.close()
    except TypeError:
        print("Database not found.")
        return ()
    print("Valid IDs:", valid_ids)
    valid_ids = tuple(valid_ids) # Format the selections into a tuple of ids; makes queries easier
    return valid_ids

# Make a set number of buildings
# count: how many buildings to make
# pickle: whether to save buildings as .pkl files (currently only works unencrypted)
# seed: seed to use for rng for point_id selection
# encrypt: whether to encrypt the building
# Outputs a list of Building objects
# Prints statistics about the time needed to make buildings
def make_buildings(
        count: int, 
        pickle: bool,
        seed: Optional[int] = None,
        encrypt: Optional[bool] = True):
    buildings = []
    timer_start = perf_counter()
    randomizer = set_seed(seed)
    for i in range(config.FIRST_BUILDING_ID, config.FIRST_BUILDING_ID + count):
        ids = choose_random_ids(randomizer)
        print("Creating building", i)
        buildings.append(Building(ids, encrypt=encrypt, building_id=i, pickle=pickle))
        print("Building", i, "created.")
    timer_end = perf_counter()
    time_taken = timer_end - timer_start
    print("Time taken to create", count, "buildings with encryption setting", encrypt, ": ", time_taken, "seconds")
    print("Average time:", time_taken / config.BUILDING_COUNT)
    return buildings

def is_dst(when):
    #Given the name of Timezone will attempt determine if that timezone 
    # is in Daylight Saving Time now (DST) - see
    # https://gist.github.com/dpapathanasiou/09bd2885813038d7d3eb
    return when.dst() != timedelta(0)

# Find days where Daylight Savings kicks in for a time zone
# Edited from https://zetcode.com/python/time-daylight/
# Returns a list of datetimes where the date is a daylight savings
# transition for tz
def find_dst_transitions(
        years: list, 
        tz: str
        ):
    transitions = []
    last_dst = None
    # For each year tested...
    for year in years:
        # Check each day of the year
        delta = relativedelta(years=1)
        # Noon is to catch the DST transition! Midnight would give
        # an off by one error
        this_date = datetime(year, 1, 1, 12, 0, 0, 0, tzinfo=tz)
        end_date = this_date + delta
        while this_date <= end_date:
            local_time = this_date
            current_dst = is_dst(local_time)
            if last_dst is not None and current_dst != last_dst:
                print("DST transition found by find_dst_transitions():", local_time)
                # Timedelta is so it's returned at midnight, not noon
                # to ensure time selection stays accurate
                transitions.append(local_time - timedelta(hours=12))
            last_dst = current_dst
            this_date = this_date + timedelta(days=1)
    return transitions

# The building class
class Building:
    def __init__(
        self,
        ids: list,
        database: Optional[str] = config.DATABASE,
        encrypt: Optional[bool] = True, # Whether or not to encrypt the building
        building_id: Optional[int] = 0, # Building ID, used for saving to file
        pickle: Optional[bool] = False # Whether to pickle the building to its own individual file
    ):
        # Set up variables
        self.__ids = ids
        self.__bid = building_id
        self.__encryption_enabled = encrypt
        self.__pickle = pickle
        self.__OUTPUT_DIR = config.OUTPUT_DIR
        self.UTC = ZoneInfo("UTC")

        # Data quality encodings- giving names for easier understanding
        self.quality = {
        "valid": 0,
        "estimated_reference_day": 8,
        "estimated_interpolation": 9,
        "questionable": 10,
        "derived": 11,
        "mixed": 13,
        "raw": 14,
        "other": 16
        }

        # Check if we're limiting the date range for data retrieval;
        # if yes, prep for that and sanity check the date range provided
        if config.LIMIT_DATE == True:
            self.__limit_date = True
            # TODO: More involved sanity checks, such as "end date is after start date"
            if config.START_DATE != config.END_DATE:
                self.__start_date = config.START_DATE
                self.__end_date = config.END_DATE
        else:
            self.__limit_date = False
            self.__start_date = None
            self.__end_date = None

        # Sanity check for id list length (makes no sense to aggregate <2 buildings; there's
        # nothing to aggregate for size = 1, and 0 or negative sizes should not be possible
        # for this use-case)
        if len(self.__ids) < 2:
            print("Building must have at least two units.")
        else:
            print("Encryption status:", str(self.__encryption_enabled))
            self.__ids = [id.item() for id in self.__ids] # Fix from numpy to native ints
            #self.query_database() # Get data from the database
            self.__data = self.query_for_sites(database, self.__ids, self.__start_date, self.__end_date)

            # Fill in missing data
            first_meter = True
            for meter in self.__ids:
                meter_data = self.__data[self.__data["point_id"] == meter]
                imputed_data = self.impute(meter_data) 
                # Make sure it all ends up in a frame so it can be aggregated!
                if first_meter == True:
                    all_imputed_data = imputed_data
                    first_meter = False
                else:
                    all_imputed_data = pd.concat([all_imputed_data, imputed_data])
            self.__data = all_imputed_data

            # If requested, encrypt the building.
            if self.__encryption_enabled == True:
                self.__setup_encryption() # Make keys
                self.__data = self.encrypt_building() # Perform encryption
            else: # Otherwise, set params as needed to indicate no encryption was performed
                #vector = self.__data[self.__data["point_id"] == self.__ids[0]]
                #first_day = vector.index[0].date()
                #vector = vector.loc[first_day:(first_day + pd.Timedelta(1, "d"))]
                #vector = vector[0:-1] # loc is right-inclusive. We don't want that. Drop the rightmost.
                self.vector_length = self.__data["real_power"].size
                print("Vector length:", self.vector_length)
                self.__cc = None
            # Aggregate the building and prep for use
            self.__data = self.aggregate()
            if "timestamp" in self.__data.columns:
                self.__data = self.__data.set_index(["timestamp"])

            # TODO: when changing resolution-
            # Make sure the aggregation interval is greater than the interval in the data-
            # reference duration column

            # If requested, save the building to a pickle/binary file (.pkl)
            # 2024-11-18: only works with unencrypted data
            if self.__pickle == True:
                self.save_data()
                print("Building", self.__bid, "saved to pickle file.")
    
    def __str__(self):
        return self.__data.to_string(max_rows=20)
    
    # Test whether batch_size variable size is valid. Must be a power of 2 to encrypt successfully
    # If valid, vector_length = batch_size
    # If not a power of 2, find the nearest power of 2 and set vector_length to that
    # so we can pad values if needed to fill it
    # Returns the smallest valid size
    def __eval_batch_size(self):
        self.vector_length = config.BATCH_SIZE
        if (self.vector_length != 0) and (self.vector_length & (self.vector_length-1) != 0): # Is it NOT a power of 2?
                # Make it a power of 2. We'll zero-pad later since we're summing within a vector, and summing
                # values + 0 will equal summing the values themselves
                # Find the next power of 2 first
                for x in range(0, 100001): # TODO: set the second value sensibly
                    power_two = 2**(x-1).bit_length()
                    if power_two > config.BATCH_SIZE: # Found one! Set it.
                        self.vector_length = power_two
                        break
        self.__batch_size = config.BATCH_SIZE # Used to check for zero padding
        return self.vector_length

    # Sets up encryption keys for "meters"
    # returns cc, keypairs, meter_order
    # cc: cryptocontext object
    # keypairs: the keys for each meter
    # meter_order: the order meters encrypt and decrypt in for threshold encryption
    def __setup_encryption(self):
        # TODO: save keys somewhere
        # self.__KEY_LOCATION = "./keys/"
        # ----- Set parameters for cryptocontext -----
        parameters = CCParamsCKKSRNS()
        secret_key_dist = SecretKeyDist.GAUSSIAN #Gauss is best compromise between security and memory usage
        parameters.SetSecretKeyDist(secret_key_dist)
        securityLevel = SecurityLevel.HEStd_128_classic # TODO: 256-bit?
        parameters.SetSecurityLevel(securityLevel)
        sigma = 3.2
        parameters.SetStandardDeviation(sigma)
        digitSize = 30
        parameters.SetDigitSize(digitSize)

        # No need to manually call Rescale()
        rescale_tech = ScalingTechnique.FLEXIBLEAUTO
        # Highest possible values for FLEXIBLEAUTO
        dcrt_bits = 59
        first_mod = 60
        parameters.SetScalingModSize(dcrt_bits)
        parameters.SetScalingTechnique(rescale_tech)
        parameters.SetFirstModSize(first_mod)

        bootstrap_iterations = 1 # OpenFHE only supports 1 or 2; 2 has twice the precision gain, but is much slower
        level_budget = [3, 3]
        levels_available_after_bootstrap = 3
        depth = levels_available_after_bootstrap + FHECKKSRNS.GetBootstrapDepth(level_budget, secret_key_dist) + (bootstrap_iterations - 1)
        depth = 5 # Temp: any higher gets the OOM killer's attention as of 2024-11-18
        parameters.SetMultiplicativeDepth(depth) # Higher values SIGNIFICANTLY slow encryption and risk OOM

        # Batch size needs to be a power of 2
        self.vector_length = self.__eval_batch_size()
        parameters.SetBatchSize(self.vector_length)

        # Enable relevant features
        cc = GenCryptoContext(parameters)
        cc.Enable(FHE) # Fully homomorphic encryption
        cc.Enable(PKE) # Asymmetric cryptography
        cc.Enable(KEYSWITCH) # Keyswitching; needed for threshold
        cc.Enable(LEVELEDSHE) # Leveled Somewhat Homomorphic ; needed for EvalSumKeyGen for automorphism
        cc.Enable(ADVANCEDSHE) # Advanced Somewhat Homomorphic Encryption; needed for EvalSumKey
        cc.Enable(MULTIPARTY) # Threshold encryption

        print("Checking encryption setup.")
        try:
        # Commented out because with larger bootstrap parameters, OOM killer decides to step in
            #cc.EvalBootstrapSetup(level_budget)
            pass
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
                # Temporarily disabled duplicates in the meantime, but long-term, this is an issue
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
            # s_a + s_b
            meter_key = keypairs[meter]
            meter_multkey = multkeys[meter]
            if meter == self.__ids[0]:
                summed_multkey = meter_multkey
            else:
                summed_multkey = cc.MultiAddEvalKeys(summed_multkey, meter_multkey, meter_key.publicKey.GetKeyTag())
        # Multkey round 2: MultiMult
        # S_a + s_b -> s_b*(s_a + s_b) and s_a*(s_a + s_b)
        multimult_keys = []
        last_key = keypairs[meter_order[-1]]
        for meter in meter_order:
            meter_key = keypairs[meter]
            meter_multimult = cc.MultiMultEvalKey(meter_key.secretKey, summed_multkey, last_key.publicKey.GetKeyTag())
            # example results order: [AABCDE, BABCDE, CABCDE, DABCDE, EABCDE]
            multimult_keys.append(meter_multimult)
        # Round 3: MultiAdd all the MultiMults together
        # s_b*(s_a + s_b) and s_a*(s_a + s_b) -> (s_a + s_b)*(s_a + s_b)
        reversed_multimult_keys = multimult_keys[::-1] # Has to be done backwards as per lib example code; EABCDE first
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
        self.meter_order = meter_order
        # TODO: Save to file
        return cc, keypairs, meter_order
                        
    # Encrypts all sensitive columns defined in config
    # Returns the encrypted frame
    # Method used depends on config.STAT_TEMPORAL_RESOLUTION;
    # individual readings are encrypted for "f" (15 minutes resolution),
    # else vectors are made accordingly
    # Currently supports 15mins and 1day resolutions
    def encrypt_building(self):
        # Used for pandas.apply() to speed the process
        def encrypt_single_value(
            target, # the value to encrypt
            keys # The keypair to use
            ) -> int:
            # Check that target type is valid for encryption
            if type(target) == int or type(target) == float:
                plaintext = self.__cc.MakeCKKSPackedPlaintext([target, 0])
                if not hasattr(self, "vector_length"): # Value needed for decryption
                    # TODO: can this be stored encrypted at all to prevent information leakage?
                    self.vector_length = plaintext.GetLength()
                ciphertext = self.__cc.Encrypt(keys, plaintext)
                return ciphertext
            else: # Value type is invalid for encryption purposes
                raise TypeError("Column to encrypt must only contain floats and/or integers.")
            
        # The main function
        if config.STAT_TEMPORAL_RESOLUTION == "d":
            all_days =  pd.date_range(start=config.START_DATE, end=config.END_DATE, freq="d", normalize=True, inclusive="both")
            print("Encrypting", config.ENCRYPT_COLS)
            for meter in self.__ids:
                meter_data = self.__data[self.__data["point_id"] == meter]
                aggregate_days = []
                for day in all_days:
                    # Get the day's data
                    try:
                        day_data = meter_data[day:(day + pd.Timedelta(1, "d"))]
                    except KeyError:
                        print("Data non-unique for timestamp", day, "and meter", meter)
                        print("Is site duplicated?")
                    # Last row is in the next day; pd[] includes start AND end. Remove end so it's not counted twice.
                    day_data = day_data.iloc[:-1]
                    day_row = {}
                    for column in day_data.columns:
                        if column in config.ENCRYPT_COLS and column in self.__data.columns:
                            # Load sensitive columns into a vector and encrypt it.
                            plaintext = day_data[column].tolist()
                            if self.__batch_size < len(plaintext):
                                self.__batch_size = len(plaintext)
                                self.__batch_size = self.__eval_batch_size()
                            elif len(plaintext) == 0:
                                plaintext = [0] * self.__batch_size
                            packed_plaintext = self.__cc.MakeCKKSPackedPlaintext(value=plaintext)
                            ciphertext = self.__cc.Encrypt(self.__shared_pubkey, packed_plaintext)
                            # Set length accordingly
                            self.vector_length = packed_plaintext.GetLength()
                            # Sum the encrypted vector.
                            # It needs to be done here, not later, so we have a coherent frame
                            # to make statistics.
                            day_row[column] = self.__cc.EvalSum(ciphertext, self.__batch_size)
                        else:
                            # Correct special cases
                            if column == "pf":
                                # TODO: recalculate it
                                day_row[column] = 0
                                pass
                                # day_row[column] = day_row["apparent_power"] / day_row["real_power"]
                            elif column == "point_id":
                                day_row[column] = meter_data[column].iloc[0]
                            elif column == "ee_site_id":
                                day_row[column] = self.__bid
                            else:
                                # We've aggregated encrypted columns; do the same for non-sensitive ones.
                                day_row[column] = day_data[column].sum()
                    try:
                        day_row["timestamp"] = day_data.index[0]
                    except:
                        day_row["timestamp"] = day
                    aggregate_day_frame = pd.DataFrame([day_row])
                    aggregate_day_frame = aggregate_day_frame.set_index(["timestamp"])
                    aggregate_days.append(aggregate_day_frame)
                # Finally, concatenate meters together
                for frame in aggregate_days:
                    if "final_frame" not in locals():
                        final_frame = frame
                    else:
                        final_frame = pd.concat([final_frame, frame])
            self.__data = final_frame
            return final_frame

        elif config.STAT_TEMPORAL_RESOLUTION == "f": # Encrypting each reading individually
            for meter in self.__ids:
                #meter_keys = self.__keypairs[meter]
                meter_data = self.__data[self.__data["point_id"] == meter]
                for column in meter_data.columns:
                    if column in config.ENCRYPT_COLS and column in self.__data.columns:
                        print("Encrypting", column)
                        if type(meter_data[column].iloc[0]) not in [Ciphertext, "object", object]: # Deals with duplicate sites
                            meter_data[column] = meter_data[column].apply(float) # Ensure data is compatible
                            meter_data[column] = meter_data[column].apply(encrypt_single_value, keys=self.__shared_pubkey)
                self.__data[self.__data["point_id"] == meter] = meter_data
        else:
            print("Resolution not yet supported.")

        return self.__data
   
    # Retrieves data for specified sites
    # database_path: path to SQLite database file
    # ids: list of point_ids to match
    # Start_date: if limiting date, the starting date to retrieve from
    # End_date: if limiting date, the last date to retrieve
    # Returns a pandas array of retrieved data
    # Staticmethod to allow usage when graphing aggregated building against
    # individual sites; no sense writing site querying twice when it's identical
    @staticmethod
    def query_for_sites(database_path, ids, start_date, end_date):
        UTC = ZoneInfo("UTC")
        with DBConn.create_connection(database_path) as conn:
            print("Connected to database.")
            # We only need to query each id once. Convert to set to get unique.
            print("Building IDs:", ids)
            unique_ids = tuple(set(ids))
            print("Unique IDs:", unique_ids)
            query = f"SELECT * FROM POWER WHERE point_id IN {unique_ids}"
            if start_date is not None and end_date is not None:
                # Convert provided times to unix timestamps to match database format
                start_date = datetime.strptime(start_date, '%Y-%m-%d').timestamp()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').timestamp()
                # Only retrieve values between the provided timestamps
                query = query + f" AND timestamp BETWEEN '{start_date}' AND '{end_date}';"
            else:
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
        UTC = ZoneInfo("UTC")
        # Explicit cast to UTC; it's already in UTC but this makes it aware
        def replace_timezone(x, **kwargs):
            for arg in kwargs:
                x = x.replace(tzinfo=kwargs[arg])
            return x
        # Make the conversion
        UTC = ZoneInfo("UTC")
        bdata['timestamp'] = pd.to_datetime(bdata['timestamp'],unit='s')
        bdata["timestamp"] = bdata["timestamp"].apply(replace_timezone, tz=UTC)
        return bdata

    # Run after functions that change power factor (sum functions); recalculates it to be correct
    def __correct_power_factor(self, building):
        # Fix the power factor
        building["pf"] = building["real_power"] / building["apparent_power"]
        return building
    
    # Translate from a numeric quality value to a human-readable string
    @staticmethod
    def quality_to_text(quality_value: int):
        reverse_quality = {0: "valid",
        8: "estimated_reference_day",
        9: "estimated_interpolation",
        10: "questionable",
        11: "derived",
        13: "mixed",
        14: "raw",
        15: "other"}
        return reverse_quality[int(quality_value)]
    
    # Impute missing data at the meter level pre-aggregation
    # target: the meter's data
    # outage_threshold: minimum # of meter readings to tolerate before considering it an outage / imputing 0s
    # Returns imputed frame
    # Staticmethod to allow imputation of queried sites when graphing sites against aggregated building
    @staticmethod
    def impute(
            target, # The frame to impute on
            outage_threshold: Optional[int] = 2 # Minimum # of missed consecutive readings to consider it an outage, not a meter failure
            ):
        print("Imputing missing data.")
        if target.empty:
            print("Cannot impute on an empty frame.")
            return target
        # Quality encodings- giving names for easier understanding
        quality = {"valid": 0,
        "estimated_reference_day": 8,
        "estimated_interpolation": 9,
        "questionable": 10,
        "derived": 11,
        "mixed": 13,
        "raw": 14,
        "other": 16}
        target["quality"] = quality["other"] # Default
        # Set up quality for existing rows not equalling NA
        # Default for rows with data- set as valid if not NA
        target["quality"] = target["quality"].where(target["real_power"].isna(), quality["valid"], axis=0)
        # We need to impute or zero any N/A PF values; many of these should be zero to begin with, but for those corresponding
        # to outages, it'll be recalculated after real and apparent power are imputed. We don't want the
        # should-be-zero PF values to be included when finding N/A rows.
        # Used to replace 0 values later- target should always have the same point_id, which is always
        # associated with the same ee_site_id
        ee_site_id = target["ee_site_id"].iloc[0]
        point_id = target["point_id"].iloc[0]
        # Explicit cast to UTC
        def replace_timezone(x, **kwargs):
            for arg in kwargs:
                x = x.replace(tzinfo=kwargs[arg])
            return x
        # Make the conversion
        UTC = ZoneInfo("UTC")
        target["timestamp"] = target["timestamp"].apply(replace_timezone, tz=UTC)
        # Fill in missing timestamps
        # timestamp should be index for this to work
        old_index = target["timestamp"].copy() # For comparison of imputation
        target = target.set_index("timestamp")
        start_datetime = target.index[0]
        end_datetime = target.index[-1] + pd.Timedelta(1, "d") # one day ahead for date_range to work properly
        fifteen_min_increments = pd.date_range(start=start_datetime, end=end_datetime, freq="15min", tz=UTC, normalize=True, inclusive="left")
        new_index = pd.Index(fifteen_min_increments, name="timestamp")
        target = target.reindex(index=new_index, method="nearest", limit=outage_threshold)
        target["duration"] = 15 # Mark the time interval of the fills
        target["raw_data_present"] = new_index.isin(old_index)
        # Mark that data was missing
        target["quality"] = target["quality"].where(target["real_power"].notna(), quality["questionable"], axis=0)
        # Find any remaining rows containing N/A that need more involved imputation
        # We can impute up to outage_threshold values forwards or backwards.
        # We then mark these as estimated in the quality column.
        # HOWEVER, caveat: if the gap happened because of daylight savings in the
        # original locality, we should NOT impute over it if possible.
        # Unfortunately, time was provided in UTC, meaning we don't know when DST
        # happened. This will need to be handled at timezone conversion instead.
        # Consider changing to limit_area="inside"?
        target["real_power"] = target["real_power"].interpolate(method="nearest", limit_area=None, limit=outage_threshold)
        target["apparent_power"] = target["apparent_power"].interpolate(method="nearest", limit_area=None, limit=outage_threshold)
        # Mark that data was interpolated where:
        # raw data present is false, and real_power has data (meaning we filled it in)
        target["quality"] = target["quality"].where(target["real_power"].isna() | target["raw_data_present"] == True, quality["estimated_interpolation"], axis=0)
        # Fix ID columns for added rows
        target["ee_site_id"] = ee_site_id
        target["point_id"] = point_id
        return target

    # Change an unencrypted frame's resolution to resolution using pd.resample()
    # Returns frame with new resolution
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

    # Aggregate sites into a building. For each timestamp, sum all values matching timestamp.
    # Place the results into their own row and adjust any fields accordingly.
    # Returns the resulting aggregated frame; see docs/documentation.md for columns and data types.
    def aggregate(self):
        # For each matching timestamp, sum values at all sites
        print("Aggregating.")
        # For each timestamp in the ids list, sum all values
        if self.__encryption_enabled == False:
            # Summing will break the quality column; we need to compute it separately
            # Save the columns for each building, then compare them-
            # Make a composite quality column.
            # If they're the same value, keep that value
            # If they're different, set to self.quality["mixed"]
            # We'll overlay this composite quality value with the final frame
            last_bquality = pd.Series() # Defined this way to allow checking if exists
            quality_col = pd.Series() # Same reason
            for bid in self.__ids:
                bquality = self.__data[self.__data["point_id"] == bid]["quality"]
                if not last_bquality.empty:
                    # Compare:
                    #quality_col = last_bquality
                    # Where they differ, set as "mixed"
                    diff = bquality.compare(last_bquality)
                    for timestamp in diff.index:
                        quality_col.loc[timestamp] = self.quality["mixed"]
                    # Where they are the same, keep the shared value
                    # TODO: this may not be fine-grained enough for large buildings
                else:
                    # Set up the column
                    quality_col = bquality
                # Enable the next loop with a new building
                last_bquality = bquality

            # Sum for each timestamp
            try:
                # Allows grouping
                aggregated_data = self.__data.copy()
                aggregated_data.reset_index(inplace=True)
                # Do the sum
                aggregated_data = aggregated_data.groupby(by="timestamp").sum(min_count=1)
                # Fix quality values using the column we computed earlier

                # Fix duration column
                aggregated_data["duration"] = 15
            except Exception as ex:
                print(f"Failed to aggregate: {ex}")
        else:
            # Aggregating encrypted data requires the use of EvalAdd
            aggregated_data = pd.DataFrame()
            for timestamp in pd.unique(self.__data.index): # For each matching timestamp
                # Collect all records matching the stamp in a frame
                interval_records = self.__data[self.__data.index == timestamp]
                # For each record in the timestamp...
                for record in range(0, interval_records["point_id"].size):
                    #...if the record is the first record in the set:
                    if record == 0:
                        # Counters equal the first record
                        duration_agg = interval_records["duration"].iloc[record]
                        real_power_agg = interval_records["real_power"].iloc[record]
                        apparent_power_agg = interval_records["apparent_power"].iloc[record]
                        power_factor_agg = interval_records["pf"].iloc[record]
                    # If this isn't the first record:
                    else:
                        # Add the record's data to the counters
                        real_power_agg = self.__cc.EvalAdd(real_power_agg, interval_records["real_power"].iloc[record])
                        #real_power_agg = self.__cc.EvalSum(real_power_agg, self.__batch_size)
                        duration_agg = interval_records["duration"].iloc[record]
                        if type(apparent_power_agg) == "object":
                            apparent_power_agg = self.__cc.EvalAdd(apparent_power_agg, interval_records["apparent_power"].iloc[record])
                            #apparent_power_agg = self.__cc.EvalSum(apparent_power_agg, self.__batch_size)
                        else:
                            apparent_power_agg += interval_records["apparent_power"].iloc[record]
                    # TODO Power factor needs to be recalculated here- rp / ap
                    # TODO build record for aggregated frame from this
                new_record = pd.DataFrame({"timestamp": interval_records.index[0], "point_id": 0, "ee_site_id": 0, "duration": duration_agg, \
                                           "real_power": real_power_agg, "apparent_power": apparent_power_agg, "pf": 0}, index=["timestamp"])
                aggregated_data = pd.concat([aggregated_data, new_record])
        # Set ID columns
        # point_id is repurposed to hold a tuple of point_ids in the building
        # ee_site_id is renamed to building_id and repurposed for that in case it winds up
        # in a frame with other buildings
        aggregated_data["point_id"] = str(self.__ids) # TODO: assign per row based on presence in aggregation?
        aggregated_data = aggregated_data.rename(columns={"ee_site_id": "building_id"}) 
        aggregated_data["building_id"] = self.__bid
        # Patch in the calculated quality value column
        aggregated_data["quality"] = quality_col
        #print(aggregated_data[aggregated_data["quality"] == 0])
        #print(aggregated_data[aggregated_data["real_power"].notna()])
        return aggregated_data
    
    # Save building to a pickle file for later use
    # Returns nothing
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

    # Get the building's data
    def get_data(self):
        return self.__data
    
    # Get the list of individual meter keys. TODO: Make "private" function?
    def get_keys(self):
        return self.__keypairs
    
    # Get the cryptocontext object. Needed for decryption.
    def get_cc(self):
        return self.__cc
    
    # Get the order that meters encrypt and decrypt in. Needed for decryption.
    def get_meter_order(self):
        return self.meter_order
    
    # Get the vector length. Needed for decryption.
    def get_length(self):
        return self.vector_length
    
    # Return the average of the real_power column for encrypted or unencrypted data.
    # Returns int (unencrypted), ciphertext (encrypted), or None (failure)
    def get_avg_real_power(self, day: datetime):
        # Get the date whose average is being asked for
        real_power = self.__data[day: (day + pd.Timedelta(1, "d"))]
        real_power = real_power["real_power"]
        if real_power.empty: # Nothing for supplied date
            print("Cannot calculate average on empty frame. Check date passed to get_avg_real_power().")
            return None
        if isinstance(real_power.iloc[0], float) or isinstance(real_power.iloc[0], int): # Value is not encrypted
            real_power = real_power.sum()
            return real_power / self.vector_length
        elif isinstance(real_power.iloc[0], object): # Value is encrypted
            # For a single reading
            real_power = real_power.iloc[0] # should only have one item inside
            return self.__cc.EvalMult(real_power, (1 / self.vector_length)) # real_power / vector_length
        else: # Type isn't practical for averaging
            print("Object type of real power not valid.")
            return None


if __name__ == "__main__":
    try:
        make_buildings(config.BUILDING_COUNT, encrypt=False, pickle=True, seed=config.SEED)
    except KeyboardInterrupt:
        print("Stopping (please wait).")