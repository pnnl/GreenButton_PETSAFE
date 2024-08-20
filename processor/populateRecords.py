import os
import csv

from commonDB import DBConn
from commonDB import helpers as h
import datetime
import time


dir_path="..\\"
def loadDataLabels(database):
    def sint(v):
        try:
            if v in ["n/a","NA"]:
                x=None
            else:
                x=int(v)
        except Exception as e:
            x=0
        return x
    def dtc(v):
        dt = datetime.datetime.strptime(v, "%Y-%m-%d")
        epoch_time = int(time.mktime(dt.timetuple()))
        return epoch_time

    DBConn.drop_TABLE(database,"LABELS")
    DBConn.create_LablesTABLE(database)
    dataLabels=os.path.join(dir_path,"processor","points.csv")
    conn = DBConn.create_connection(database)
    with conn:        
        with open(dataLabels) as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            allRows=[]
            rowCounter=0
            for row in spamreader:
                if len(row)==8 and row[0]!='ee_site_id':
                    #assert row[4]=='15', "Measurements must have 15 minute intervals"
                    if sint(row[1])!=None:
                        prow=(sint(row[0]),sint(row[1]),str(row[2]),sint(row[3]),h.escapeStr(row[4]),h.escapeStr(row[5]),h.escapeStr(row[6]),dtc(row[7]))
                        #print(', '.join(prow))
                        allRows.extend([prow])
                    else:
                        #if rowCounter!=0:
                        #    print(sint(row[0]),sint(row[1]),str(row[2]),sint(row[3]),h.escapeStr(row[4]),h.escapeStr(row[5]),h.escapeStr(row[6]),dtc(row[7]))
                        pass
                else:
                    if rowCounter!=0:
                        print(row)
                    pass
                rowCounter+=1
            DBConn.insert_LabelRecords(conn, allRows)
            print ("Done with", dataLabels)




# folder path
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2018'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2019'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2020'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2021'
#dir_path = r'C:\\GitHub\\n95111-data\\NEEA\\2022'


# list to store files
allFiles = []


def iterate(cur_path,allFiles):
    # Iterate directory
    for item in os.listdir(cur_path):
        fullPath=os.path.join(cur_path, item)
        # check if current path is a file
        if os.path.isfile(fullPath):
            if os.path.basename(cur_path)=="power":
                allFiles.append(fullPath)
        else:
           
            iterate(fullPath,allFiles)
iterate(dir_path,allFiles)
database = 'records.db'
#["lt",["sqrt",["sum", ["pow","PowerSystemResource.Measurement.MeasurementType.ReactivePower",2], ["pow","PowerSystemResource.Measurement.MeasurementType.ActivePower",2]]],100]
#CIRCUIT_26 is not present in siteID 10936
#CIRCUIT_13 is not present in siteID 7616
#CIRCUIT_17 is not present in siteID 7616
#CIRCUIT_4 is not present in siteID 7616
#CIRCUIT_27 is not present in siteID 6351
#CIRCUIT_29 is not present in siteID 6351
#CIRCUIT_13 is not present in siteID 4721
#CIRCUIT_18 is not present in siteID 9251
#Mains is not present in siteID 10296
#CIRCUIT_28 is not present in siteID 8746
#CIRCUIT_36 is not present in siteID 8746
#CIRCUIT_15 is not present in siteID 8506
#CIRCUIT_2 is not present in siteID 8506
#CIRCUIT_17 is not present in siteID 3736
#CIRCUIT_20 is not present in siteID 10231

