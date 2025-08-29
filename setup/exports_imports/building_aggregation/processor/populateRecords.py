import os
import csv
import datetime
import time
if __name__ == "__main__":
    from commonDB import DBConn
    from commonDB import helpers as h
else:
    from processor.commonDB import DBConn
    from processor.commonDB import helpers as h
    from config import DATABASE, ROOT_DATA_DIR

# folder paths
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2018'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2019'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2020'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2021'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2022'

# Apologies for the sparse comments- I got this code uncommented and did my best to
# document what's going on. It's my best guess, so take it all with a grain of salt.

dir_path = DATABASE

def loadDataLabels(database):
    def str_to_int(v): # str -> int
        try:
            if v in ["n/a","NA"]:
                output = None
            else:
                output = int(v)
        except:
            print("Cannot convert", v, "to integer.")
            output = 0
        return output
    
    def dtc(v): # datetime convert; str -> epoch as int
        dt = datetime.datetime.strptime(v, "%Y-%m-%d")
        epoch_time = int(time.mktime(dt.timetuple()))
        return epoch_time

    # Recreate the Labels table since we're loading data into it- no duplicates
    DBConn.drop_TABLE(database,"LABELS")
    DBConn.create_LablesTABLE(database)
    dataLabels=os.path.join(ROOT_DATA_DIR,"points.csv")

    #conn = DBConn.create_connection(database)
    # Read data from file
    # TODO: would this be faster with pandas?
    with DBConn.create_connection(database) as conn:        
        with open(dataLabels) as csvfile:
            data = csv.reader(csvfile, delimiter=',', quotechar='"')
            allRows=[]
            rowCounter = 0
            for row in data:
                # Row has all columns, row is not the column labels, and point id (primary key) exists
                if len(row) == 8 and row[0] != 'ee_site_id' and str_to_int(row[1]) != None:
                    #assert row[4]=='15', "Measurements must have 15 minute intervals"
                    # "point row" or possibly "print row"
                    prow=(str_to_int(row[0]), str_to_int(row[1]), str(row[2]), str_to_int(row[3]), \
                        h.escapeStr(row[4]), h.escapeStr(row[5]), h.escapeStr(row[6]), dtc(row[7]))
                    #print(', '.join(prow))
                    allRows.extend([prow])
                elif rowCounter != 0:
                    print(row)
                rowCounter += 1
            DBConn.insert_LabelRecords(conn, allRows)
            print ("Done with", dataLabels)


def iterate(cur_path,allFiles):
    # Iterate directory and subdirectories
    for item in os.listdir(cur_path):
        fullPath=os.path.join(cur_path, item)
        # check if current path is a file
        if os.path.isfile(fullPath):
            if os.path.basename(cur_path) == "power":
                allFiles.append(fullPath) # This is a file in the right place. Keep it.
        else:
            # This is a directory, not a file. We may need the files inside it.
            # Iterate through the subdirectory looking for power directories
            iterate(fullPath,allFiles)


def populateAll():
    allFiles = [] # list to store files
    #iterate(dir_path,allFiles) # Find the files in this dir and its subdirectories
    iterate(ROOT_DATA_DIR, allFiles)
    database = 'records.db'
    # What is this?
    #["lt",["sqrt",["sum", ["pow","PowerSystemResource.Measurement.MeasurementType.ReactivePower",2], ["pow","PowerSystemResource.Measurement.MeasurementType.ActivePower",2]]],100]

    loadDataLabels(database)
    DBConn.create_POWERTABLE(database)
    # create a database connection
    with DBConn.create_connection(database) as conn:
        cursor_obj = conn.cursor()
        cursor_obj.execute("BEGIN TRANSACTION") # Speeds up transaction
        points_DB = {}
        # Labels table contains data about each circuit's locations and attributes
        # sourced from points.csv.
        # One row corresponds to one meter.
        allLabels = DBConn.query(conn,"select * from LABELS")
        for entry in allLabels:
            siteID = entry[0] # ee_site_id, unique id for site
            circuitLabel = entry[2] # regname, eg. "Mains"
            pointID = entry[1] # point_id, unique id for meter
            # Add site to the dictionary of points
            if siteID in points_DB:
                if circuitLabel not in points_DB[siteID]: # Site exists, but not this particular meter on the site
                    points_DB[siteID][circuitLabel] = pointID
                else: # Site and meter already exist. TODO: consider checking whether they're identical and requesting choice if not identical
                    print("SiteID:", siteID, " [Error]", circuitLabel, pointID, "already has a point ID", points_DB[siteID][circuitLabel])
            else: # Site does not exist in points_DB
                points_DB[siteID] = {circuitLabel:pointID}

        missing_ids={} # Holds IDs missing: "site_id": [missing_circuits_at_site]
        for aFile in allFiles:
            # Retrieve data from file
            with open(aFile, newline='') as csvfile:
                data = csv.reader(csvfile, delimiter=',', quotechar='"')
                allRows = [] # Will hold file contents
                for row in data:
                    if len(row) == 8 and row[0] != 'ee_site_id': # Assert that is not the header
                        #assert row[4]=='15', "Measurements must have 15 minute intervals"
                        site_id = int(row[0])
                        circuit_label = row[1]
                        try:
                            pointID = points_DB[site_id][circuit_label]
                            # prow: "print row" or "point row"
                            prow = (site_id, pointID, h.getTime(row[2]), int(row[4]), h.getValue(row[5]), h.getValue(row[6]), h.getValue(row[7]))
                            allRows.extend([prow])
                        except Exception as e:
                            if site_id not in missing_ids: # This site has not had missing circuits before
                                missing_ids[site_id] = [] # Add the site to the missing ids list to record that it wasn't processed
                            if circuit_label not in missing_ids[site_id]: # This circuit has not been recorded as missing for this site
                                missing_ids[site_id] += [circuit_label] # Add the circuit to the site's missing entries
                                print (circuit_label, "is not present in siteID", site_id)
                    elif len(row) != 8: # Handle misformatted data
                        print("Columns missing from row:", str(row))
            DBConn.insert_PowerRecords(conn, allRows)
            createIndex = "CREATE INDEX index_point_id ON point_id"
            cursor_obj.execute(createIndex)
            cursor_obj.execute("PRAGMA optimize;")
            cursor_obj.close()
            print ("Done with", aFile)

if __name__ == "__main__":
    populateAll()