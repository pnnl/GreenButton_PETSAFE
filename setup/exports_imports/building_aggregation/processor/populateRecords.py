import os
import csv
import datetime
import time
import sys 

sys.path.append('/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation/processor')
sys.path.append('/home/ubuntu/PETSAFE/setup/exports_imports/building_aggregation')

if __name__ == "__main__":
    from commonDB import DBConn
    from commonDB import helpers as h
    from config import DATABASE, ROOT_DATA_DIR
else:
    from .commonDB import DBConn
    from .commonDB import helpers as h
    from ..config import DATABASE, ROOT_DATA_DIR

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
    DBConn.drop_TABLE(database,"POWER")   #THis is for init
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
            # if os.path.basename(cur_path) == "power":
            if 'POWER' in os.path.basename(fullPath) and 'new' in os.path.basename(fullPath):
                allFiles.append(fullPath) # This is a file in the right place. Keep it.
        else:
            # This is a directory, not a file. We may need the files inside it.
            # Iterate through the subdirectory looking for power directories
            iterate(fullPath,allFiles)


def populateAll():
    allFiles = [] # list to store files
    #iterate(dir_path,allFiles) # Find the files in this dir and its subdirectories
    iterate(ROOT_DATA_DIR, allFiles)
    # database = 'records.db'
    database = DATABASE
    # What is this?
    #["lt",["sqrt",["sum", ["pow","PowerSystemResource.Measurement.MeasurementType.ReactivePower",2], ["pow","PowerSystemResource.Measurement.MeasurementType.ActivePower",2]]],100]

    print()
    print(allFiles)
    print()

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
                        
                        except KeyError as e:
                            if site_id not in missing_ids: # This site has not had missing circuits before
                                missing_ids[site_id] = [] # Add the site to the missing ids list to record that it wasn't processed
                            if circuit_label not in missing_ids[site_id] and circuit_label not in points_DB[site_id]: # This circuit has not been recorded as missing for this site
                                missing_ids[site_id] += [circuit_label] # Add the circuit to the site's missing entries
                                print (circuit_label, "is not present in siteID", site_id)
                        except Exception as e:
                            print (row)
                            print('Handle error')
                    elif len(row) != 8: # Handle misformatted data
                        print("Columns missing from row:", str(row))
            DBConn.insert_PowerRecords(conn, allRows)
            #createIndex = "CREATE INDEX index_point_id ON point_id"
            #cursor_obj.execute(createIndex)
            #cursor_obj.execute("PRAGMA optimize;")
            cursor_obj.close()
            print ("Done with", aFile)




