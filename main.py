import multiprocessing
import pandas as pd
import plotly.express as px
import pickle

import config
import dct
from list_files import list_files_in_dir

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

def unpickle_buildings():
    if config.OUTPUT_DIR[-1] != "/":
        config.OUTPUT_DIR += "/"
    filepath = config.OUTPUT_DIR + "buildings/"
    buildings_frame = pd.DataFrame()
    # Get all buildings from files and place in one big frame for processing
    try:
        for file in list_files_in_dir(filepath, append_path=True):
            with open(file, "rb") as file:
                building= pickle.load(file)
            buildings_frame = pd.concat((buildings_frame, building))
        return buildings_frame
    except Exception as ex:
        print("Could not unpickle buildings:", ex)
        raise SystemExit # For now

def main():
    TEST_QUERY = False
    # Test query, about 75sec
    if TEST_QUERY == True:
        print("Testing query (may take a while)")
        with DBConn.create_connection(config.DATABASE) as conn:
            #columns = ['ee_site_id', 'point_id', 'timestamp', 'duration', 'real_power', 'apparent_power', 'pf']
            columns = ['timestamp']
            query = "SELECT * FROM POWER WHERE ee_site_id=491 AND timestamp=1585155600"
            query = "SELECT timestamp FROM POWER"
            results = conn.execute(query)
            data = results.fetchall()
            data = pd.DataFrame.from_records(data=data, columns=columns)
        print(data)
        print("Query testing done.")

    if config.READ_FILES == True:
        populate_database()
    
    if config.CREATE_BUILDINGS == True:
        cb.make_buildings(config.BUILDING_COUNT, pickle=True)

    if config.DCT == True:
        buildings = unpickle_buildings()
        for id in buildings["building_id"].unique():
            this_building = buildings[buildings["building_id"] == id]
            dct_matrix = dct.decompose(this_building["real_power"])
            dct_matrix = dct.drop_coefficients(dct_matrix)
            recomposed = dct.recompose(dct_matrix)

            if config.GRAPH_DCT == True:
                graphframe = pd.DataFrame()
                graphframe = pd.concat((graphframe, pd.Series(data=recomposed)))
                graphframe = graphframe.rename(columns={0: "recomposed"})
                graphframe = pd.concat((graphframe, buildings["real_power"].reset_index()), axis=1)
                graphframe = graphframe.set_index("timestamp")
                #print(graphframe)
                fig = px.line(graphframe)
                fig.update_traces(opacity=0.75)
                fig.data[0].line.color = "#A9A9A9"
                fig.show()

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