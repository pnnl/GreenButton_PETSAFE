from scipy.fftpack import dct, idct
from math import floor
import numpy as np
import pandas as pd
from typing import Optional

# Saving to file
from config import OUTPUT_DIR
from os.path import exists
from os import makedirs
from pickle import dump

import dct.dct_config as dctc

DCT_TYPE = 2

DROP_BELOW_THRESHOLD = False
THRESHOLD_VAL = dctc.DROP_THRESHOLD

DROP_HIGH = False
PORTION_TO_DROP = 3/4

KEEP_LARGEST_HIGH = False
NUMBER_OF_LARGEST = dctc.NUMBER_OF_LARGEST

# Break data into cosine functions using DCT. Outputs an array of coefficients.
def decompose(
        target_column, # Pandas series to decompose
        log: Optional[bool] = False # Whether to log decomposition to terminal
        ):
    # From SciPy codebase:
    # For a single dimension array ``x``, ``dct(x, norm='ortho')`` is equal to
    # MATLAB ``dct(x)``.

    # **Type II**
    # There are several definitions of the DCT-II; we use the following
    # (for ``norm=None``)

    # .. math::

    #    y_k = 2 \sum_{n=0}^{N-1} x_n \cos\left(\frac{\pi k(2n+1)}{2N} \right)

    # If ``norm='ortho'``, ``y[k]`` is multiplied by a scaling factor ``f``

    # .. math::
    #    f = \begin{cases}
    #    \sqrt{\frac{1}{4N}} & \text{if }k=0, \\
    #    \sqrt{\frac{1}{2N}} & \text{otherwise} \end{cases}

    # which makes the corresponding matrix of coefficients orthonormal
    # (``O @ O.T = np.eye(N)``).
    # return _pocketfft.dct(x, type, n, axis, norm, overwrite_x)
    # -->
    # def dct(x, type=2, n=None, axis=-1, norm=None,
    #     overwrite_x=False, workers=None, orthogonalize=None):
    #     return _execute(_pocketfft.dct, x, type, n, axis, norm, 
    #                 overwrite_x, workers, orthogonalize)
    # -->
    # def _execute(pocketfft_func, x, type, s, axes, norm, 
    #     overwrite_x, workers, orthogonalize):
    #     xp = array_namespace(x)
    #     x = np.asarray(x)
    #     y = pocketfft_func(x, type, s, axes, norm,
    #             overwrite_x=overwrite_x, workers=workers,
    #             orthogonalize=orthogonalize)
    #     return xp.asarray(y)
    # -->
    # dct = functools.partial(_r2r, True, pfft.dct)
    # dct.__name__ = 'dct'
    # -->
    # import functools
    # AND -->
    # THE ACTUAL DCT PART.
    # def _r2r(forward, transform, x, type=2, n=None, axis=-1, norm=None,
    #      overwrite_x=False, workers=None, orthogonalize=None):
    # """Forward or backward 1-D DCT/DST
    # 
    # Parameters
    # ----------
    # forward : bool
    #     Transform direction (determines type and normalisation)
    # transform : {pypocketfft.dct, pypocketfft.dst}
    #     The transform to perform
    # """
    # tmp = _asfarray(x)
    # overwrite_x = overwrite_x or _datacopied(tmp, x)
    # norm = _normalization(norm, forward)
    # workers = _workers(workers)
    # 
    # if not forward:
    #     if type == 2:
    #         type = 3
    #     elif type == 3:
    #         type = 2
    # 
    # if n is not None:
    #     tmp, copied = _fix_shape_1d(tmp, n, axis)
    #     overwrite_x = overwrite_x or copied
    # elif tmp.shape[axis] < 1:
    #     raise ValueError(f"invalid number of data points ({tmp.shape[axis]}) specified")
    # 
    # out = (tmp if overwrite_x else None)
    # 
    # For complex input, transform real and imaginary components separably
    # if np.iscomplexobj(x):
    #     out = np.empty_like(tmp) if out is None else out
    #     transform(tmp.real, type, (axis,), norm, out.real, workers)
    #     transform(tmp.imag, type, (axis,), norm, out.imag, workers)
    #     return out
    # 
    # return transform(tmp, type, (axis,), norm, out, workers, orthogonalize)

    if log == True:
        print("Decomposing into DCT coefficients.")
    # Ortho norm ensures that inverse DCT gets the same values out that went in
    return dct(target_column.to_numpy(), type=DCT_TYPE, norm="ortho")

# Zero some coefficients to "smooth" data
def drop_coefficients(
        coefficients_array,
        PORTION_TO_DROP: Optional[float] = PORTION_TO_DROP,
        NUMBER_OF_LARGEST: Optional[int] = NUMBER_OF_LARGEST,
        THRESHOLD_VAL: Optional[int] = THRESHOLD_VAL
        ):
    # Used to drop high values and/or add their max value(s) back in
    index_of_drop = floor(len(coefficients_array) * PORTION_TO_DROP)

    # We'll need to keep high freq values to add them back in later.
    if dctc.DROP_METHOD.lower() == "drop high keep max":
        all_freqs = np.copy(coefficients_array)
        high_freqs = all_freqs[-index_of_drop:]

    # Zero all values whose absolute value is below a threshold
    elif dctc.DROP_METHOD.lower() == "threshold":
        thresholds = [-THRESHOLD_VAL, THRESHOLD_VAL]
        if dctc.PRINT_DEBUG == True:
            print("Zeroing all coefficients with an absolute value below", THRESHOLD_VAL)
        # Zero all values below magnitude threshold
        for value in coefficients_array:
            if value > thresholds[0] and value < thresholds[1]:
                coefficients_array[coefficients_array == value] = 0
    
    elif dctc.DROP_METHOD.lower() == "roll down":
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

    else:
        if dctc.PRINT_DEBUG == True:
            print("Keeping all coefficients.")
    if dctc.PRINT_DEBUG == True:
        print("Coefficient adjustment done.")
    return coefficients_array

