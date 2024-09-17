import pandas as pd
import numpy as np
from scipy.fftpack import dct, idct

DCT_TYPE = 2

def decompose(target_column):
    print("Decomposing into DCT coefficients.")
    real_power = target_column.to_numpy()
    dct_real = dct(real_power, type=DCT_TYPE)
    return dct_real

def drop_coefficients(coefficients_array):
    thresholds = [-0.1, 0.1]
    thresholds = [0, 0]
    print("Dropping all coefficients between", thresholds[0], "and", thresholds[1])
    # Zero all values below threshold
    for value in coefficients_array:
        if value > thresholds[0] and value < thresholds[1]:
            coefficients_array[coefficients_array == value] = 0
    #print(coefficients_array)
    return coefficients_array

def recompose(coefficients_array):
    data = idct(coefficients_array, type=DCT_TYPE)
    # Problem: recomposition is not perfectly recreating values. It's CLOSE, but not the same.
    print(66.432 / 0.346) # To find the scalar difference, ratio of the first 2 non-0 values
    scalar = 192.00000000000003
    data = data / scalar
    return data
