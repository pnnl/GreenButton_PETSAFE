import multiprocessing
import pandas as pd
import plotly.express as px
#from time import perf_counter

from dct import dct
import dct.dct_config as dctc
import dct.normalization as norm
import dct.fit_dct as fitdct
import dct.retrieve_and_analyze as dctra
from unpickle_buildings import unpickle_buildings, unpickle_resample_buildings

#from processor.commonDB import DBConn

def main():
        if dctc.AGGREGATE_BEFORE_DCT == True:
            buildings = unpickle_resample_buildings()
        else:
            buildings = unpickle_buildings()
        # Normalize the database to values between 0 and 1.
        if dctc.NORMALIZE == True:
            subdir = "normalized" # used to save coefficients to file
            buildings["real_power"] = norm.normalize(buildings["real_power"])
        else:
            subdir = "non-normalized"

        # DCT operations: calculating, zeroing coefficients, and recomposing afterwards
        # to get the data back into a usable form    
        for id in buildings["building_id"].unique():
            print("Performing DCT on building", id)
            this_building = buildings[buildings["building_id"] == id]
            #if config.FIT_DCT == True:
            #    method = config.METHOD
            #    best_fit = dct.fit_accuracy(this_building["real_power"], method)
            if dctc.STORE_DCT == False:
                dct_matrix = dct.decompose(this_building["real_power"])
                #dct_matrix = dct.drop_coefficients(dct_matrix)
                recomposed = dct.recompose(dct_matrix)
                print(dct_matrix)

                # Graph DCT values with original data to see visual changes
                if dctc.GRAPH_DCT == True:
                    dctra.graph_dct(recomposed, buildings)

            # For each building, calculate and save DCT values for each day of data
            elif dctc.FIT_DCT == False: # config.STORE_DCT != False
                fitdct.fit_dct(this_building, subdir)

        if dctc.RETRIEVE_DCT == True:
            dctra.retrieve_and_analyze()
            

# Thanks, multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping (please wait).")