from scipy.fftpack import dct, idct
from sklearn.preprocessing import minmax_scale
import pandas as pd
from typing import Optional

# Chosen because it can be reversed perfectly
DCT_TYPE = 2

# Config
# TODO: REPLACE THESE WITH ARGUMENTS!

START_DATE = "2023-07-03"
END_DATE = "2023-07-08"

PORTION_TO_DROP = 3/4

# Method used for dropping coefficients to 0. Options:
# "threshold": drop all below a threshold value
# "drop high": drop the upper X% of frequencies
# "drop high keep max": drop the upper X% of frequencies, but keep the largest N
# "roll down": move values of high frequency coefficients down by adding them to low frequency coefficients; then zero them
DROP_METHOD = "roll down"

# If using drop high keep max: how many largest coefficients to keep
NUMBER_OF_LARGEST = 5

# If using threshold: at what value and below to drop coefficients to 0
DROP_THRESHOLD = 10
THRESHOLD_VAL = DROP_THRESHOLD

# Cutoff point for considering something "high frequency"; e.g.
# 0.25 treats the top 25% of coefficients as being "high frequency"
# Must be between 0 and 1
PORTION_TO_DROP = 0.5

# If using roll down: what percentage of each coefficient to move down
PERCENTAGE_KEPT = 1

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

# Perform DCT on each day of data in frame;
# frame should have a datetime index
def dct_by_day(frame, column_for_dct):
    # Split building data into days; do DCT per day
    all_days =  pd.date_range(start=START_DATE, end=END_DATE, freq="d", normalize=True, inclusive="both")
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

# Recreate data from DCT coefficients
def recompose(coefficients_array):
    # Reconstruct the data from the coefficients array
    # Ortho norm ensures that inverse DCT gets the same values out that went in
    coefficients_array = list(coefficients_array) # Fixes a KeyError
    data = idct(coefficients_array, type=DCT_TYPE, norm="ortho")
    # data is a list of numpy arrays. Change it into a flat list of Python floats for graphing.
    data = list(data.flat)
    cleaned_data = [x.item() for x in data]
    return cleaned_data

# Find the difference between the average values of actual and recreated data
def compare_averages(recomposed_data, original_data):
    original_avg = original_data.sum() / original_data.size
    dct_avg = recomposed_data.sum() / recomposed_data.size
    avg_difference = dct_avg - original_avg
    return avg_difference, dct_avg

# data should be a pandas frame column (series)
def normalize(data):
    data = data.to_numpy()
    return minmax_scale(data)

if __name__ == '__main__':
    print("Please import perform_dct into another script and supply coefficients to your preferred function.")