from scipy.fftpack import dct, idct
from math import floor
import numpy as np

DCT_TYPE = 2

DROP_BELOW_THRESHOLD = False
THRESHOLD_VAL = 30

DROP_HIGH = True
PORTION_TO_DROP = 1 / 2

KEEP_LARGEST_HIGH = True
NUMBER_OF_LARGEST = 1

# Break data into cosine functions using DCT. Outputs an array of coefficients.
def decompose(target_column):
    print("Decomposing into DCT coefficients.")
    real_power = target_column.to_numpy()
    dct_real = dct(real_power, type=DCT_TYPE)
    return dct_real

# Zero some coefficients to "smooth" data
def drop_coefficients(coefficients_array):
    # Used to drop high values and/or add their max value(s) back in
    index_of_drop = floor(len(coefficients_array) * PORTION_TO_DROP)

    # We'll need to keep high freq values to add them back in later.
    if KEEP_LARGEST_HIGH == True:
        all_freqs = np.copy(coefficients_array)
        high_freqs = all_freqs[-index_of_drop:]

    # Zero all values whose absolute value is below a threshold
    if DROP_BELOW_THRESHOLD == True:
        thresholds = [-THRESHOLD_VAL, THRESHOLD_VAL]
        print("Zeroing all coefficients with an absolute value below", THRESHOLD_VAL)
        # Zero all values below magnitude threshold
        for value in coefficients_array:
            if value > thresholds[0] and value < thresholds[1]:
                coefficients_array[coefficients_array == value] = 0

    # Zero all high frequency values over a certain portion of the array
    if DROP_HIGH == True:
        print("Zeroing the upper", PORTION_TO_DROP, "of high-frequency coefficients.")
        # Drop high frequency values
        coefficients_array[-index_of_drop:] = 0

        # Add back in the most significant high frequency coefficients
        if KEEP_LARGEST_HIGH == True:
            for i in range(0, NUMBER_OF_LARGEST):
                value_to_keep = max(high_freqs)
                keep_position = np.where(all_freqs == value_to_keep) # TODO: deal with duplicate maxes
                print("Keeping", value_to_keep, "at", keep_position)
                coefficients_array[keep_position] = value_to_keep
    print(coefficients_array)
    print("Coefficient adjustment done.")
    return coefficients_array

def recompose(coefficients_array):
    # Reconstruct the data from the coefficients array
    data = idct(coefficients_array, type=DCT_TYPE)
    # Problem: recomposition appears to be scaled up.
    # Solution: divide by a scalar found by dividing the first two non-0 values in a frame
    # Tested and it appears to hold firm for multiple frames
    # TODO: why does this happen in the first place? Why this value/ratio?
    scalar = 66.432 / 0.346
    data = data / scalar
    return data