CIRCUIT_9 is not present in siteID 10015
Mains is not present in siteID 10015
CIRCUIT_1 is not present in siteID 10044
CIRCUIT_11 is not present in siteID 10044
CIRCUIT_12 is not present in siteID 10044
CIRCUIT_13 is not present in siteID 10044
CIRCUIT_14 is not present in siteID 10044
CIRCUIT_15 is not present in siteID 10044
CIRCUIT_16 is not present in siteID 10044
CIRCUIT_17 is not present in siteID 10044
CIRCUIT_18 is not present in siteID 10044
CIRCUIT_19 is not present in siteID 10044
CIRCUIT_2 is not present in siteID 10044
CIRCUIT_21 is not present in siteID 10044
CIRCUIT_3 is not present in siteID 10044
CIRCUIT_4 is not present in siteID 10044
CIRCUIT_5 is not present in siteID 10044
CIRCUIT_6 is not present in siteID 10044
CIRCUIT_7 is not present in siteID 10044
CIRCUIT_9 is not present in siteID 10044
Mains is not present in siteID 10044
CIRCUIT_27 is not present in siteID 10068
CIRCUIT_28 is not present in siteID 10068
CIRCUIT_1 is not present in siteID 10099
CIRCUIT_10 is not present in siteID 10099
CIRCUIT_11 is not present in siteID 10099
CIRCUIT_12 is not present in siteID 10099
CIRCUIT_13 is not present in siteID 10099
CIRCUIT_15 is not present in siteID 10099
CIRCUIT_17 is not present in siteID 10099
CIRCUIT_19 is not present in siteID 10099
CIRCUIT_2 is not present in siteID 10099
CIRCUIT_20 is not present in siteID 10099
CIRCUIT_3 is not present in siteID 10099
CIRCUIT_4 is not present in siteID 10099
CIRCUIT_5 is not present in siteID 10099
CIRCUIT_6 is not present in siteID 10099
CIRCUIT_7 is not present in siteID 10099
CIRCUIT_9 is not present in siteID 10099
Mains is not present in siteID 10099
CIRCUIT_1 is not present in siteID 100760
CIRCUIT_10 is not present in siteID 100760
CIRCUIT_11 is not present in siteID 100760
CIRCUIT_12 is not present in siteID 100760
CIRCUIT_13 is not present in siteID 100760
CIRCUIT_14 is not present in siteID 100760
CIRCUIT_16 is not present in siteID 100760
CIRCUIT_17 is not present in siteID 100760
CIRCUIT_18 is not present in siteID 100760
CIRCUIT_19 is not present in siteID 100760
CIRCUIT_20 is not present in siteID 100760
CIRCUIT_21 is not present in siteID 100760
CIRCUIT_22 is not present in siteID 100760
CIRCUIT_24 is not present in siteID 100760
CIRCUIT_26 is not present in siteID 100760
CIRCUIT_3 is not present in siteID 100760
CIRCUIT_4 is not present in siteID 100760
CIRCUIT_5 is not present in siteID 100760
CIRCUIT_6 is not present in siteID 100760
CIRCUIT_7 is not present in siteID 100760
CIRCUIT_8 is not present in siteID 100760
CIRCUIT_9 is not present in siteID 100760
Mains is not present in siteID 100760
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230209.csv
CIRCUIT_1 is not present in siteID 10033
CIRCUIT_10 is not present in siteID 10033
CIRCUIT_11 is not present in siteID 10033
CIRCUIT_12 is not present in siteID 10033
CIRCUIT_13 is not present in siteID 10033
CIRCUIT_14 is not present in siteID 10033
CIRCUIT_15 is not present in siteID 10033
CIRCUIT_16 is not present in siteID 10033
CIRCUIT_17 is not present in siteID 10033
CIRCUIT_19 is not present in siteID 10033
CIRCUIT_2 is not present in siteID 10033
CIRCUIT_20 is not present in siteID 10033
CIRCUIT_21 is not present in siteID 10033
CIRCUIT_22 is not present in siteID 10033
CIRCUIT_23 is not present in siteID 10033
CIRCUIT_24 is not present in siteID 10033
CIRCUIT_3 is not present in siteID 10033
CIRCUIT_4 is not present in siteID 10033
CIRCUIT_5 is not present in siteID 10033
CIRCUIT_7 is not present in siteID 10033
CIRCUIT_9 is not present in siteID 10033
Mains is not present in siteID 10033
CIRCUIT_1 is not present in siteID 10068
CIRCUIT_10 is not present in siteID 10068
CIRCUIT_11 is not present in siteID 10068
CIRCUIT_12 is not present in siteID 10068
CIRCUIT_14 is not present in siteID 10068
CIRCUIT_15 is not present in siteID 10068
CIRCUIT_16 is not present in siteID 10068
CIRCUIT_17 is not present in siteID 10068
CIRCUIT_18 is not present in siteID 10068
CIRCUIT_19 is not present in siteID 10068
CIRCUIT_2 is not present in siteID 10068
CIRCUIT_20 is not present in siteID 10068
CIRCUIT_21 is not present in siteID 10068
CIRCUIT_23 is not present in siteID 10068
CIRCUIT_24 is not present in siteID 10068
CIRCUIT_25 is not present in siteID 10068
CIRCUIT_4 is not present in siteID 10068
CIRCUIT_5 is not present in siteID 10068
CIRCUIT_7 is not present in siteID 10068
CIRCUIT_9 is not present in siteID 10068
Mains is not present in siteID 10068
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230210.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230211.csv
CIRCUIT_1 is not present in siteID 3436
CIRCUIT_11 is not present in siteID 3436
CIRCUIT_13 is not present in siteID 3436
CIRCUIT_15 is not present in siteID 3436
CIRCUIT_16 is not present in siteID 3436
CIRCUIT_17 is not present in siteID 3436
CIRCUIT_18 is not present in siteID 3436
CIRCUIT_19 is not present in siteID 3436
CIRCUIT_2 is not present in siteID 3436
CIRCUIT_20 is not present in siteID 3436
CIRCUIT_21 is not present in siteID 3436
CIRCUIT_22 is not present in siteID 3436
CIRCUIT_24 is not present in siteID 3436
CIRCUIT_3 is not present in siteID 3436
CIRCUIT_4 is not present in siteID 3436
CIRCUIT_5 is not present in siteID 3436
CIRCUIT_6 is not present in siteID 3436
CIRCUIT_7 is not present in siteID 3436
CIRCUIT_9 is not present in siteID 3436
Mains is not present in siteID 3436
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230212.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230213.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230214.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230215.csv
CIRCUIT_1 is not present in siteID 100910
CIRCUIT_11 is not present in siteID 100910
CIRCUIT_12 is not present in siteID 100910
CIRCUIT_13 is not present in siteID 100910
CIRCUIT_14 is not present in siteID 100910
CIRCUIT_15 is not present in siteID 100910
CIRCUIT_17 is not present in siteID 100910
CIRCUIT_2 is not present in siteID 100910
CIRCUIT_3 is not present in siteID 100910
CIRCUIT_4 is not present in siteID 100910
CIRCUIT_5 is not present in siteID 100910
CIRCUIT_6 is not present in siteID 100910
CIRCUIT_7 is not present in siteID 100910
CIRCUIT_8 is not present in siteID 100910
CIRCUIT_9 is not present in siteID 100910
Mains is not present in siteID 100910
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230216.csv
CIRCUIT_1 is not present in siteID 10034
CIRCUIT_10 is not present in siteID 10034
CIRCUIT_11 is not present in siteID 10034
CIRCUIT_12 is not present in siteID 10034
CIRCUIT_13 is not present in siteID 10034
CIRCUIT_14 is not present in siteID 10034
CIRCUIT_16 is not present in siteID 10034
CIRCUIT_17 is not present in siteID 10034
CIRCUIT_18 is not present in siteID 10034
CIRCUIT_19 is not present in siteID 10034
CIRCUIT_20 is not present in siteID 10034
CIRCUIT_21 is not present in siteID 10034
CIRCUIT_22 is not present in siteID 10034
CIRCUIT_23 is not present in siteID 10034
CIRCUIT_24 is not present in siteID 10034
CIRCUIT_25 is not present in siteID 10034
CIRCUIT_3 is not present in siteID 10034
CIRCUIT_5 is not present in siteID 10034
CIRCUIT_7 is not present in siteID 10034
CIRCUIT_8 is not present in siteID 10034
CIRCUIT_9 is not present in siteID 10034
Mains is not present in siteID 10034
CIRCUIT_1 is not present in siteID 10054
CIRCUIT_10 is not present in siteID 10054
CIRCUIT_11 is not present in siteID 10054
CIRCUIT_13 is not present in siteID 10054
CIRCUIT_14 is not present in siteID 10054
CIRCUIT_16 is not present in siteID 10054
CIRCUIT_17 is not present in siteID 10054
CIRCUIT_18 is not present in siteID 10054
CIRCUIT_19 is not present in siteID 10054
CIRCUIT_20 is not present in siteID 10054
CIRCUIT_21 is not present in siteID 10054
CIRCUIT_22 is not present in siteID 10054
CIRCUIT_23 is not present in siteID 10054
CIRCUIT_24 is not present in siteID 10054
CIRCUIT_25 is not present in siteID 10054
CIRCUIT_26 is not present in siteID 10054
CIRCUIT_27 is not present in siteID 10054
CIRCUIT_3 is not present in siteID 10054
CIRCUIT_4 is not present in siteID 10054
CIRCUIT_5 is not present in siteID 10054
CIRCUIT_6 is not present in siteID 10054
CIRCUIT_7 is not present in siteID 10054
CIRCUIT_9 is not present in siteID 10054
Mains is not present in siteID 10054
CIRCUIT_1 is not present in siteID 10088
CIRCUIT_11 is not present in siteID 10088
CIRCUIT_12 is not present in siteID 10088
CIRCUIT_13 is not present in siteID 10088
CIRCUIT_14 is not present in siteID 10088
CIRCUIT_15 is not present in siteID 10088
CIRCUIT_17 is not present in siteID 10088
CIRCUIT_18 is not present in siteID 10088
CIRCUIT_19 is not present in siteID 10088
CIRCUIT_20 is not present in siteID 10088
CIRCUIT_21 is not present in siteID 10088
CIRCUIT_22 is not present in siteID 10088
CIRCUIT_23 is not present in siteID 10088
CIRCUIT_24 is not present in siteID 10088
CIRCUIT_25 is not present in siteID 10088
CIRCUIT_26 is not present in siteID 10088
CIRCUIT_27 is not present in siteID 10088
CIRCUIT_28 is not present in siteID 10088
CIRCUIT_5 is not present in siteID 10088
CIRCUIT_6 is not present in siteID 10088
CIRCUIT_7 is not present in siteID 10088
CIRCUIT_8 is not present in siteID 10088
Mains is not present in siteID 10088
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230217.csv
CIRCUIT_3 is not present in siteID 10088
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230218.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230219.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230220.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230221.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230222.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230223.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230224.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230225.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230226.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230227.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230228.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230301.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230302.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230303.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230304.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230305.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230306.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230307.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230308.csv
CIRCUIT_7 is not present in siteID 893
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230309.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230310.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230311.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230312.csv
CIRCUIT_12 is not present in siteID 269104
CIRCUIT_2 is not present in siteID 269104
CIRCUIT_29 is not present in siteID 269104
CIRCUIT_30 is not present in siteID 269104
CIRCUIT_4 is not present in siteID 269104
CIRCUIT_6 is not present in siteID 269104
CIRCUIT_8 is not present in siteID 269104
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230313.csv
CIRCUIT_1 is not present in siteID 269104
CIRCUIT_10 is not present in siteID 269104
CIRCUIT_11 is not present in siteID 269104
CIRCUIT_13 is not present in siteID 269104
CIRCUIT_14 is not present in siteID 269104
CIRCUIT_15 is not present in siteID 269104
CIRCUIT_16 is not present in siteID 269104
CIRCUIT_17 is not present in siteID 269104
CIRCUIT_18 is not present in siteID 269104
CIRCUIT_19 is not present in siteID 269104
CIRCUIT_20 is not present in siteID 269104
CIRCUIT_21 is not present in siteID 269104
CIRCUIT_3 is not present in siteID 269104
CIRCUIT_5 is not present in siteID 269104
CIRCUIT_7 is not present in siteID 269104
CIRCUIT_9 is not present in siteID 269104
Mains is not present in siteID 269104
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230314.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230315.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230316.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230317.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230318.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230319.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230320.csv
CIRCUIT_1 is not present in siteID 10023
CIRCUIT_10 is not present in siteID 10023
CIRCUIT_12 is not present in siteID 10023
CIRCUIT_13 is not present in siteID 10023
CIRCUIT_14 is not present in siteID 10023
CIRCUIT_15 is not present in siteID 10023
CIRCUIT_16 is not present in siteID 10023
CIRCUIT_2 is not present in siteID 10023
CIRCUIT_4 is not present in siteID 10023
CIRCUIT_6 is not present in siteID 10023
CIRCUIT_8 is not present in siteID 10023
Mains is not present in siteID 10023
CIRCUIT_1 is not present in siteID 10037
CIRCUIT_10 is not present in siteID 10037
CIRCUIT_11 is not present in siteID 10037
CIRCUIT_12 is not present in siteID 10037
CIRCUIT_13 is not present in siteID 10037
CIRCUIT_15 is not present in siteID 10037
CIRCUIT_2 is not present in siteID 10037
CIRCUIT_3 is not present in siteID 10037
CIRCUIT_5 is not present in siteID 10037
CIRCUIT_7 is not present in siteID 10037
CIRCUIT_9 is not present in siteID 10037
Mains is not present in siteID 10037
CIRCUIT_1 is not present in siteID 10039
CIRCUIT_10 is not present in siteID 10039
CIRCUIT_2 is not present in siteID 10039
CIRCUIT_3 is not present in siteID 10039
CIRCUIT_5 is not present in siteID 10039
CIRCUIT_6 is not present in siteID 10039
CIRCUIT_7 is not present in siteID 10039
CIRCUIT_8 is not present in siteID 10039
Mains is not present in siteID 10039
CIRCUIT_1 is not present in siteID 10118
CIRCUIT_10 is not present in siteID 10118
CIRCUIT_11 is not present in siteID 10118
CIRCUIT_13 is not present in siteID 10118
CIRCUIT_15 is not present in siteID 10118
CIRCUIT_17 is not present in siteID 10118
CIRCUIT_19 is not present in siteID 10118
CIRCUIT_2 is not present in siteID 10118
CIRCUIT_20 is not present in siteID 10118
CIRCUIT_21 is not present in siteID 10118
CIRCUIT_22 is not present in siteID 10118
CIRCUIT_23 is not present in siteID 10118
CIRCUIT_24 is not present in siteID 10118
CIRCUIT_25 is not present in siteID 10118
CIRCUIT_27 is not present in siteID 10118
CIRCUIT_3 is not present in siteID 10118
CIRCUIT_4 is not present in siteID 10118
CIRCUIT_5 is not present in siteID 10118
CIRCUIT_6 is not present in siteID 10118
CIRCUIT_7 is not present in siteID 10118
CIRCUIT_8 is not present in siteID 10118
CIRCUIT_9 is not present in siteID 10118
Mains is not present in siteID 10118
CIRCUIT_1 is not present in siteID 10125
CIRCUIT_10 is not present in siteID 10125
CIRCUIT_11 is not present in siteID 10125
CIRCUIT_12 is not present in siteID 10125
CIRCUIT_13 is not present in siteID 10125
CIRCUIT_15 is not present in siteID 10125
CIRCUIT_16 is not present in siteID 10125
CIRCUIT_17 is not present in siteID 10125
CIRCUIT_18 is not present in siteID 10125
CIRCUIT_19 is not present in siteID 10125
CIRCUIT_21 is not present in siteID 10125
CIRCUIT_22 is not present in siteID 10125
CIRCUIT_23 is not present in siteID 10125
CIRCUIT_25 is not present in siteID 10125
CIRCUIT_26 is not present in siteID 10125
CIRCUIT_3 is not present in siteID 10125
CIRCUIT_4 is not present in siteID 10125
CIRCUIT_5 is not present in siteID 10125
CIRCUIT_7 is not present in siteID 10125
CIRCUIT_9 is not present in siteID 10125
Mains is not present in siteID 10125
CIRCUIT_1 is not present in siteID 10239
CIRCUIT_11 is not present in siteID 10239
CIRCUIT_13 is not present in siteID 10239
CIRCUIT_15 is not present in siteID 10239
CIRCUIT_16 is not present in siteID 10239
CIRCUIT_17 is not present in siteID 10239
CIRCUIT_2 is not present in siteID 10239
CIRCUIT_3 is not present in siteID 10239
CIRCUIT_4 is not present in siteID 10239
CIRCUIT_6 is not present in siteID 10239
CIRCUIT_7 is not present in siteID 10239
CIRCUIT_8 is not present in siteID 10239
CIRCUIT_9 is not present in siteID 10239
Mains is not present in siteID 10239
CIRCUIT_1 is not present in siteID 10310
CIRCUIT_2 is not present in siteID 10310
CIRCUIT_3 is not present in siteID 10310
CIRCUIT_5 is not present in siteID 10310
CIRCUIT_7 is not present in siteID 10310
CIRCUIT_9 is not present in siteID 10310
Mains is not present in siteID 10310
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230321.csv
CIRCUIT_1 is not present in siteID 10073
CIRCUIT_10 is not present in siteID 10073
CIRCUIT_11 is not present in siteID 10073
CIRCUIT_2 is not present in siteID 10073
CIRCUIT_3 is not present in siteID 10073
CIRCUIT_5 is not present in siteID 10073
CIRCUIT_7 is not present in siteID 10073
CIRCUIT_9 is not present in siteID 10073
Mains is not present in siteID 10073
CIRCUIT_1 is not present in siteID 100210
CIRCUIT_10 is not present in siteID 100210
CIRCUIT_11 is not present in siteID 100210
CIRCUIT_2 is not present in siteID 100210
CIRCUIT_3 is not present in siteID 100210
CIRCUIT_5 is not present in siteID 100210
CIRCUIT_7 is not present in siteID 100210
CIRCUIT_8 is not present in siteID 100210
CIRCUIT_9 is not present in siteID 100210
Mains is not present in siteID 100210
CIRCUIT_1 is not present in siteID 101860
CIRCUIT_10 is not present in siteID 101860
CIRCUIT_11 is not present in siteID 101860
CIRCUIT_12 is not present in siteID 101860
CIRCUIT_13 is not present in siteID 101860
CIRCUIT_14 is not present in siteID 101860
CIRCUIT_15 is not present in siteID 101860
CIRCUIT_16 is not present in siteID 101860
CIRCUIT_17 is not present in siteID 101860
CIRCUIT_19 is not present in siteID 101860
CIRCUIT_2 is not present in siteID 101860
CIRCUIT_20 is not present in siteID 101860
CIRCUIT_22 is not present in siteID 101860
CIRCUIT_24 is not present in siteID 101860
CIRCUIT_26 is not present in siteID 101860
CIRCUIT_3 is not present in siteID 101860
CIRCUIT_4 is not present in siteID 101860
CIRCUIT_5 is not present in siteID 101860
CIRCUIT_6 is not present in siteID 101860
CIRCUIT_7 is not present in siteID 101860
CIRCUIT_8 is not present in siteID 101860
CIRCUIT_9 is not present in siteID 101860
Mains is not present in siteID 101860
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230322.csv
CIRCUIT_1 is not present in siteID 10014
CIRCUIT_10 is not present in siteID 10014
CIRCUIT_11 is not present in siteID 10014
CIRCUIT_3 is not present in siteID 10014
CIRCUIT_5 is not present in siteID 10014
CIRCUIT_7 is not present in siteID 10014
CIRCUIT_8 is not present in siteID 10014
Mains is not present in siteID 10014
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230323.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230324.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230325.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230326.csv
CIRCUIT_1 is not present in siteID 120622
CIRCUIT_10 is not present in siteID 120622
CIRCUIT_11 is not present in siteID 120622
CIRCUIT_12 is not present in siteID 120622
CIRCUIT_13 is not present in siteID 120622
CIRCUIT_14 is not present in siteID 120622
CIRCUIT_15 is not present in siteID 120622
CIRCUIT_16 is not present in siteID 120622
CIRCUIT_17 is not present in siteID 120622
CIRCUIT_18 is not present in siteID 120622
CIRCUIT_19 is not present in siteID 120622
CIRCUIT_2 is not present in siteID 120622
CIRCUIT_21 is not present in siteID 120622
CIRCUIT_23 is not present in siteID 120622
CIRCUIT_24 is not present in siteID 120622
CIRCUIT_25 is not present in siteID 120622
CIRCUIT_26 is not present in siteID 120622
CIRCUIT_27 is not present in siteID 120622
CIRCUIT_28 is not present in siteID 120622
CIRCUIT_3 is not present in siteID 120622
CIRCUIT_4 is not present in siteID 120622
CIRCUIT_5 is not present in siteID 120622
CIRCUIT_6 is not present in siteID 120622
CIRCUIT_8 is not present in siteID 120622
CIRCUIT_9 is not present in siteID 120622
Mains is not present in siteID 120622
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230327.csv
CIRCUIT_1 is not present in siteID 10866
CIRCUIT_10 is not present in siteID 10866
CIRCUIT_11 is not present in siteID 10866
CIRCUIT_12 is not present in siteID 10866
CIRCUIT_13 is not present in siteID 10866
CIRCUIT_14 is not present in siteID 10866
CIRCUIT_15 is not present in siteID 10866
CIRCUIT_17 is not present in siteID 10866
CIRCUIT_18 is not present in siteID 10866
CIRCUIT_19 is not present in siteID 10866
CIRCUIT_20 is not present in siteID 10866
CIRCUIT_21 is not present in siteID 10866
CIRCUIT_22 is not present in siteID 10866
CIRCUIT_23 is not present in siteID 10866
CIRCUIT_24 is not present in siteID 10866
CIRCUIT_25 is not present in siteID 10866
CIRCUIT_26 is not present in siteID 10866
CIRCUIT_27 is not present in siteID 10866
CIRCUIT_28 is not present in siteID 10866
CIRCUIT_3 is not present in siteID 10866
CIRCUIT_5 is not present in siteID 10866
CIRCUIT_6 is not present in siteID 10866
CIRCUIT_7 is not present in siteID 10866
CIRCUIT_8 is not present in siteID 10866
CIRCUIT_9 is not present in siteID 10866
Mains is not present in siteID 10866
CIRCUIT_1 is not present in siteID 397168
CIRCUIT_11 is not present in siteID 397168
CIRCUIT_12 is not present in siteID 397168
CIRCUIT_13 is not present in siteID 397168
CIRCUIT_15 is not present in siteID 397168
CIRCUIT_16 is not present in siteID 397168
CIRCUIT_17 is not present in siteID 397168
CIRCUIT_18 is not present in siteID 397168
CIRCUIT_19 is not present in siteID 397168
CIRCUIT_20 is not present in siteID 397168
CIRCUIT_22 is not present in siteID 397168
CIRCUIT_23 is not present in siteID 397168
CIRCUIT_24 is not present in siteID 397168
CIRCUIT_25 is not present in siteID 397168
CIRCUIT_3 is not present in siteID 397168
CIRCUIT_4 is not present in siteID 397168
CIRCUIT_5 is not present in siteID 397168
CIRCUIT_7 is not present in siteID 397168
CIRCUIT_9 is not present in siteID 397168
Mains is not present in siteID 397168
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230328.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230329.csv
CIRCUIT_1 is not present in siteID 7471
CIRCUIT_10 is not present in siteID 7471
CIRCUIT_11 is not present in siteID 7471
CIRCUIT_12 is not present in siteID 7471
CIRCUIT_14 is not present in siteID 7471
CIRCUIT_16 is not present in siteID 7471
CIRCUIT_18 is not present in siteID 7471
CIRCUIT_20 is not present in siteID 7471
CIRCUIT_21 is not present in siteID 7471
CIRCUIT_22 is not present in siteID 7471
CIRCUIT_3 is not present in siteID 7471
CIRCUIT_5 is not present in siteID 7471
CIRCUIT_7 is not present in siteID 7471
CIRCUIT_8 is not present in siteID 7471
CIRCUIT_9 is not present in siteID 7471
Mains is not present in siteID 7471
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230330.csv
CIRCUIT_1 is not present in siteID 10100
CIRCUIT_10 is not present in siteID 10100
CIRCUIT_12 is not present in siteID 10100
CIRCUIT_14 is not present in siteID 10100
CIRCUIT_15 is not present in siteID 10100
CIRCUIT_16 is not present in siteID 10100
CIRCUIT_17 is not present in siteID 10100
CIRCUIT_18 is not present in siteID 10100
CIRCUIT_19 is not present in siteID 10100
CIRCUIT_2 is not present in siteID 10100
CIRCUIT_20 is not present in siteID 10100
CIRCUIT_21 is not present in siteID 10100
CIRCUIT_22 is not present in siteID 10100
CIRCUIT_23 is not present in siteID 10100
CIRCUIT_25 is not present in siteID 10100
CIRCUIT_3 is not present in siteID 10100
CIRCUIT_4 is not present in siteID 10100
CIRCUIT_5 is not present in siteID 10100
CIRCUIT_6 is not present in siteID 10100
CIRCUIT_7 is not present in siteID 10100
CIRCUIT_8 is not present in siteID 10100
CIRCUIT_9 is not present in siteID 10100
Mains is not present in siteID 10100
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230331.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230401.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230402.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230403.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230404.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230405.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230406.csv
Mains is not present in siteID 308832
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230407.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230408.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230409.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230410.csv
CIRCUIT_1 is not present in siteID 4631
CIRCUIT_10 is not present in siteID 4631
CIRCUIT_12 is not present in siteID 4631
CIRCUIT_13 is not present in siteID 4631
CIRCUIT_14 is not present in siteID 4631
CIRCUIT_16 is not present in siteID 4631
CIRCUIT_17 is not present in siteID 4631
CIRCUIT_18 is not present in siteID 4631
CIRCUIT_19 is not present in siteID 4631
CIRCUIT_20 is not present in siteID 4631
CIRCUIT_3 is not present in siteID 4631
CIRCUIT_4 is not present in siteID 4631
CIRCUIT_5 is not present in siteID 4631
CIRCUIT_6 is not present in siteID 4631
CIRCUIT_7 is not present in siteID 4631
CIRCUIT_8 is not present in siteID 4631
CIRCUIT_9 is not present in siteID 4631
Mains is not present in siteID 4631
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230411.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230412.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230413.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230414.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230415.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230416.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230417.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230418.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230419.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230420.csv
CIRCUIT_1 is not present in siteID 4481
CIRCUIT_10 is not present in siteID 4481
CIRCUIT_11 is not present in siteID 4481
CIRCUIT_12 is not present in siteID 4481
CIRCUIT_14 is not present in siteID 4481
CIRCUIT_16 is not present in siteID 4481
CIRCUIT_18 is not present in siteID 4481
CIRCUIT_19 is not present in siteID 4481
CIRCUIT_20 is not present in siteID 4481
CIRCUIT_21 is not present in siteID 4481
CIRCUIT_23 is not present in siteID 4481
CIRCUIT_25 is not present in siteID 4481
CIRCUIT_3 is not present in siteID 4481
CIRCUIT_9 is not present in siteID 4481
Mains is not present in siteID 4481
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230421.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230422.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230423.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230424.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230425.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230426.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230427.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230428.csv
CIRCUIT_1 is not present in siteID 298259
CIRCUIT_11 is not present in siteID 298259
CIRCUIT_13 is not present in siteID 298259
CIRCUIT_14 is not present in siteID 298259
CIRCUIT_15 is not present in siteID 298259
CIRCUIT_16 is not present in siteID 298259
CIRCUIT_17 is not present in siteID 298259
CIRCUIT_18 is not present in siteID 298259
CIRCUIT_19 is not present in siteID 298259
CIRCUIT_2 is not present in siteID 298259
CIRCUIT_20 is not present in siteID 298259
CIRCUIT_21 is not present in siteID 298259
CIRCUIT_22 is not present in siteID 298259
CIRCUIT_3 is not present in siteID 298259
CIRCUIT_4 is not present in siteID 298259
CIRCUIT_5 is not present in siteID 298259
CIRCUIT_6 is not present in siteID 298259
CIRCUIT_7 is not present in siteID 298259
CIRCUIT_8 is not present in siteID 298259
CIRCUIT_9 is not present in siteID 298259
Mains is not present in siteID 298259
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230429.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230430.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230501.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230502.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230503.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230504.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230505.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230506.csv
CIRCUIT_18 is not present in siteID 101860
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230507.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230508.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230509.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230510.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230511.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230512.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230513.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230514.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230515.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230516.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230517.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230518.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230519.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230520.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230521.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230522.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230523.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230524.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230525.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230526.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230527.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230528.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230529.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230530.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230531.csv
CIRCUIT_1 is not present in siteID 254366
CIRCUIT_10 is not present in siteID 254366
CIRCUIT_12 is not present in siteID 254366
CIRCUIT_13 is not present in siteID 254366
CIRCUIT_14 is not present in siteID 254366
CIRCUIT_15 is not present in siteID 254366
CIRCUIT_16 is not present in siteID 254366
CIRCUIT_17 is not present in siteID 254366
CIRCUIT_3 is not present in siteID 254366
CIRCUIT_5 is not present in siteID 254366
CIRCUIT_6 is not present in siteID 254366
CIRCUIT_7 is not present in siteID 254366
CIRCUIT_8 is not present in siteID 254366
CIRCUIT_9 is not present in siteID 254366
Mains is not present in siteID 254366
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230601.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230602.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230603.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230604.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230605.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230606.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230607.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230608.csv
CIRCUIT_1 is not present in siteID 307473
CIRCUIT_10 is not present in siteID 307473
CIRCUIT_11 is not present in siteID 307473
CIRCUIT_13 is not present in siteID 307473
CIRCUIT_15 is not present in siteID 307473
CIRCUIT_17 is not present in siteID 307473
CIRCUIT_18 is not present in siteID 307473
CIRCUIT_19 is not present in siteID 307473
CIRCUIT_20 is not present in siteID 307473
CIRCUIT_21 is not present in siteID 307473
CIRCUIT_22 is not present in siteID 307473
CIRCUIT_23 is not present in siteID 307473
CIRCUIT_24 is not present in siteID 307473
CIRCUIT_25 is not present in siteID 307473
CIRCUIT_27 is not present in siteID 307473
CIRCUIT_3 is not present in siteID 307473
CIRCUIT_5 is not present in siteID 307473
CIRCUIT_7 is not present in siteID 307473
CIRCUIT_8 is not present in siteID 307473
CIRCUIT_9 is not present in siteID 307473
Mains is not present in siteID 307473
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230609.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230610.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230611.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230612.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230613.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230614.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230615.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230616.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230617.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230618.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230619.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230620.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230621.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230622.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230623.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230624.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230625.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230626.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230627.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230628.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230629.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230630.csv
CIRCUIT_1 is not present in siteID 510
CIRCUIT_10 is not present in siteID 510
CIRCUIT_11 is not present in siteID 510
CIRCUIT_12 is not present in siteID 510
CIRCUIT_13 is not present in siteID 510
CIRCUIT_14 is not present in siteID 510
CIRCUIT_15 is not present in siteID 510
CIRCUIT_17 is not present in siteID 510
CIRCUIT_18 is not present in siteID 510
CIRCUIT_19 is not present in siteID 510
CIRCUIT_20 is not present in siteID 510
CIRCUIT_21 is not present in siteID 510
CIRCUIT_22 is not present in siteID 510
CIRCUIT_23 is not present in siteID 510
CIRCUIT_24 is not present in siteID 510
CIRCUIT_25 is not present in siteID 510
CIRCUIT_26 is not present in siteID 510
CIRCUIT_27 is not present in siteID 510
CIRCUIT_28 is not present in siteID 510
CIRCUIT_3 is not present in siteID 510
CIRCUIT_5 is not present in siteID 510
CIRCUIT_6 is not present in siteID 510
CIRCUIT_7 is not present in siteID 510
CIRCUIT_8 is not present in siteID 510
Mains is not present in siteID 510
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230701.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230702.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230703.csv
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230704.csv
CIRCUIT_10 is not present in siteID 374781
CIRCUIT_12 is not present in siteID 374781
CIRCUIT_14 is not present in siteID 374781
CIRCUIT_16 is not present in siteID 374781
CIRCUIT_18 is not present in siteID 374781
CIRCUIT_2 is not present in siteID 374781
CIRCUIT_20 is not present in siteID 374781
CIRCUIT_23 is not present in siteID 374781
CIRCUIT_24 is not present in siteID 374781
CIRCUIT_29 is not present in siteID 374781
CIRCUIT_4 is not present in siteID 374781
CIRCUIT_6 is not present in siteID 374781
CIRCUIT_8 is not present in siteID 374781
Done with ..\2023-Full_v8.1\2023\power\power-fifteen-20230705.csv
CIRCUIT_1 is not present in siteID 374781
CIRCUIT_11 is not present in siteID 374781
CIRCUIT_13 is not present in siteID 374781
CIRCUIT_15 is not present in siteID 374781
CIRCUIT_17 is not present in siteID 374781
CIRCUIT_19 is not present in siteID 374781
CIRCUIT_21 is not present in siteID 374781
CIRCUIT_22 is not present in siteID 374781
CIRCUIT_25 is not present in siteID 374781
CIRCUIT_26 is not present in siteID 374781
CIRCUIT_3 is not present in siteID 374781
CIRCUIT_5 is not present in siteID 374781
CIRCUIT_7 is not present in siteID 374781
CIRCUIT_9 is not present in siteID 374781
Mains is not present in siteID 374781

