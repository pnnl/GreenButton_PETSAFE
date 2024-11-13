import multiprocessing
import pandas as pd
import pickle
from time import perf_counter
from sklearn.metrics import mean_squared_error

import config
from list_files import list_files_in_dir
import dct.dct_main as dct_main

# Building module-related imports
import create_buildings as cb
from building_analysis.reader import Reader
from building_analysis.decryptor import Decryptor

def populate_database():
    import processor.populateRecords as popdb
    print("Creating database...")
    popdb.loadDataLabels(config.DATABASE)
    popdb.populateAll()
    print("Records created.")

def unpickle_buildings():
    if config.OUTPUT_DIR[-1] != "/":
        config.OUTPUT_DIR += "/"
    filepath = config.OUTPUT_DIR + "buildings/"
    buildings_frame = pd.DataFrame()
    # Get all buildings from files and place in one big frame for processing
    try:
        for file in list_files_in_dir(filepath, append_path=True):
            #print("Reading", file)
            with open(file, "rb") as file:
                building = pickle.load(file)
            buildings_frame = pd.concat((buildings_frame, building))
        return buildings_frame
    except Exception as ex:
        print("Could not unpickle buildings:", ex)
        raise SystemExit # For now

def main():
    # Create the database. Required for any other operations.
    if config.READ_FILES == True:
        populate_database()
    
    # Create buildings from the data. 
    # Optionally, save them to a pickle file in OUTPUT_DIR/buildings/
    if config.CREATE_BUILDINGS == True:
        # Make buildings; both encrypted and decrypted
        # Temp: TODO save this to file instead. this works for now.
        # Current barrier to file saving is pickle's refusal to work with openfhe objects, including keypairs,
        # but no clear methods to save keys and cc obj to file in documentation.
        timer_start = perf_counter()
        buildings = cb.make_buildings(config.BUILDING_COUNT, pickle=False, seed=config.SEED, encrypt=False)
        timer_end = perf_counter()
        plaintext_processing_time = timer_end - timer_start

        timer_start = perf_counter()
        encrypted_buildings = cb.make_buildings(config.BUILDING_COUNT, pickle=False, seed=config.SEED, encrypt=True)
        timer_end = perf_counter()
        enc_processing_time = timer_end - timer_start

        # Basic stats on both sets of buildings, calculate the relative error between them
        plaintext_sums = []
        enc_sums = []
        plaintext_avgs = []
        enc_avgs = []
        b_id = 0 # Used to match encrypted to plaintext buildings by id
        for enc_building in encrypted_buildings:
            cc = enc_building.get_cc()
            keys = enc_building.get_keys()
            order = enc_building.get_meter_order()
            length = enc_building.get_length()

            # Get the encrypted data
            enc_data = enc_building.get_data()
            # Get the plaintext data
            plaintext_reader = Reader(resolution=config.STAT_TEMPORAL_RESOLUTION, building=buildings[b_id])

            # Calculate statistics for each time interval (sum, avg, etc.)
            for timestamp in plaintext_reader.get_data().index:
                # Get data for interval

                # Sums
                timer_start = perf_counter()
                enc_power_sum = enc_data["real_power"].loc[enc_data.index == timestamp].iloc[0] # encrypted
                timer_end = perf_counter()
                enc_processing_time += timer_end - timer_start

                timer_start = perf_counter()
                plaintext_sum = plaintext_reader.get_data()["real_power"].loc[enc_data.index == timestamp].iloc[0]
                timer_end = perf_counter()
                plaintext_processing_time += timer_end - timer_start
                plaintext_sums.append(plaintext_sum)

                # Averages
                timer_start = perf_counter()
                enc_power_avg = enc_building.get_avg_real_power(timestamp)
                timer_end = perf_counter()
                enc_processing_time += timer_end - timer_start

                timer_start = perf_counter()
                plaintext_power_avg = buildings[b_id].get_avg_real_power(timestamp)
                plaintext_avgs.append(plaintext_power_avg)
                timer_end = perf_counter()
                plaintext_processing_time += timer_end - timer_start

                # Decrypt
                start_time = perf_counter()
                decryptor = Decryptor(keys=keys, cc=cc, order=order, length=length)
                print("Decrypting statistics.")
                dec_power_sum = decryptor.decrypt_target(enc_power_sum)
                enc_sums.append(dec_power_sum)
                print("Decrypted sum.")
                end_time = perf_counter()
                time_taken = end_time - start_time
                enc_processing_time += time_taken
                dec_power_avg = decryptor.decrypt_target(enc_power_avg)
                enc_avgs.append(dec_power_avg)

                print("---------")
                #print("Building", enc_data["building_id"].iloc[0])
                #print("Timestamp:", timestamp)
                #print("Actual Sum:", plaintext_sum)
                #print("Homomorphic Sum:", dec_power_sum)
                #print("Actual Avg:", plaintext_power_avg)
                #print("Homomorphic Avg:", dec_power_avg)
                #print("Time to decrypt:", time_taken, "seconds")
                #print("---------")

            b_id += 1
            avg_plaintext_time = plaintext_processing_time / config.BUILDING_COUNT
            print("Avg time to process encrypted buildings:", enc_processing_time / config.BUILDING_COUNT, "seconds")
            print("Avg time to process plaintext buildings:", avg_plaintext_time, "seconds")
            print("Sums RMSE:", mean_squared_error(plaintext_sums, enc_sums))

            print("Avgs RMSE:", mean_squared_error(plaintext_avgs, enc_avgs))




    # Calculate DCT on data and perform any selected operations with it
    if config.PERFORM_DCT == True:
        dct_main.main()
    
    print("Done.\n========================================================")

# Thanks, multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping (please wait).")

    """
        # Decryption testing
        try:
            test_value = data["power"].iloc[0]
            if config.DECRYPT == True:
                decryptor = Decryptor()
                test_value = decryptor.decrypt_target(test_value)
                print("Decrypted first value:", test_value)
        except Exception as error:
            print("Unable to retrieve values:", error)
    """