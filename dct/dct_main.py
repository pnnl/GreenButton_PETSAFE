import multiprocessing

from dct import perform_dct
from dct import graph_dct
import dct.dct_config as dctc
import dct.normalization as norm
import dct.retrieve_and_analyze as dctra
from dct.unpickle_buildings import unpickle_buildings, unpickle_resample_buildings

def main():
    if dctc.PERFORM_DCT == True: # Calculate DCT coefficients
        # Retrieve building data
        if dctc.RESAMPLE_BEFORE_DCT == True:
            # Unpickle buildings and resample to desired resolution
            buildings = unpickle_resample_buildings(dctc.BUILDING_DIRECTORY)
        else:
            # Just unpickle at saved resolution
            buildings = unpickle_buildings(dctc.BUILDING_DIRECTORY)

        if dctc.NORMALIZE == True: # Normalize the data to values between 0 and 1.
            buildings["real_power"] = norm.normalize(buildings["real_power"])
            save_to = "normalized" # used to save coefficients to file
        else:
            save_to = "non-normalized"

        # DCT operations: calculating, zeroing coefficients, and recomposing afterwards
        # to get the data back into a usable form  
        for id in buildings["building_id"].unique():
            print("Performing DCT on building", id)
            # Get each building's data
            this_building = buildings[buildings["building_id"] == id]
            # Perform DCT, decomposing into coefficients
            dct_coefficients = perform_dct.decompose(this_building["real_power"])

            if dctc.DROP_COEFFICIENTS == True: # Reduce number of non-zero coefficients
                dct_coefficients = perform_dct.drop_coefficients(dct_coefficients)
                # Recreate data from coefficients to detect any accuracy loss
                recomposed = perform_dct.recompose(dct_coefficients)

            # For each building, save DCT coefficients to file
            elif dctc.STORE_DCT == True:
                perform_dct.save_to_file(this_building, id, save_to)

    # Instead of calculating coefficients, retrieve existing coefficients saved previously
    if dctc.RETRIEVE_DCT == True:
        dctra.retrieve_and_analyze()

    # Graph DCT coefficients...
    if dctc.GRAPH_DCT == True:
        if dctc.GRAPH_AS_HIST == True: # ...as a histogram
            graph_dct.graph_coefficients_as_hist(dct_coefficients)
        elif dctc.GRAPH_AS_SCATTER == True: # ...as a scatter plot
            graph_dct.graph_coefficients_as_scatter(dct_coefficients)
        elif dctc.GRAPH_DATA_AGAINST_RECOMPOSED == True: # ...recomposed, alongside original data
            graph_dct.graph_recomposed_against_real(recomposed, buildings)
        else: # ...but we don't know how to graph them
            print("No graphing method specified.")
            

# Thanks, multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping (please wait).")