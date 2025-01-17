from dct import perform_dct
from dct import graph_dct
import dct.dct_config as dctc
import dct.normalization as norm
import dct.retrieve_and_analyze as dctra
from dct.unpickle_buildings import unpickle_buildings, unpickle_resample_buildings

import pandas as pd

def main():
    # -------- PREP FOR DCT ----------
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

        # Will be used to hold multi-building data for later use
        all_building_coefficient_frames = []
        if dctc.CALC_RMSE == True:
            all_rmse = [] # root mean square error

        # -------- PERFORM DCT ----------
        # For each building, perform DCT individually
        for id in buildings["building_id"].unique():
            if dctc.PRINT_DEBUG == True:
                print("Performing DCT on building", id)
            # Get each building's data
            this_building = buildings[buildings["building_id"] == id]

            # X lines where X = number of days in building;
            # each line with ~96 points
            if dctc.DCT_ACTION in ["average", "mod average", "magnitude"]:
                building_coefficients = perform_dct.dct_by_day(this_building, "real_power")
                building_coefficients.index.name = 'Coefficient'
                all_building_coefficient_frames.append(building_coefficients) # To allow concatenation into one plot later

                if dctc.DCT_ACTION != "magnitude": # Find the average DCT coefficients from those daily coefficients
                    # Prep formatting to make this simpler
                    building_coefficients = building_coefficients.transpose()
                    days_in_sample = building_coefficients[0].size
                    # Calculate the coefficients for one day, averaged for the time period
                    avg = building_coefficients.sum() / days_in_sample # Sums by rows, aka per coefficient
                    if "avg_coefficients" not in locals(): # Make the initial frame
                        avg_coefficients = avg
                        dct_count = 1
                    else: # Add the building to the frame
                        avg_coefficients += avg
                        dct_count += 1

            else:
                # Cut data down to desired time period
                this_building = this_building[dctc.START_DATE:dctc.END_DATE]
                building_id = this_building["building_id"].iloc[0]
                # Perform DCT on however much data is present, decomposing into coefficients
                dct_coefficients = perform_dct.decompose(this_building["real_power"])

                if dctc.DROP_COEFFICIENTS == True: # Reduce some coefficients to 0
                    dct_coefficients = perform_dct.drop_coefficients(dct_coefficients)

                # Recreate data from coefficients to detect any accuracy loss
                recomposed = perform_dct.recompose(dct_coefficients)

                # For each building, save DCT coefficients to file
                if dctc.STORE_DCT == True:
                    perform_dct.save_to_file(this_building, id, save_to)
            
            # -------- PROCESS DCT ----------
            # Average coefficients for all buildings
            if dctc.DCT_ACTION in ["average", "mod average"]:
                if dctc.PRINT_DEBUG == True:
                    print("Averaging building", id)
                fig, avg_frame = dctra.make_average_dct_curve(this_building, id, dct_count, avg_coefficients)

                if dctc.DCT_ACTION == "mod average":
                    rmse = dctra.DCT_with_DP(avg_frame, "Averaged DCT", id, \
                                             percent_to_drop=dctc.HIGH_THRESHOLD, keep_highest=dctc.NUMBER_OF_LARGEST, threshold=dctc.DROP_THRESHOLD)
                    
                    # Calculate RMSE for the building between actual power and reconstructed power
                    if dctc.CALC_RMSE == True:
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
                
            else:
                frame = pd.DataFrame(this_building["real_power"])
                frame["Recomposed"] = recomposed

                if dctc.DROP_METHOD == "roll down":
                    graph_dct.graph_shifting_coefficients_down(frame, building_id)
                else:
                    graph_dct.graph_direct_dct(frame, building_id)

                if dctc.SHOW_DCT == True:
                    print("Building", building_id)
                    print(frame)

        # Calculate the RMSE average across buildings
        if dctc.DCT_ACTION == "mod average" and dctc.CALC_RMSE == True:
            all_buildings_rmse_average = 0
            for rmse in all_rmse:
                all_buildings_rmse_average += rmse
            all_buildings_rmse_average = all_buildings_rmse_average / len(all_rmse)
            print(f"RMSE average: {all_buildings_rmse_average}")

        # Graph the distribution of coefficient values per coefficient
        if dctc.DCT_ACTION == "magnitude":
            fig, frame = graph_dct.graph_coefficients_as_box_all_buildings(all_building_coefficient_frames,
                                                              title=f"Coefficient Magnitudes by Building",
                                                              transpose=True)
            fig.show()


    # Graph DCT coefficients...
    if dctc.GRAPH_DCT == True and dctc.GRAPH_DATA_AGAINST_RECOMPOSED == True: # ...recomposed, alongside original data
        graph_dct.graph_recomposed_against_real(recomposed, buildings)

# Test threshold values of interest without having to enter them all by hand  
# If using, run this instead of main()   
def test_thresholds():
    print(f"Time resolution for DCT averaging: {dctc.START_DATE} to {dctc.END_DATE}")
    try: # Test threshold values of interest without having to enter them all by hand
        for threshold in [0.5, 0.6, 0.65, 0.7, 0.75]: #[0.25, 0.5, 0.65, 0.7, 0.75, 0.9]:
            dctc.HIGH_THRESHOLD = threshold
            #dctc.DROP_THRESHOLD = threshold
            #for keep_largest in [1, 2, 5, 10]:
            #    dctc.NUMBER_OF_LARGEST = keep_largest
            main()
    except KeyboardInterrupt:
        print("Stopping (please wait).")



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping (please wait).")