def shift_down_coefficients(coefficients_array):
    # How to handle the down shift
    METHOD = "top only"

    # At what position to start shifting down from; 0.5 shifts upper half down
    position_to_shift = dctc.PORTION_ROLLED
    # What percentage of each coefficient to shift down; remaining values are zeroed
    portion_to_shift = dctc.PERCENTAGE_KEPT

    num_coeffs = len(coefficients_array)
    shift_index = int(num_coeffs - (num_coeffs * position_to_shift)) # Round to nearest index

    print("Number:", num_coeffs)
    print("Shift point:", shift_index)
    # Slice up the list for easier shifting
    coeffs_to_shift = coefficients_array[shift_index:]
    coeffs_to_keep = coefficients_array[:shift_index]
    # Shift down
    for coeff in coeffs_to_shift:
        value_to_shift = coeff * portion_to_shift # This can stay a float
        match METHOD:
            case "top only": # Move all high coefficients into highest kept coefficient
                coeffs_to_keep[-1] += value_to_shift # Add to top coefficient to keep
            case "even across top": # Shift each high coefficient down into its own lower coefficient
                # Remember to handle cases where more than 50% are shifted down; grouping needed
                pass
    coeffs_to_shift = [0 for remainder in coeffs_to_shift] # Zero the leftovers
    coefficients_array = [*coeffs_to_keep, *coeffs_to_shift] # Re-concatenate
    return coefficients_array

# Perform DCT on each day of data in frame;
# frame should have a datetime index
def dct_by_day(frame, column_for_dct):
    # Get first and last timestamps for building
    #start_datetime = frame.index[0]
    #end_datetime = frame.index[-1]
    # Split building data into days; do DCT per day
    all_days =  pd.date_range(start=dctc.START_DATE, end=dctc.END_DATE, freq="d", normalize=True, inclusive="both")
    for day in all_days:
        day_data = frame[day:(day + pd.Timedelta(1, "d"))]
        # Timedelta is both-inclusive. We only want left-inclusive. Drop the very last entry.
        day_data = day_data[:-1]
        # Get coefficients for day
        day_dct_coefficients = pd.Series(decompose(day_data[column_for_dct]), name=day).rename(day)
         # Add to frame as column
        if "coefficients_per_day" not in locals():
            # Set up frame for graphing
            coefficients_per_day = pd.DataFrame(day_dct_coefficients)
        else:
            coefficients_per_day = pd.concat([coefficients_per_day, day_dct_coefficients], axis=1)
    return coefficients_per_day

def recompose(coefficients_array):
    # Reconstruct the data from the coefficients array
    # Ortho norm ensures that inverse DCT gets the same values out that went in
    data = idct(coefficients_array, type=DCT_TYPE, norm="ortho")
    return data

# Add noise to coefficients for differential privacy
# TODO: this is currently very rough and privacy parameters are undecided.
# TODO: right now, noise is added the same way for all coefficients.
# Would some coefficients benefit from more or less noise to balance privacy
# with accuracy? It seems likely.
def add_noise(coefficients_array):
    location = 0
    scale = 1 # TODO: figure out what to set this to
    rng = np.random.default_rng()
    for coefficient in coefficients_array:
        noise = rng.laplace(location, scale)
        noisy_coefficient = coefficient + noise
        coefficients_array[coefficient] = noisy_coefficient
    return coefficients_array


def compare_averages(recomposed_data, original_data):
    original_avg = original_data.sum() / original_data.size
    dct_avg = recomposed_data.sum() / recomposed_data.size
    avg_difference = dct_avg - original_avg
    return avg_difference, dct_avg

# Save all DCT coefficients to file; location varies based on operation
# to make it easier to retrieve coefficients made with specific method
def save_to_file(coefficients, building_id, subdir):
    filename = "Building-" + str(building_id) + "-coefficients.pkl"
    if dctc.PRINT_DEBUG == True:
        print("Saving DCT coefficients to pickle file at", filename)
    # Set directory path of output- output directory in config + "buildings" subdirectory
    dirpath = OUTPUT_DIR + "/coefficients/"
    if dctc.DCT_ONE_DAY == True:
        dirpath = dirpath + "/one-day/"
    if dctc.GRAPH_TARGET == "d":
        dirpath = dirpath + "/daily-coefficients/"
    if dctc.RESAMPLE_BEFORE_DCT == True:
        dirpath = dirpath + "/resampled-buildings/"
    if dctc.HIGH_ONLY == True:
        dirpath = dirpath + "/top-" + str(dctc.HIGH_THRESHOLD) + "/"
    dirpath = dirpath + subdir + "/"
    if not exists(dirpath):
        makedirs(dirpath)
    # Save as file to output dir
    with open(dirpath + filename, "wb") as outfile:
        dump(coefficients, outfile)

if __name__ == '__main__':
    print("Please import perform_dct into another script and supply coefficients to your preferred function.")