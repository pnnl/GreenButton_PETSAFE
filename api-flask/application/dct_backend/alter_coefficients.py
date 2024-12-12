from math import floor
import numpy as np
from typing import Optional

# This needs to be replaced by function arguments
import dct.dct_config as dctc

# Zero some coefficients to "smooth" data
def drop_coefficients(
        coefficients_array,
        PORTION_TO_DROP: Optional[float] = 0,
        NUMBER_OF_LARGEST: Optional[int] = 1,
        THRESHOLD_VAL: Optional[int] = 10
        ):
    # Used to drop high values and/or add their max value(s) back in
    index_of_drop = floor(len(coefficients_array) * PORTION_TO_DROP)

    match dctc.DROP_METHOD.lower():

    # We'll need to keep high freq values to add them back in later.
        case "drop high keep max":
            all_freqs = np.copy(coefficients_array)
            high_freqs = all_freqs[-index_of_drop:]

    # Zero all values whose absolute value is below a threshold
        case "threshold":
            thresholds = [-THRESHOLD_VAL, THRESHOLD_VAL]
            if dctc.PRINT_DEBUG == True:
                print("Zeroing all coefficients with an absolute value below", THRESHOLD_VAL)
            # Zero all values below magnitude threshold
            for value in coefficients_array:
                if value > thresholds[0] and value < thresholds[1]:
                    coefficients_array[coefficients_array == value] = 0
    
        case "roll down":
            shift_down_coefficients(coefficients_array)

    # Zero all high frequency values over a certain portion of the array
    if dctc.DROP_METHOD.lower() in ["drop high", "drop high keep max"]:
        if dctc.PRINT_DEBUG == True:
            print("Zeroing the upper", PORTION_TO_DROP, "of high-frequency coefficients.")
        # Drop high frequency values
        coefficients_array[-index_of_drop:] = 0

    # Add back in the most significant high frequency coefficients
    if dctc.DROP_METHOD.lower() == "drop high keep max":
        for i in range(0, NUMBER_OF_LARGEST):
            value_to_keep = max(high_freqs)
            # TODO: deal with duplicate maxes
            high_freqs = np.delete(high_freqs, np.where(high_freqs == value_to_keep))
            keep_position = np.where(all_freqs == value_to_keep)
            if dctc.PRINT_DEBUG == True:
                print("Keeping", value_to_keep, "at", keep_position)
            coefficients_array[keep_position] = value_to_keep

    if dctc.PRINT_DEBUG == True:
        print("Coefficient adjustment done.")
    return coefficients_array


# Alter coefficient values by "shifting down":
# If this is the coefficient set after DCT:
# [2.7, 6, 0.5, 63, -9, 12, 2, -8]
# Then applying this method with a value of 0.75 
# (consider the top 75% of coefficients to be "high frequency") yields:
# [2.7 , 66.5, 0, 0, 0, 0, 0, 0]
# This method has a notable weakness: the effects of given parameters vary 
# significantly between buildings. Some buildings will have noticeable curve distortion; 
# others will have little to none, as the high frequency coefficients may cancel themselves out.
def shift_down_coefficients(coefficients_array):
    # At what position to start shifting down from; 0.5 shifts upper half down
    position_to_shift = dctc.PORTION_ROLLED
    # What percentage of each coefficient to shift down; remaining values are zeroed
    portion_to_shift = dctc.PERCENTAGE_KEPT
    # Other parameters needed to know where to shift down
    num_coeffs = len(coefficients_array)
    shift_index = int(num_coeffs - (num_coeffs * position_to_shift)) # Round to nearest index
    # Slice up the list for easier shifting
    coeffs_to_shift = coefficients_array[shift_index:]
    coeffs_to_keep = coefficients_array[:shift_index]
    orig_coeff = coeffs_to_keep[-1]
    print("Num of coeffs to keep:", len(coeffs_to_keep))
    print("Num of coeffs to shift:", len(coeffs_to_shift))
    # Shift down
    for coeff in coeffs_to_shift:
        value_to_shift = coeff * portion_to_shift # This can stay a float
        coeffs_to_keep[-1] += value_to_shift # Add to top coefficient to keep
    coeffs_to_shift = [0 for remainder in coeffs_to_shift] # Zero the leftovers
    print("Original value of last kept coefficient:", orig_coeff)
    print("Altered value of last kept coefficient:", coeffs_to_keep[-1])
    print("Change in value:", coeffs_to_keep[-1] - orig_coeff)
    print("----------")
    coefficients_array = [*coeffs_to_keep, *coeffs_to_shift] # Re-concatenate
    return coefficients_array