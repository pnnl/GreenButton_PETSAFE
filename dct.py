from scipy.fftpack import dct, idct
from math import floor
import numpy as np
from typing import Optional
import pandas as pd

DCT_TYPE = 2

DROP_BELOW_THRESHOLD = True
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
    if log == True:
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
            # TODO: deal with duplicate maxes
            high_freqs = np.delete(high_freqs, np.where(high_freqs == value_to_keep))
            keep_position = np.where(all_freqs == value_to_keep)
            print("Keeping", value_to_keep, "at", keep_position)
            coefficients_array[keep_position] = value_to_keep

    #print(coefficients_array)
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

def analyze(coefficients_array):
    import plotly.express as px
    data = pd.DataFrame(data=coefficients_array)
    data_distribution = pd.DataFrame(data.value_counts())
    #print(data_distribution.index)
    data_distribution = data_distribution.reset_index()
    data_distribution = data_distribution.rename(columns={0: "Coefficient"})
    #data_distribution = data_distribution.set_index("Coefficient")
    print(data_distribution)
    # , x="Coefficient", y="count"
    fig = px.histogram(data_distribution, x="Coefficient", y="count", marginal="box")
    print("Showing graph in web browser")
    fig.show()
