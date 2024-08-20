import os
import csv
import datetime
import time

from commonDB import DBConn
from commonDB import helpers as h

# folder path
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2018'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2019'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2020'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2021'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2022'

dir_path="..\\"

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
    dataLabels=os.path.join(dir_path,"processor","points.csv")

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
                    # prow is short for "print row"
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



def main():
    allFiles = [] # list to store files
    iterate(dir_path,allFiles) # Find the files in this dir and its subdirectories
    database = 'records.db'
    #["lt",["sqrt",["sum", ["pow","PowerSystemResource.Measurement.MeasurementType.ReactivePower",2], ["pow","PowerSystemResource.Measurement.MeasurementType.ActivePower",2]]],100]

    if 1==2:
        loadDataLabels(database)
        DBConn.create_POWERTABLE(database)
    # create a database connection
    conn = DBConn.create_connection(database)
    with conn:
        points_DB={}
        allLabels=DBConn.query(conn,"select * from LABELS")
        for entry in  allLabels:
            siteID=entry[0]
            curcuitLabel=entry[2]
            pointID=entry[1]
        
            if siteID in points_DB:
                if curcuitLabel not in points_DB[siteID]:
                    points_DB[siteID][curcuitLabel]=pointID
                else:
                    print("SiteID:" ,siteID," [Error]",curcuitLabel,pointID, "already has a point ID",points_DB[siteID][curcuitLabel])
            else:
                points_DB[siteID]={curcuitLabel:pointID}

        missing_ids={}
        for aFile in allFiles:
            with open(aFile, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                allRows=[]
                for row in spamreader:
                    if len(row)==8 and row[0]!='ee_site_id':   #Assert that is not hte header
                        #assert row[4]=='15', "Measurements must have 15 minute intervals"
                        site_id=int(row[0])
                        circuit_label=row[1]
                        try:
                            pointID=points_DB[site_id][circuit_label]
                            prow=(site_id,pointID,h.getTime(row[2]),int(row[4]),h.getValue(row[5]),h.getValue(row[6]),h.getValue(row[7]))
                            #print(', '.join(prow))
                            allRows.extend([prow])
                        except Exception as e:
                            if site_id not in missing_ids:
                                missing_ids[site_id]=[]
                            if circuit_label not in missing_ids[site_id]:
                                missing_ids[site_id]+=[circuit_label]
                                x=os.path.basename(aFile)
                                print (circuit_label,"is not present in siteID",site_id)
                            #print (e)
                DBConn.insert_PowerRecords(conn, allRows)
                print ("Done with", aFile)

main()