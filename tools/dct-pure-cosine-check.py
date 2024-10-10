from scipy.fftpack import dct
import numpy as np
from typing import Optional
import pandas as pd
from math import cos

DCT_TYPE = 2

# Create the first 5k x positions of a cosine wave
def gen_cosine_data():
    data = []
    for i in range(0, 50000):
        data.append(cos(i/2))
    data = pd.DataFrame(data=data)
    return data

# Generate the coefficients for that data
def gen_cosine_coefficients(data):
    data = data.apply(decompose)
    data = data.rename(columns={0: "Coefficient"})
    return data

# Break data into cosine functions using DCT. Outputs an array of coefficients.
def decompose(
        target_column, # Pandas series to decompose
        log: Optional[bool] = False # Whether to log decomposition to terminal
        ):
    if log == True:
        print("Decomposing into DCT coefficients.")
    # Ortho norm ensures that inverse DCT gets the same values out that went in
    return dct(target_column.to_numpy(), type=DCT_TYPE, norm="ortho") 

# Graph the results
def graph(coefficients):
    print("Generating graph (this will take a few minutes)...")
    import plotly.express as px
    #i = 1
    #for coefficient in coefficients:
    #    record = pd.DataFrame([[i, coefficient]], columns=["Coefficient", "Magnitude"])
    #    if "data" not in locals():
    #        data = record
    #    else:
    #        data = pd.concat([data, record])
    #    i += 1
    fig = px.scatter(coefficients)
    print("Showing graph in web browser")
    #print(data)
    fig.show()
    return fig

def main():
    coefficients = gen_cosine_coefficients(gen_cosine_data())
    print(coefficients)
    graph(coefficients)

main()