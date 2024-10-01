from scipy.fftpack import dct, idct
from math import floor
import numpy as np
from typing import Optional
import pandas as pd

import normalization as norm

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
    # Ortho norm ensures that inverse DCT gets the same values out that went in
    dct_real = dct(real_power, type=DCT_TYPE, norm="ortho")
    return dct_real

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

def compare_averages(recomposed_data, original_data):
    original_avg = original_data.sum() / original_data.size
    dct_avg = recomposed_data.sum() / recomposed_data.size
    avg_difference = dct_avg - original_avg
    return avg_difference, dct_avg

# Find best values to maintain accuracy of DCT data
def fit_accuracy(
        original_data, 
        method: Optional[str] = None,
        DROP_HIGH: Optional[bool] = DROP_HIGH,
        PORTION_TO_DROP: Optional[float] = PORTION_TO_DROP,
        KEEP_LARGEST_HIGH: Optional[bool] = KEEP_LARGEST_HIGH,
        NUMBER_OF_LARGEST: Optional[int] = NUMBER_OF_LARGEST,
        DROP_BELOW_THRESHOLD: Optional[bool] = DROP_BELOW_THRESHOLD,
        THRESHOLD_VAL: Optional[int] = THRESHOLD_VAL):

    def test_fit(
            original_data,
            DROP_HIGH: Optional[bool] = DROP_HIGH,
            PORTION_TO_DROP: Optional[float] = PORTION_TO_DROP,
            KEEP_LARGEST_HIGH: Optional[bool] = KEEP_LARGEST_HIGH,
            NUMBER_OF_LARGEST: Optional[int] = NUMBER_OF_LARGEST,
            DROP_BELOW_THRESHOLD: Optional[bool] = DROP_BELOW_THRESHOLD,
            THRESHOLD_VAL: Optional[int] = THRESHOLD_VAL
            ):
        dct_matrix = decompose(original_data)
        dct_matrix = drop_coefficients(dct_matrix, DROP_HIGH=DROP_HIGH, PORTION_TO_DROP=PORTION_TO_DROP, KEEP_LARGEST_HIGH=KEEP_LARGEST_HIGH,\
                            NUMBER_OF_LARGEST=NUMBER_OF_LARGEST, DROP_BELOW_THRESHOLD=DROP_BELOW_THRESHOLD, THRESHOLD_VAL=THRESHOLD_VAL)
        recomposed = recompose(dct_matrix)
        print("Difference:", compare_averages(recomposed, original_data))
        diff, dct_avg = compare_averages(recomposed, original_data)
        return diff, dct_avg
    
    def check_best(value, avg_diff, dct_avg, current_best):
        if avg_diff > current_best[1] and dct_avg > 0:
            best["Average"] = (value, avg_diff)
        return best

    original_data = pd.Series(data=norm.normalize(original_data))
    best = (0, 0) # value, average
    best = {"Average": (0,0), \
            "Min": (0,0), \
            "Max": (0,0)}
    match method:
        case "threshold":
            DROP_BELOW_THRESHOLD = True
            print("Fitting for 'drop below threshold.'")
            min_to_test = 2
            max_to_test = 100
            for i in range(min_to_test, max_to_test + 1):
                THRESHOLD_VAL = i
                diff, dct_avg = test_fit(original_data, DROP_BELOW_THRESHOLD=DROP_BELOW_THRESHOLD, THRESHOLD_VAL=THRESHOLD_VAL)
                best = check_best(i, diff, dct_avg, best)

        case "drop high":
            DROP_HIGH = True
            print("Fitting for 'drop high'")
            min_to_test = 10
            max_to_test = 100
            for i in range(min_to_test, max_to_test + 1):
                PORTION_TO_DROP = i / 100
                diff, dct_avg = test_fit(original_data, DROP_HIGH=DROP_HIGH, PORTION_TO_DROP=PORTION_TO_DROP)
                best = check_best(i, diff, dct_avg, best)

        case "drop high keep max":
            KEEP_LARGEST_HIGH = True
            print("Fitting for 'drop high, keep maximum value(s).'")
            min_to_test = 2
            max_to_test = 100
            for i in range(min_to_test, max_to_test + 1):
                PORTION_TO_DROP = i / 100
                min_to_keep = 2
                max_to_keep = 10
                for i in range(min_to_keep, max_to_keep + 1):
                    NUMBER_OF_LARGEST = i
                    diff, dct_avg = test_fit(original_data, KEEP_LARGEST_HIGH=KEEP_LARGEST_HIGH, PORTION_TO_DROP=PORTION_TO_DROP, \
                                    NUMBER_OF_LARGEST=NUMBER_OF_LARGEST)
                    best = check_best(i, diff, dct_avg, best)
        case __:
            print("""Available methods for coefficient reduction:
              "threshold"
              "drop high"
              "drop high keep large"
              """)
            return None

    print("Best fit for weighted average:", best["Average"][0], "with average difference of", best["Average"][1])
    return best
