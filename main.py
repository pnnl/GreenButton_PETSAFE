import multiprocessing
import pandas as pd
import plotly.express as px
import pickle
import numpy as np
from os.path import exists
from os import makedirs

import config
import dct
import normalization as norm
from list_files import list_files_in_dir

# Building module-related imports
from virtual_buildings import create_buildings as cb
from building_analysis.reader import Reader
#from building_analysis.decryptor import Decryptor
from processor.commonDB import DBConn

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
                building= pickle.load(file)
            buildings_frame = pd.concat((buildings_frame, building))
            #dates = np.unique(buildings_frame.index.date) # timestamp is index
            #print("Buildings frame:", dates, "\n=========")
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
        cb.make_buildings(config.BUILDING_COUNT, pickle=True, seed=config.SEED)

    # Calculate DCT on data and perform any selected operations with it
    if config.PERFORM_DCT == True:
        buildings = unpickle_buildings()
        #print(buildings[buildings["real_power"] > 0])
        # Normalize the database to values between 0 and 1.
        if config.NORMALIZE == True:
            subdir = "normalized" # used to save coefficients to file
            buildings["real_power"] = norm.normalize(buildings["real_power"])
            #print(buildings["real_power"])
        else:
            subdir = "non-normalized"

        # DCT operations: calculating, zeroing coefficients, and recomposing afterwards
        # to get the data back into a usable form    
        for id in buildings["building_id"].unique():
            print("Performing DCT on building", id)
            this_building = buildings[buildings["building_id"] == id]
            if config.FIT_DCT == True:
                method = config.METHOD
                best_fit = dct.fit_accuracy(this_building["real_power"], method)
            if config.STORE_DCT == False:
                dct_matrix = dct.decompose(this_building["real_power"])
                dct_matrix = dct.drop_coefficients(dct_matrix)
                recomposed = dct.recompose(dct_matrix)
                print(dct_matrix)

                # Graph DCT values with original data to see visual changes
                if config.GRAPH_DCT == True:
                    import matplotlib as mpl
                    print("Preparing graph for building", id)
                    graphframe = pd.DataFrame()
                    graphframe = pd.concat((graphframe, pd.Series(data=recomposed)))
                    graphframe = graphframe.rename(columns={0: "recomposed"})
                    graphframe = pd.concat((graphframe, buildings["real_power"].reset_index()), axis=1)
                    graphframe = graphframe.set_index("timestamp")
                    #print(graphframe)
                    fig = px.line(graphframe)
                    fig.update_traces(opacity=0.75)
                    fig.data[0].line.color = "red"
                    fig.data[1].line.color = "#A9A9A9"
                    print("Showing graph in web browser")
                    fig.show()

            # For each building, calculate and save DCT values for each day of data
            elif config.FIT_DCT == False: # config.STORE_DCT != False
                dates = np.unique(this_building.index.date) # timestamp is index
                coefficients = np.empty(0, dtype=np.float64)
                for day in dates:
                    # Get the day of data and do DCT on it
                    day_data = this_building[this_building.index.date == day]
                    day_dct_matrix = dct.decompose(day_data["real_power"], log=False)
                    if config.HIGH_ONLY == True:
                        drop_index = int(config.HIGH_THRESHOLD * day_dct_matrix.size)
                        day_dct_matrix = day_dct_matrix[drop_index:]
                    #day_dct_matrix = dct.drop_coefficients(day_dct_matrix)
                    # TODO: consider nesting as 2D array instead to preserve daily association
                    coefficients = np.concatenate((coefficients, day_dct_matrix))

                filename = "Building-" + str(this_building["building_id"].iloc[0]) + "-coefficients.pkl"
                print("Saving DCT coefficients to pickle file at", filename)
                # Set directory path of output- output directory in config + "buildings" subdirectory
                dirpath = config.OUTPUT_DIR + "/coefficients/"
                if config.HIGH_ONLY == True:
                    dirpath = dirpath + "/top-" + str(config.HIGH_THRESHOLD) + "/"
                dirpath = dirpath + subdir + "/"
                if not exists(dirpath):
                    makedirs(dirpath)
                # Save as file to output dir
                with open(dirpath + filename, "wb") as outfile:
                    pickle.dump(coefficients, outfile)

    if config.RETRIEVE_DCT == True:
            if config.OUTPUT_DIR[-1] != "/":
                config.OUTPUT_DIR += "/"
            filepath = config.OUTPUT_DIR + "coefficients/"
            if config.HIGH_ONLY == True:
                filepath = filepath + "top-" + str(config.HIGH_THRESHOLD) + "/"
            if config.NORMALIZE == True: # TODO: separate switch for reading vs writing normalized data?
                filepath = filepath + "normalized/"
            else:
                filepath = filepath + "non-normalized/"
            print(filepath)
            coefficients = np.empty(0, dtype=np.float64)
            try:
                for file in list_files_in_dir(filepath, append_path=True):
                    with open(file, "rb") as file:
                        building_coefficients = pickle.load(file)
                    coefficients = np.append(coefficients, building_coefficients)
            except Exception as ex:
                print("Could not unpickle building coefficients:", ex)
                raise SystemExit # For now
            
            if config.ANALYZE_DCT == True:
                dct.analyze(coefficients)
                

    if config.CREATE_STATISTICS == True:
        reader = Reader(config.START_DATE, config.END_DATE, resolution=config.STAT_TEMPORAL_RESOLUTION)
        data = reader.get_data()
        building_ids = reader.get_building_ids()
        #building_id = 2
        for building_id in building_ids:
            power_sum_building = reader.get_building_power_sum(building_id)
            power_avg_building = reader.get_building_power_avg(building_id)
            print("__________")
            print("Site IDs for building", building_id, ":", reader.get_building_site_ids(building_id))
            print("Total power demand of building", building_id, "between", config.START_DATE, "and", config.END_DATE, ":", power_sum_building, "kW")
            print("Power demand average of building", building_id, "between", config.START_DATE, "and", config.END_DATE, ":", power_avg_building, "kW")
            # TODO: graph looks weird if resolution = time range provided (eg. day resolution and single day for date range)
            #fig = reader.graph_building_power(building_id, config.STAT_TEMPORAL_RESOLUTION, show_graph=True)
        #fig = reader.graph_building_power(1, config.STAT_TEMPORAL_RESOLUTION, show_graph=True)
    
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