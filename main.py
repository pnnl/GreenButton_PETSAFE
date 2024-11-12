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
        buildings = cb.make_buildings(config.BUILDING_COUNT, pickle=False, seed=config.SEED, encrypt=False)
        encrypted_buildings = cb.make_buildings(config.BUILDING_COUNT, pickle=False, seed=config.SEED, encrypt=True)

        # Basic stats on both sets of buildings, calculate the relative error between them
        decrypt_times = []
        plaintext_sums = []
        enc_sums = []
        b_id = 0 # Used to match encrypted to plaintext buildings by id
        rounds = 0 # Used to average time overhead
        for building in encrypted_buildings:
            cc = building.get_cc()
            keys = building.get_keys()
            order = building.get_meter_order()
            length = building.get_length()

            # Get the encrypted data
            enc_data = building.get_data()
            enc_data = enc_data.set_index(["timestamp"])
            # Get the plaintext data
            plaintext_reader = Reader(resolution=config.STAT_TEMPORAL_RESOLUTION, building=buildings[b_id])

            # Calculate statistics for each time interval (sum, avg, etc.)
            for timestamp in plaintext_reader.get_data().index:
                # Get data for interval
                enc_power_sum_building = enc_data["real_power"].loc[enc_data.index == timestamp].iloc[0] # encrypted
                plaintext_sum = plaintext_reader.get_data()["real_power"].loc[enc_data.index == timestamp].iloc[0]
                plaintext_sums.append(plaintext_sum)

                # Decrypt
                start_time = perf_counter()
                decryptor = Decryptor(keys=keys, cc=cc, order=order, length=length)
                print("Decrypting statistics.")
                dec_power_sum_building = decryptor.decrypt_target(enc_power_sum_building)
                enc_sums.append(dec_power_sum_building)
                print("Decrypted sum.")
                end_time = perf_counter()

                print("---------")
                print("Building", enc_data["building_id"].iloc[0])
                print("Timestamp:", timestamp)
                print("Actual:", plaintext_sum)
                print("Decrypted:", dec_power_sum_building)
                time_taken = end_time - start_time
                decrypt_times.append(time_taken)
                print("Time to decrypt:", time_taken, "seconds")
                print("---------")
                rounds += 1

            b_id += 1
            print("Average time for decryption:", sum(decrypt_times) / rounds, "seconds")
            print("RMSE:", mean_squared_error(plaintext_sums, enc_sums))




    # Calculate DCT on data and perform any selected operations with it
    if config.PERFORM_DCT == True:
        dct_main.main()

    if config.CREATE_STATISTICS == True:
        if config.DECRYPT == True:
            reader = Reader(config.START_DATE, config.END_DATE, resolution=config.STAT_TEMPORAL_RESOLUTION, read_dir=config.OUTPUT_DIR + "encrypted-buildings/")
        else:
            reader = Reader(config.START_DATE, config.END_DATE, resolution=config.STAT_TEMPORAL_RESOLUTION)
        data = reader.get_data()
        building_ids = reader.get_building_ids()
        #building_id = 2
        building_rmses = []
        for building_id in building_ids:
            print("Calculating statistics.")
            power_sum_building = reader.get_building_power_sum(building_id)
            power_avg_building = reader.get_building_power_avg(building_id)
            
            RMSE = True
            if RMSE == True:
                building_with_sites = reader.get_building_with_sites(building_id, "15min")
                # Transform into the average for comparison
                building_with_sites["Building Aggregate"] = building_with_sites["Building Aggregate"]
                for column in building_with_sites.columns:
                    if column != "Building Aggregate":
                        building_with_sites[column] = building_with_sites["Building Aggregate"] - building_with_sites[column]
                        numerator = building_with_sites[column].sum()
                        sample_size = building_with_sites[column].size
                        site_rmse = numerator / (sample_size - 1)
                        building_rmses.append(site_rmse)

            if config.DECRYPT == True:
                start_time = perf_counter()
                decryptor = Decryptor()
                print("Decrypting statistics.")
                power_sum_building = decryptor.decrypt_target(power_sum_building)
                print("Decrypted sum.")
                power_avg_building = decryptor.decrypt_target(power_avg_building)
                print("Decrypted average.")
                end_time = perf_counter()
                print("Time to decrypt:", end_time - start_time, "seconds")

            # Round for legibility
            power_sum_building = round(power_sum_building, 4)
            power_avg_building = round(power_avg_building, 4)
            print("__________")
            print("Site IDs for building", building_id, ":", reader.get_building_site_ids(building_id))
            print("Total power demand of building", building_id, "between", config.START_DATE, "and", config.END_DATE, ":", power_sum_building, "kW")
            print("Power demand average of building", building_id, "between", config.START_DATE, "and", config.END_DATE, ":", power_avg_building, "kW")
            # TODO: graph looks weird if resolution = time range provided (eg. day resolution and single day for date range)
        if config.DECRYPT == False: # Graphing encrypted not implemented; need to decrypt first for that
            #fig = reader.graph_building_power(building_id, config.STAT_TEMPORAL_RESOLUTION, show_graph=True)
            fig = reader.graph_building_power_with_sites(7, config.STAT_TEMPORAL_RESOLUTION, show_graph=True)
            pass
        if RMSE == True:
            rmse_series = pd.Series(building_rmses)
            rmse_average = rmse_series.sum() / rmse_series.size
            rmse_min = rmse_series.min()
            rmse_worst = rmse_series[rmse_series == rmse_series.abs().max()].max()
            print("RMSE min:", rmse_min)
            print("RMSE average:", rmse_average)
            print("RMSE worst:", rmse_worst)
    
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