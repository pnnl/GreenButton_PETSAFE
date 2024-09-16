import multiprocessing
import pandas as pd

import config
import dct

# Building module-related imports
from virtual_buildings import create_buildings as cb
#from building_analysis.reader import Reader
#from building_analysis.decryptor import Decryptor
from processor.commonDB import DBConn

# Output directory for prepped data
OUTPUT_DIR = "./output/"

def populate_database():
    import processor.populateRecords as popdb
    print("Creating database...")
    popdb.loadDataLabels(config.DATABASE)
    popdb.populateAll()
    print("Records created.")

def main():
    TEST_QUERY = False
    # Test query, about 75sec
    if TEST_QUERY == True:
        with DBConn.create_connection(config.DATABASE) as conn:
            columns = ['ee_site_id', 'point_id', 'timestamp', 'duration', 'real_power', 'apparent_power', 'pf']
            query = "SELECT * FROM POWER WHERE ee_site_id=491 AND timestamp=1585155600"
            results = conn.execute(query)
            data = results.fetchall()
            data = pd.DataFrame.from_records(data=data, columns=columns)
        print(data)

    if config.READ_FILES == True:
        populate_database()
    
    if config.CREATE_BUILDINGS == True:
        cb.make_buildings(config.BUILDING_COUNT, pickle=True)

    if config.DCT == True:
        pass

    if config.CREATE_STATISTICS == True:
        raise NotImplemented

# Thanks, multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping.")

    """
    if config.CREATE_STATISTICS == True:
        # TODO: read from pickle if available
        reader = Reader(config.START_DATE, config.END_DATE, resolution=config.STAT_TEMPORAL_RESOLUTION)
        data = reader.get_data()
        ids = reader.get_ids()
        #building_id = 2
        for building_id in ids:
            power_sum_building = reader.get_building_power_sum(building_id)
            power_avg_building = reader.get_building_power_avg(building_id)
            print("__________")
            print("Total power demand of building", building_id, "between", config.START_DATE, "and", config.END_DATE, ":", power_sum_building, "kW")
            print("Power demand average of building", building_id, "between", config.START_DATE, "and", config.END_DATE, ":", power_avg_building, "kW")
            # TODO: graph looks weird if resolution = time range provided (eg. day resolution and single day for date range)
            fig = reader.graph_building_power(building_id, config.STAT_TEMPORAL_RESOLUTION, show_graph=True)
        #fig = reader.graph_building_power(1, config.STAT_TEMPORAL_RESOLUTION, show_graph=True)

        # Decryption testing
        try:
            test_value = data["power"].iloc[0]
            if config.DECRYPT == True:
                decryptor = Decryptor()
                test_value = decryptor.decrypt_target(test_value)
                print("Decrypted first value:", test_value)
        except Exception as error:
            print("Unable to retrieve values:", error)

def unpickle_data():
    if config.OUTPUT_DIR[-1] != "/":
        config.OUTPUT_DIR += "/"
    filename = config.OUTPUT_DIR + config.YEAR + "-" + config.STAT_TEMPORAL_RESOLUTION
    with open(filename, "rb") as file:
        return pickle.load(file)
    """