import pandas as pd
import plotly.express as px

# Graph the distribution of DCT coefficients to make it easier to choose
# threshold values
def graph_coefficients_as_hist(coefficients_array):
    data = pd.DataFrame(data=coefficients_array)
    data_distribution = pd.DataFrame(data.value_counts())
    data_distribution = data_distribution.reset_index()
    data_distribution = data_distribution.rename(columns={0: "Coefficient"})
    fig = px.histogram(data_distribution, x="Coefficient", y="count", marginal="box")
    print("Showing graph in web browser")
    fig.show()

def graph_coefficients_as_scatter(coefficients_frame):
    print("Generating graphs (this will take a few minutes)...")
    fig = px.scatter(coefficients_frame)
    print("Showing graph in web browser")
    fig.show()

def graph_coefficients_by_building(coefficients_2d_array):
    # A list of numpy arrays; one array per day of data
    print("Generating graph (this will take a few minutes)...")
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

def graph_coefficients_by_day(coefficients):
    print("Generating graphs (this will take a few minutes)...")
    scatter = False
    box = True
    if scatter == True:
        fig = px.scatter(coefficients)
        print("Showing scatter plot in web browser")
        fig.show()
    if box == True:
        fig = px.box(coefficients, x=coefficients.index, y=coefficients.columns, title="Coefficient Magnitude by Day", color=coefficients.columns) # points=False
        print("Showing box plot in web browser")
        fig.show()

# Graph building real_power against recomposed DCT data
def graph_recomposed_against_real(dct_frame, buildings_frame):
    print("Preparing graph for building", id)
    graphframe = pd.DataFrame()
    graphframe = pd.concat((graphframe, pd.Series(data=dct_frame)))
    graphframe = graphframe.rename(columns={0: "recomposed"})
    graphframe = pd.concat((graphframe, buildings_frame["real_power"].reset_index()), axis=1)
    graphframe = graphframe.set_index("timestamp")
    fig = px.line(graphframe)
    fig.update_traces(opacity=0.75)
    fig.data[0].line.color = "red"
    fig.data[1].line.color = "#A9A9A9"
    print("Showing graph in web browser")
    fig.show()