def populateAllV2():
    database = DATABASE
    input_file='POWER15_wide_new.csv'  #this file must be procured from the NEEA data and placed in the same directory as this script. It is a wide-format version of the power data, with one row per timestamp and separate columns for each circuit's power measurements. This is a more efficient format for loading the data, but it requires some assumptions about the data structure (eg. that there are only two columns for mains measurements, "Mains" and "Mains with Solar", and that these are labeled as such in the points.csv file).
    #ee_site_id,MIN_T_l,MAX_T_l,min_t,max_t,Central AC,Central Vacuum,Clothes Dryer,Clothes Washer,Dishwasher,Ducted Heatpump,Ductless Heatpump,Electric Baseboard Heaters,Electric Furnace,Electric Resistance Storage Water Heaters,ERV,EULR BOX,EVSE,Garbage Disposal,Gas Furnace (Component),Heat Pump Water Heater,Hot Tub,Ignitor,Instantaneous Water Heater (Elec),Instantaneous Water Heater (Gas),Mains,Mains With Solar,Microwave,Other,Other Large Load,Other With Solar,Other Zonal Heat,PTAC,PUMP,Refrigerator/Freezer,Room AC,Solar,Stove/Oven/Range,Sub Panel
    #491,2019-07-31 17:00:00.000,2019-07-31 17:14:00.000,2019-08-01 00:00:00.000,2019-08-01 00:14:00.000,,,0.002,0.144,0,,0.184,0,,0,,,,0.01,,,0.001,,,,,-0.151,,0.419,,,,,,,,-1.531,0.003,
    #491,2019-07-31 17:15:00.000,2019-07-31 17:29:00.000,2019-08-01 00:15:00.000,2019-08-01 00:29:00.000,,,0.002,0.275,0,,0.186,0,,0,,,,0.01,,,0.002,,,,,0.19,,0.312,,,,,,,,-1.421,0.004,
    #491,2019-07-31 17:30:00.000,2019-07-31 17:44:00.000,2019-08-01 00:30:00.000,2019-08-01 00:44:00.000,,,0.001,0.1,0,,0.182,0,,1.277,,,,0.01,,,0.001,,,,,1.158,,0.357,,,,,,,,-1.301,0.003,
    #491,2019-07-31 17:45:00.000,2019-07-31 17:59:00.000,2019-08-01 00:45:00.000,2019-08-01 00:59:00.000,,,0.002,0.158,0,,0.184,0,,0,,,,0.01,,,0.001,,,,,-0.024,,0.349,,,,,,,,-1.176,0.003,
    #491,2019-07-31 18:00:00.000,2019-07-31 18:14:00.000,2019-08-01 01:00:00.000,2019-08-01 01:14:00.000,,,0.002,0.274,0,,0.18,0,,0,,,,0.01,,,0.002,,,,,0.318,,0.35,,,,,,,,-1.033,0.003,
    #491,2019-07-31 18:15:00.000,2019-07-31 18:29:00.000,2019-08-01 01:15:00.000,2019-08-01 01:29:00.000,,,0.002,0.092,0,,0.177,0,,0,,,,0.01,,,0.001,,,,,1.331,,0.345,,,,,,,,-0.889,0.003,
    #491,2019-07-31 18:30:00.000,2019-07-31 18:44:00.000,2019-08-01 01:30:00.000,2019-08-01 01:44:00.000,,,0.002,0.167,0,,0.177,0,,0,,,,0.01,,,0.001,,,,,0.596,,0.34,,,,,,,,-0.736,0.003,
    #491,2019-07-31 18:45:00.000,2019-07-31 18:59:00.000,2019-08-01 01:45:00.000,2019-08-01 01:59:00.000,,,0.002,0.271,0,,0.128,0,,0,,,,0.01,,,0.002,,,,,0.657,,0.243,,,,,,,,-0.647,0.003,
    #491,2019-07-31 19:00:00.000,2019-07-31 19:14:00.000,2019-08-01 02:00:00.000,2019-08-01 02:14:00.000,,,0.002,0.089,0,,0.012,0,,0,,,,0.01,,,0.001,,,,,0.606,,0.39,,,,,,,,-0.502,0.003,

    loadDataLabels(database)
    DBConn.create_POWERTABLE(database)
    # create a database connection
    with DBConn.create_connection(database) as conn:
        cursor_obj = conn.cursor()
        cursor_obj.execute("BEGIN TRANSACTION") # Speeds up transaction
        points_DB = {}
        points_DB_V2={}
        # Labels table contains data about each circuit's locations and attributes
        # sourced from points.csv.
        # One row corresponds to one meter.
        allLabels = DBConn.query(conn,"select * from LABELS")
        for entry in allLabels:
            siteID = entry[0] # ee_site_id, unique id for site
            circuitLabel = entry[2] # regname, eg. "Mains"
            pointID = entry[1] # point_id, unique id for meter
            STD_Label = entry[4] 

            if siteID not in points_DB_V2:
                points_DB_V2[siteID]={}
            if STD_Label not in  points_DB_V2[siteID]:
                points_DB_V2[siteID][STD_Label]=circuitLabel
            else:
                if STD_Label in ['Other', 'Ductless Heatpump','Electric Baseboard Heaters',
                                 'Other Zonal Heat','Electric Furnace','Stove/Oven/Range',
                                 'Refrigerator/Freezer','Gas Furnace (Component)','Ducted Heatpump',
                                 'Electric Resistance Storage Water Heaters','Electric Resistance Storage Water Heaters',
                                 'Dishwasher','Garbage Disposal','Instantaneous Water Heater (Elec)', 'Central AC',
                                 'Hot Tub','Clothes Dryer','Microwave','Other With Solar','Clothes Washer']:
                    pass
                else:
                    print (points_DB_V2[siteID][STD_Label])
                    print (entry)
                    print ("Repeated descriptor: ",STD_Label)

            # Add site to the dictionary of points
            if siteID in points_DB:
                if circuitLabel not in points_DB[siteID]: # Site exists, but not this particular meter on the site
                    points_DB[siteID][circuitLabel] = pointID
                else: # Site and meter already exist. TODO: consider checking whether they're identical and requesting choice if not identical
                    print("SiteID:", siteID, " [Error]", circuitLabel, pointID, "already has a point ID", points_DB[siteID][circuitLabel])
            else: # Site does not exist in points_DB
                points_DB[siteID] = {circuitLabel:pointID}

        missing_ids={} # Holds IDs missing: "site_id": [missing_circuits_at_site]
        rowCount=0
        ErrorRows=[]
        with open(input_file, newline='') as csvfile:
            data = csv.reader(csvfile, delimiter=',', quotechar='"')
            allRows = [] # Will hold file contents
            for row in data:
                ##['ee_site_id', 'timestamp_end', 'timestamp_start', 'duration', 'Mains', 'Mains With Solar']
                if len(row) == 6 and row[0] != 'ee_site_id' and row[0] != '': # Assert that is not the header or empty
                    #assert row[4]=='15', "Measurements must have 15 minute intervals"
                    site_id = int(row[0])
                    try:
                        if 'Mains With Solar' in points_DB_V2[site_id]:
                            circuit_label=points_DB_V2[site_id]['Mains With Solar']
                            key_row=5
                        if 'Mains' in points_DB_V2[site_id]:
                            circuit_label=points_DB_V2[site_id]['Mains']
                            key_row=4
                        if 'Mains With Solar' in points_DB_V2[site_id] and 'Mains' in points_DB_V2[site_id]:
                            print ("Confused, Mains and Mains with Solar exist at the same location??? ",site_id)
                        
                        if row[4]=='' and  key_row==4:
                            print ("Why is this column not populated??? ",site_id)
                            ErrorRows.extend([row])
                            continue
                        if row[5] =='' and  key_row==5:
                            print ("Why is this column not populated??? ",site_id)
                            ErrorRows.extend([row])
                            continue
                        if (row[4] !='') and   (row[5] !='') :
                            print ("Why are both cols populated")
                            ErrorRows.extend([row])
                            continue
                    except KeyError as e:
                        print ("missing key in",site_id)
                        continue

                    #circuit_label = row[1]
                    try:
                        pointID = points_DB[site_id][circuit_label]
                        # prow: "print row" or "point row"
                        prow = (site_id, pointID, h.getTime(row[1]), int(row[3]), h.getValue(row[key_row]), 0, 1)
                        allRows.extend([prow])
                        rowCount+=1
                        if len(allRows)>1000:
                            DBConn.insert_PowerRecords(conn, allRows)
                            allRows=[]
                    
                    except KeyError as e:
                        if site_id not in missing_ids: # This site has not had missing circuits before
                            missing_ids[site_id] = [] # Add the site to the missing ids list to record that it wasn't processed
                        if circuit_label not in missing_ids[site_id] and circuit_label not in points_DB[site_id]: # This circuit has not been recorded as missing for this site
                            missing_ids[site_id] += [circuit_label] # Add the circuit to the site's missing entries
                            print (circuit_label, "is not present in siteID", site_id)
                    except Exception as e:
                        print (row)
                        print('Handle error')
                elif len(row) != 8: # Handle misformatted data
                    print("Columns missing from row:", str(row))
        DBConn.insert_PowerRecords(conn, allRows)
        #createIndex = "CREATE INDEX index_point_id ON point_id"
        #cursor_obj.execute(createIndex)
        #cursor_obj.execute("PRAGMA optimize;")
        cursor_obj.close()

        with open("errors.csv", 'w', newline='') as file:
            # Create a csv.writer object
            writer = csv.writer(file)

            # Write all rows at once using writerows()
            writer.writerows(ErrorRows)

        print ("Done with",rowCount)


if __name__ == "__main__":
    populateAllV2()