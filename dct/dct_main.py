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
        all_building_coefficient_frames = []
        all_rmse = []
        for id in buildings["building_id"].unique():
            if dctc.PRINT_DEBUG == True:
                print("Performing DCT on building", id)
            # Get each building's data
            this_building = buildings[buildings["building_id"] == id]

            # X lines where X = number of days in building;
            # each line with ~96 points
            if dctc.GRAPH_BY_DAY == True or dctc.DCT_TARGET == "d":
                building_coefficients = perform_dct.dct_by_day(this_building, "real_power")
                building_coefficients.index.name = 'Coefficient'
                all_building_coefficient_frames.append(building_coefficients) # To allow concatenation into one plot later
                #graph_dct.graph_coefficients_as_scatter(building_coefficients, x_label="Coefficient", y_label="Value")
                #graph_dct.graph_coefficients_as_box(building_coefficients, title=f"Building {id} Coefficient Magnitudes", transpose=True)
                if dctc.MAKE_DCT_AVG_CURVE == True:
                    # Calculate the coefficients for one day, averaged for the year
                    building_coefficients = building_coefficients.transpose()
                    days_in_year = building_coefficients[0].size
                    avg = building_coefficients.sum() / days_in_year # Sums all 365 days of coefficients by rows, aka per coefficient
                    if "avg_coefficients" not in locals(): # Make the initial frame
                        avg_coefficients = avg
                        dct_count = 1
                    else: # Add the building to the frame
                        avg_coefficients += avg
                        dct_count += 1

            else:
                # Perform DCT on however much data is present, decomposing into coefficients
                dct_coefficients = perform_dct.decompose(this_building["real_power"])

                if dctc.DROP_COEFFICIENTS == True: # Reduce number of non-zero coefficients
                    dct_coefficients = perform_dct.drop_coefficients(dct_coefficients)
                    # Recreate data from coefficients to detect any accuracy loss
                    recomposed = perform_dct.recompose(dct_coefficients)

                # For each building, save DCT coefficients to file
                elif dctc.STORE_DCT == True:
                    perform_dct.save_to_file(this_building, id, save_to)
            
            # Average coefficients for all buildings
            if dctc.MAKE_DCT_AVG_CURVE == True:
                if dctc.PRINT_DEBUG == True:
                    print("Averaging building", id)
                fig, avg_frame = dctra.make_average_dct_curve(this_building, id, dct_count, avg_coefficients)
                if dctc.DCT_AVG_DP == True:
                    rmse = dctra.DCT_with_DP(avg_frame, "Averaged DCT", id, percent_to_drop=dctc.HIGH_THRESHOLD, keep_highest=dctc.NUMBER_OF_LARGEST)
                    average_rmse = 0
                    for day in rmse:
                        average_rmse += rmse[day]
                    average_rmse = average_rmse / len(rmse)
                    if dctc.PRINT_DEBUG == True:
                        print(f"Average RMSE for building {id}, drop {dctc.HIGH_THRESHOLD * 100}%: {average_rmse}")
                    all_rmse.append(average_rmse)

                # Stop early to prevent graph spam if we only want to look at building 0 for testing purposes
                # (Remember to test all to ensure building bias doesn't wind up ingrained into structure!)
                one_building_only = False
                if one_building_only == True:
                    raise SystemExit

        if dctc.DCT_AVG_DP == True:
            all_buildings_rmse_average = 0
            for rmse in all_rmse:
                all_buildings_rmse_average += rmse
            all_buildings_rmse_average = all_buildings_rmse_average / len(all_rmse)
            print(f"RMSE average for drop {dctc.HIGH_THRESHOLD * 100}%: {all_buildings_rmse_average}")

        if dctc.GRAPH_BY_DAY == True:
            graph_dct.graph_coefficients_as_box_all_buildings(all_building_coefficient_frames,
                                                              title=f"Coefficient Magnitudes by Building",
                                                              transpose=True)

    # Instead of calculating coefficients, retrieve existing coefficients saved previously
    if dctc.RETRIEVE_DCT == True:
        dctra.retrieve_and_analyze()

    # Graph DCT coefficients...
    if dctc.GRAPH_DCT == True:
        # TODO: can we combine or shorten these into one function call or a case/switch?
        if dctc.GRAPH_AS_HIST == True: # ...as a histogram
            graph_dct.graph_coefficients_as_hist(dct_coefficients)
        elif dctc.GRAPH_AS_SCATTER == True: # ...as a scatter plot
            graph_dct.graph_coefficients_as_scatter(dct_coefficients)
        elif dctc.GRAPH_AS_BOX == True: # ...as a scatter plot
            graph_dct.graph_coefficients_as_box(dct_coefficients)
        elif dctc.GRAPH_DATA_AGAINST_RECOMPOSED == True: # ...recomposed, alongside original data
            graph_dct.graph_recomposed_against_real(recomposed, buildings)
        else: # ...but we don't know how to graph them
            print("No graphing method specified.")
            

# Thanks, multiprocessing
if __name__ == '__main__':
    # Yes, this should go in main(). Yes, I intend to rework it eventually to make that happen. TODO.
    print(f"Time resolution for DCT averaging: {dctc.START_DATE} to {dctc.END_DATE}")
    try: # Test threshold values of interest without having to enter them all by hand
        #for threshold in [0.25, 0.5, 0.65, 0.7, 0.75, 0.9]: # 0.25, 0.5, 0.75, 0.9, 0.95, 0.98]:
        #    dctc.HIGH_THRESHOLD = threshold
        #    for keep_largest in [1, 2, 5, 10]:
        #        dctc.NUMBER_OF_LARGEST = keep_largest
                main()
    except KeyboardInterrupt:
        print("Stopping (please wait).")