import pandas as pd
import plotly.express as px
from typing import Optional
from os.path import exists
from os import makedirs

import dct.dct_config as dctc

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

def graph_coefficients_as_scatter(
        frame,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None
        ):
    print("Generating graphs (this will take a few minutes)...")
    x_label = frame.index if x_label == None else x_label
    y_label = frame.columns if y_label == None else y_label
    fig = px.scatter(frame, labels={"index": x_label, "value": y_label}) # color="Building"
    print("Showing graph in web browser")
    fig.show()

# Graph a single building's coefficient distribution as a box plot
def graph_coefficients_as_box(
        coefficients: object, # DataFrame
        title: str,
        transpose: Optional[bool] = False
        ):
    print("Generating graphs (this will take a few minutes)...") #color=coefficients.columns
    if transpose == True: # Needed to graph distribution of coefficient values by coefficient
        coefficients = coefficients.transpose()
    fig = px.box(coefficients, title=title, labels={"variable": "Coefficient", "value": "Value"}) # points=False
    print("Showing box plot in web browser")
    fig.show()

# Show coefficient distributions for ALL buildings as parallel box plots
# Outputs two graphs- one including each indv building and one overlaid plot, and one box plot of all
# buildings' distributions side by side
# Warning: VERY LONG graph. Had to be long to distinguish between boxes.
# TODO: Legend is not functional; find a way to make the legend work by incorporating building id in frame
# For now, color and order distinguish buildings; first in graph is 1, second is 2, etc.
# Matches order of provided buildings, so if you had buildings 2, 6, and 8, then that's your order.
def graph_coefficients_as_box_all_buildings(
        coefficients: list, # List of DataFrames
        title: str,
        transpose: Optional[bool] = False
        ):
    from plotly.subplots import make_subplots
    print("Generating graphs (this will take a few minutes)...")
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
    color = 0
    row_height = 1000
    row_count = len(coefficients) + 1 # 1 is for all buildings together
    subplot_titles = ["All Buildings"]
    for i in range(1,row_count+1):
        subplot_titles.append(f'Building {i}')
    fig = make_subplots(rows=row_count, cols=1, column_widths=[10000], row_heights=[row_height]*row_count, x_title="Coefficient", y_title="Value", \
                        subplot_titles=tuple(subplot_titles))
    row = 2
    bid = 0
    for frame in coefficients:
        if transpose == True: # Needed to graph distribution of coefficient values by coefficient
            frame = frame.transpose()
        framefig = px.box(frame, labels={"variable": "Coefficient", "value": "Value"})
        trace = framefig.data[0]
        trace.line.color = colors[color]
        fig = fig.add_trace(trace, row=1,col=1) # The general plot
        # Separate plot for buildings side by side as box plots
        if "all_buildings_fig" not in locals():
            all_buildings_fig = framefig
        else:
            all_buildings_fig = all_buildings_fig.add_trace(trace)
        # Add to specific subplot for that building in main plot
        fig = fig.add_trace(trace, row=row, col=1)
        # Titles of axes
        #fig.update_xaxes(title_text="Coefficient", row=row, col=1)
        #fig.update_xaxes(title_text="Value", row=row, col=1)
        # Set up next building's placement
        row += 1
        # Set up next building's color
        color += 1
        # Set up title
        bid += 1
    print("Showing box plot in web browser")
    all_buildings_fig.update_layout(title_text=title, width=10000) # Long enough to see all buildings side by side
    fig.update_layout(title_text=title, height=(row_count*row_height), width=10000) # Long enough to see all buildings side by side
    #fig.show()
    #all_buildings_fig.show()
    return fig, frame

# Graph each building's coefficient distribution
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

# Graph frames as multiple lines on the same graph
def graph_lines(
        framelist: list, # One or more dataframes in a list
        x_label: Optional[str] = None,
        y_label: Optional[str] = None
        ):
    print("Generating graphs (this will take a few minutes)...")
    # Prep axes labels
    x_label = framelist[0].index if x_label == None else x_label
    y_label = framelist[0].columns if y_label == None else y_label
    # Prep figure
    if len(framelist) == 1: # Just graphing one series- ideal situation
        fig = px.line(framelist[0], labels={"index": x_label, "value": y_label}) # color="Building"
    else: # Cobbling multiple frames together into one graph
        for frame in framelist:
            if "fig" not in locals():
                fig = px.line(frame, labels={"index": x_label, "value": y_label}) # color="Building"
            else:
                fig = fig.add_trace(px.line(frame, labels={"index": x_label, "value": y_label}).data[0])
    print("Showing graph in web browser")
    fig.show()

# Graph the effects of shifting coefficients down
def graph_shifting_coefficients_down(frame, building_id):
    one_building_only = False
    save_images = True
    # Build the graph
    fig = px.line(frame, title=f"Building {building_id} with High Coefficients Shifted Down (Added to Highest Kept Coefficient)")
    save_dir = "data/graphs/dct-on-real-power-methods/" #+ "building-" + str(building_id) + "/"
    save_title = "shift-down-" + str(dctc.PERCENTAGE_KEPT * 100) + "percent-of-top-" + str(dctc.PORTION_ROLLED * 100) + \
        "-percent-coeffs-from-" + dctc.START_DATE + " to " + dctc.END_DATE + '-Building-' + \
        str(building_id)
    if save_images == True:
        if not exists(save_dir):
            makedirs(save_dir)
        fig.write_html(save_dir + save_title + ".html")
    else:
        fig.show()
    if one_building_only == True:
        raise SystemExit