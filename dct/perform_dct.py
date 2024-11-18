from scipy.fftpack import dct, idct
from math import floor
import numpy as np
from typing import Optional
import pandas as pd

import dct.normalization as norm
from dct.dct_config import *

DCT_TYPE = 2

DROP_BELOW_THRESHOLD = False
THRESHOLD_VAL = 1

DROP_HIGH = False
PORTION_TO_DROP = 3/4

KEEP_LARGEST_HIGH = False
NUMBER_OF_LARGEST = 5

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
        DROP_HIGH: Optional[bool] = DROP_HIGH,
        PORTION_TO_DROP: Optional[float] = PORTION_TO_DROP,
        KEEP_LARGEST_HIGH: Optional[bool] = KEEP_LARGEST_HIGH,
        NUMBER_OF_LARGEST: Optional[int] = NUMBER_OF_LARGEST,
        DROP_BELOW_THRESHOLD: Optional[bool] = DROP_BELOW_THRESHOLD,
        THRESHOLD_VAL: Optional[int] = THRESHOLD_VAL
        ):
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
            # TODO: deal with duplicate maxes
            high_freqs = np.delete(high_freqs, np.where(high_freqs == value_to_keep))
            keep_position = np.where(all_freqs == value_to_keep)
            print("Keeping", value_to_keep, "at", keep_position)
            coefficients_array[keep_position] = value_to_keep

    else:
        print("Keeping all coefficients.")
    #print(coefficients_array)
    print("Coefficient adjustment done.")
    return coefficients_array

def recompose(coefficients_array):
    # Reconstruct the data from the coefficients array
    # Ortho norm ensures that inverse DCT gets the same values out that went in
    data = idct(coefficients_array, type=DCT_TYPE, norm="ortho")
    return data

# Add noise to coefficients for differential privacy
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

# Graph the distribution of DCT coefficients to make it easier to choose
# threshold values
def analyze(coefficients_array):
    import plotly.express as px
    data = pd.DataFrame(data=coefficients_array)
    data_distribution = pd.DataFrame(data.value_counts())
    data_distribution = data_distribution.reset_index()
    data_distribution = data_distribution.rename(columns={0: "Coefficient"})
    fig = px.histogram(data_distribution, x="Coefficient", y="count", marginal="box")
    print("Showing graph in web browser")
    fig.show()

def analyze_daily_buildings(coefficients_frame):
    print("Generating graphs (this will take a few minutes)...")
    import plotly.express as px
    fig = px.scatter(coefficients_frame)
    print("Showing graph in web browser")
    fig.show()

def analyze_per_building(coefficients_2d_array):
    # A list of numpy arrays; one array per day of data
    print("Generating graph (this will take a few minutes)...")
    import plotly.express as px
    i = 0 # Used to name buildings in rows
    top_coefficient_index = 5000 #50
    for building in coefficients_2d_array:
        j = 1 # Used to determine which coefficient is which
        print("Preparing building", str(i))
        for coefficient in building:
            record = pd.DataFrame([[j, coefficient, "Building " + str(i)]], columns=["Coefficient", "Magnitude", "Building"])
            #record = record.fillna(0)
            j += 1
            if "data" not in locals():
                data = record
            else:
                if j <= top_coefficient_index: # 1-indexed, so "equal to" is included
                    data = pd.concat([data, record])
                else:
                    break
        print("Building", i, "done (", j, "coefficients).")
        i += 1
    fig = px.scatter(data, x="Coefficient", y="Magnitude", color="Building") # color="Building"
    print("Showing graph in web browser")
    print(data)
    fig.show()
    return data

def compare_averages(recomposed_data, original_data):
    original_avg = original_data.sum() / original_data.size
    dct_avg = recomposed_data.sum() / recomposed_data.size
    avg_difference = dct_avg - original_avg
    return avg_difference, dct_avg