CIRCUIT_27 is not present in siteID 374781
Mains is not present in siteID 303645
Mains_left is not present in siteID 197303
CIRCUIT_1 is not present in siteID 241484
CIRCUIT_10 is not present in siteID 241484
CIRCUIT_11 is not present in siteID 241484
CIRCUIT_12 is not present in siteID 241484
CIRCUIT_13 is not present in siteID 241484
CIRCUIT_14 is not present in siteID 241484
CIRCUIT_15 is not present in siteID 241484
CIRCUIT_17 is not present in siteID 241484
CIRCUIT_2 is not present in siteID 241484
CIRCUIT_3 is not present in siteID 241484
CIRCUIT_4 is not present in siteID 241484
CIRCUIT_5 is not present in siteID 241484
CIRCUIT_6 is not present in siteID 241484
CIRCUIT_8 is not present in siteID 241484
CIRCUIT_1 is not present in siteID 7481
CIRCUIT_10 is not present in siteID 7481
CIRCUIT_11 is not present in siteID 7481
CIRCUIT_12 is not present in siteID 7481
CIRCUIT_14 is not present in siteID 7481
CIRCUIT_16 is not present in siteID 7481
CIRCUIT_18 is not present in siteID 7481
CIRCUIT_19 is not present in siteID 7481
CIRCUIT_20 is not present in siteID 7481
CIRCUIT_21 is not present in siteID 7481
CIRCUIT_3 is not present in siteID 7481
CIRCUIT_5 is not present in siteID 7481
CIRCUIT_7 is not present in siteID 7481
CIRCUIT_8 is not present in siteID 7481
CIRCUIT_9 is not present in siteID 7481
Mains is not present in siteID 7481
CIRCUIT_1 is not present in siteID 292998
CIRCUIT_10 is not present in siteID 292998
CIRCUIT_11 is not present in siteID 292998
CIRCUIT_12 is not present in siteID 292998
CIRCUIT_13 is not present in siteID 292998
CIRCUIT_15 is not present in siteID 292998
CIRCUIT_16 is not present in siteID 292998
CIRCUIT_17 is not present in siteID 292998
CIRCUIT_18 is not present in siteID 292998
CIRCUIT_19 is not present in siteID 292998
CIRCUIT_20 is not present in siteID 292998
CIRCUIT_21 is not present in siteID 292998
CIRCUIT_22 is not present in siteID 292998
CIRCUIT_23 is not present in siteID 292998
CIRCUIT_25 is not present in siteID 292998
CIRCUIT_27 is not present in siteID 292998
CIRCUIT_5 is not present in siteID 292998
CIRCUIT_6 is not present in siteID 292998
CIRCUIT_7 is not present in siteID 292998
CIRCUIT_8 is not present in siteID 292998
CIRCUIT_9 is not present in siteID 292998


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
