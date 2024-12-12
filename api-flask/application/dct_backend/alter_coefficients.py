from math import floor
import numpy as np
from typing import Optional

# Zero some coefficients to "smooth" data
def drop_coefficients(
        coefficients_array,
        method,
        PORTION_TO_DROP: Optional[float] = 0,
        NUMBER_OF_LARGEST: Optional[int] = 1,
        THRESHOLD_VAL: Optional[int] = 10
        ):
    # Used to drop high values and/or add their max value(s) back in
    index_of_drop = floor(len(coefficients_array) * PORTION_TO_DROP)

    match method.lower():

    # We'll need to keep high freq values to add them back in later.
        case "drop high keep max":
            all_freqs = np.copy(coefficients_array)
            high_freqs = all_freqs[-index_of_drop:]

    # Zero all values whose absolute value is below a threshold
        case "threshold":
            thresholds = [-THRESHOLD_VAL, THRESHOLD_VAL]
            #if dctc.PRINT_DEBUG == True:
            #    print("Zeroing all coefficients with an absolute value below", THRESHOLD_VAL)
            # Zero all values below magnitude threshold
            for value in coefficients_array:
                if value > thresholds[0] and value < thresholds[1]:
                    coefficients_array[coefficients_array == value] = 0

    # Zero all high frequency values over a certain portion of the array
    if method.lower() in ["drop high", "drop high keep max"]:
        #if dctc.PRINT_DEBUG == True:
        #    print("Zeroing the upper", PORTION_TO_DROP, "of high-frequency coefficients.")
        # Drop high frequency values
        coefficients_array[-index_of_drop:] = 0

    # Add back in the most significant high frequency coefficients
    if method.lower() == "drop high keep max":
        for i in range(0, NUMBER_OF_LARGEST):
            value_to_keep = max(high_freqs)
            # TODO: deal with duplicate maxes
            high_freqs = np.delete(high_freqs, np.where(high_freqs == value_to_keep))
            keep_position = np.where(all_freqs == value_to_keep)
            #if dctc.PRINT_DEBUG == True:
            #    print("Keeping", value_to_keep, "at", keep_position)
            coefficients_array[keep_position] = value_to_keep

    #if dctc.PRINT_DEBUG == True:
    #    print("Coefficient adjustment done.")
    return coefficients_array