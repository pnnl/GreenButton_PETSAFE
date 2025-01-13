import influx_database as idb
import pandas as pd
from dct_backend.list_files import iterate

from multiprocessing import Pool

def data_worker_read(file):
    data = pd.read_csv(file)
    # Add column marking these readings as raw meter data (non-aggregated)
    data["privacy"] = "raw_meter"
    return data

def prepare_data():
    print("Preparing data for import")
    # Get all electrical usage files from the data set
    data_root = "../data/2023-Full_v8.1/"
    # Iterate over subdirectories of the root to find power CSV files
    source_files = [] # list to store files
    iterate(data_root, source_files)
    # Read files to pandas
    # Multiprocessing is used to make the time significantly less
    # File reading takes forever for even one year otherwise
    with Pool(processes=4) as pool:
        partials = pool.map(data_worker_read, source_files)
    # Combine the partial sets
    data = pd.concat(partials, axis=0)
    return data

def write_data(data):
    print("Importing data")
    # Init database connection for writing
    conn = idb.init_client()
    # Write from pandas
    try: # Write
        idb.write_from_pandas(conn, data)
    except Exception as ex: # Writing fails; alert the user
        print(ex)
        return ex
    # We're done; close the connection
    idb.close_client(conn)
    # Return okay
    return "Success"

def main():
    data = prepare_data()
    print(data)
    #status = write_data(data)
    #print(status)

if __name__ == "__main__":
    main()
    