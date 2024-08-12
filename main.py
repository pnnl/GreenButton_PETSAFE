import multiprocessing
from math import floor
from sys import exit

import config
from list_files import list_files_in_dir

# Building module-related imports
from virtual_buildings import meterdata as md
from building_analysis.reader import Reader
from building_analysis.decryptor import Decryptor

# Output directory for prepped data
OUTPUT_DIR = "./output/"

def process_file(file):
    file = config.POWER_DIR + file
    try:
        parser = md.MeterDataParser(file, building_size=8, seed=config.SEED, encrypt=config.ENCRYPT)
    except KeyboardInterrupt:
        print("Stopping.")
        exit()
    try:
        parser.output_to_file(config.OUTPUT_DIR)
        print(file, "done.")
    except Exception as error:
        print("Could not output files:", error)

def main():
    if config.PREP_FILES == True:
        files = list_files_in_dir(config.POWER_DIR, False)
        # Only use multiprocessing if we're not going to need multiprocessing for
        # encryption- would use too many cores otherwise
        if config.ENCRYPT == False:
            processors = multiprocessing.cpu_count()
            processors = floor(processors / 2)
            results = []
            with multiprocessing.Pool(processes=processors) as pool:
                for result in pool.map(process_file, files):
                    results.append(result)
        else:
            for file in files:
                process_file(file)

    if config.CREATE_STATISTICS == True:
        reader = Reader(config.START_DATE, config.END_DATE)
        data = reader.get_data()
        power_sum_building_1 = reader.get_building_power_sum(1)
        power_avg_building_1 = reader.get_building_power_avg(1)
        print("Total power demand of building 1 between", config.START_DATE, "and", config.END_DATE, ":", power_sum_building_1, "kW")
        print("Power demand average of building 1 for temporal resolution in config:", power_avg_building_1, "kW")
        reader.graph_building_power(1)
        print("Graph output.")

        # Decryption testing
        try:
            test_value = data["power"].iloc[0]
            if config.DECRYPT == True:
                decryptor = Decryptor()
                test_value = decryptor.decrypt_target(test_value)
                print("Decrypted first value:", test_value)
            else:
                print("First value:", test_value)
        except Exception as error:
            print("Unable to retrieve values:", error)
    
# Thanks, multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped.")