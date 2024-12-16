import pandas as pd
import pickle

import config
import tools.benchmark_encryption as benchmark
from list_files import list_files_in_dir
import dct.dct_main as dct_main

# Building module-related imports
import create_buildings as cb

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
        compare_encryption_times = False
        if compare_encryption_times == True:
            benchmark.benchmark_encryption()
        else:
            buildings = cb.make_buildings(config.BUILDING_COUNT, pickle=config.SAVE_AS_PICKLE, seed=config.SEED, encrypt=config.ENCRYPT)


    # Calculate DCT on data and perform any selected operations with it
    if config.PERFORM_DCT == True:
        dct_main.main()
    
    print("Done.\n========================================================")

# Thanks, multiprocessing
if __name__ == '__main__':
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