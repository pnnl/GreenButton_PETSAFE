import pandas as pd
import pickle
import numpy as np
import plotly.express as px

import config
from dct import perform_dct
import dct.dct_config as dctc
from list_files import list_files_in_dir

def retrieve_and_analyze():
    # Get path to retrieve from
            if config.OUTPUT_DIR[-1] != "/":
                config.OUTPUT_DIR += "/"
            filepath = config.OUTPUT_DIR + "coefficients/"
            if dctc.DCT_ONE_DAY == True:
                filepath = filepath + "one-day/"
            if dctc.DAILY_DCT_GRAPH == True:
                filepath = filepath + "daily-coefficients/"
            if dctc.ANALYZE_DCT_PER_BUILDING == True:
                filepath = filepath + "resampled-buildings/"
            if dctc.HIGH_ONLY == True:
                filepath = filepath + "top-" + str(dctc.HIGH_THRESHOLD) + "/"
            if dctc.NORMALIZE == True: # TODO: separate switch for reading vs writing normalized data?
                filepath = filepath + "normalized/"
            else:
                filepath = filepath + "non-normalized/"
            print(filepath)

            if dctc.ANALYZE_DCT_PER_BUILDING == True or dctc.DAILY_DCT_GRAPH == True:
                coefficients = pd.DataFrame()
            else:
                coefficients = np.empty(0, dtype=np.float64)
            try:
                for file in list_files_in_dir(filepath, append_path=True):
                    with open(file, "rb") as file:
                        building_coefficients = pickle.load(file)
                        # This will be a list of numpy arrays; one array per day of data
                    if dctc.SHOW_DCT == True:
                        print(building_coefficients)
                    if dctc.DAILY_DCT_GRAPH == True:
                        coefficients = building_coefficients
                        print("Generating graphs (this will take a few minutes)...")
                        import plotly.express as px
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
                        break
                    elif dctc.ANALYZE_DCT_PER_BUILDING == True:
                        coefficients[str(file)[79:-19]] = pd.Series(building_coefficients)
                    else:
                        coefficients = np.append(coefficients, building_coefficients)
            except Exception as ex:
                print("Could not unpickle building coefficients:", ex)
                raise SystemExit # For now
            
            if dctc.ANALYZE_DCT_PER_BUILDING == True:
                perform_dct.analyze_daily_buildings(coefficients)

            #if config.ANALYZE_DCT_PER_BUILDING == True:
            #    building_coefficients = dct.analyze_per_building(coefficients)
            #    if config.OUTPUT_DIR[-1] != "/":
            #        config.OUTPUT_DIR += "/"
            #    dirpath = config.OUTPUT_DIR + "coefficients/coefficients-per-building.pkl"
            #    with open(dirpath, "wb") as outfile:
            #        pickle.dump(building_coefficients, outfile)
            elif dctc.ANALYZE_DCT == True:
                perform_dct.analyze(coefficients)

def graph_dct(dct_frame, buildings_frame):
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