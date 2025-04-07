#import os
#import csv
import datetime
from commonDB import DBConn
#from commonDB import helpers as h
import pickle
import time
import pandas as pd
import numpy as np
def convertTime(date_str):
    date_format = "%Y-%m-%d"
    # Convert string to datetime object
    dt = datetime.datetime.strptime(date_str, date_format)
    # Convert datetime to epoch
    epoch_time = int(time.mktime(dt.timetuple()))
    return epoch_time

# Retrieves entries where the circuit_label_type_id is in [ids]
def getEntriesOfType(
        conn, # Database connection
        ids: list # The list of type ids to match for circuit type
):
    # fstring is injection vector; parameterized mitigates that
    query = "SELECT *  FROM LABELS WHERE LABELS.circuit_label_type_id IN (?)"
    ids = str(tuple(ids)) # format for parameterized query
    results = conn.execute(query, ids)
    x = results.fetchall()
    allEntries = []
    for xi in x:
        entry = {"ee_site_id":xi[0],"point_id":xi[1],"regname":xi[2],"circuit_label_type_id":xi[3],"circuit_label_type_desc":xi[4],"circuit_label":xi[5],"equipment_type_desc":xi[6]}
        print(entry["ee_site_id"], entry["circuit_label_type_desc"])
        allEntries.extend([entry])
    return allEntries

#unixepoch
#select *,datetime(timestamp, 'unixepoch') ,unixepoch("2021-01-01") from POwER where  timestamp >unixepoch("2021-01-02") limit 10
def pullRecords(database):
    conn = DBConn.create_connection(database)
    with conn:
        if 1==1:
            res = conn.execute("""
        select LABELS.point_id,*,datetime(day_zero_dt, 'unixepoch', 'localtime') as start_ts
        FROM 
        LABELS where (LABELS.circuit_label_type_id=15 or LABELS.circuit_label_type_id=16)
        and LABELS.day_zero_dt <unixepoch("2021-01-01") order by day_zero_dt   ;
        """)
            x=res.fetchall()
            points=[pt[0] for pt in x]

            start=convertTime("2021-01-01")
            end=convertTime("2022-01-01")
            print(start,end)
            ts=[x for x in range(start,end,900)]
            df1 = pd.DataFrame({
                'timestamp': ts
            })

            for p in points:
                colName=str(p)
                params = str(p)
                query = 'Select timestamp,P  FROM POWER WHERE POWER.point_id=? AND POWER.timestamp >=unixepoch("2021-01-01")+3600*8 AND POWER.timestamp < unixepoch("2022-01-01")+3600*8 ;'
                res = conn.execute(query, params)
                allPs=res.fetchall()
                if len(allPs)==0:
                    print("No data found with pointID", colName)
                    continue
                #print(allPs[0][0],allPs[-1][0])
                recorder_records=np.array(allPs)
                df2 = pd.DataFrame({
                'timestamp': recorder_records[:,0],
                colName:recorder_records[:,1]
                })

                df1 = pd.merge(df1, df2, on='timestamp', how='left')
                #df1[colName] = df1[colName].fillna(0)
                print("Added readings for point_id",colName,"Count:",len(recorder_records))
            df1.to_pickle('ALL_READINGS.pkl')
#No data found with pointID 26566
#No data found with pointID 26192
#No data found with pointID 25415
#No data found with pointID 26418
#No data found with pointID 25921
#No data found with pointID 26639
#No data found with pointID 25542
#No data found with pointID 26093
#No data found with pointID 33829


        if 1==2:
            res = conn.execute("""
        SELECT * FROM POWERS WHERE   
        
        INNER JOIN POWER 
        ON POWER.ee_site_id = LABELS.ee_site_id AND POWER.regname = LABELS.regname 
        WHERE LABELS.circuit_label_type_id=15
        limit 10;
            """)

        if 1==2:
           #############
            ###Mains With Solar, Mains Without Solar, Mains
            allMainEntries = getEntriesOfType([15, 16], conn)

            #############
            ###Electric Baseboard Heaters, Electric Furnace
            allHeaterEntries = getEntriesOfType([7, 8, 28], conn)

            #################
            ###Electric Vehicle Chargers
            allEVEntries = getEntriesOfType([10], conn)
            #################

            

            for entry in allMainEntries:
                site_id=entry["ee_site_id"]
                command=f'SELECT * FROM POWER WHERE ee_site_id={site_id} and regname = \'{entry["regname"]}\' order by timestamp;'
                res = conn.execute(command)
                main_recorder=res.fetchall()

                heater_recorders=[]
                heater_recorders_labels=[]
                for heater in allHeaterEntries:
                    if heater["ee_site_id"]==site_id:
                        command=f'SELECT * FROM POWER WHERE ee_site_id={entry["ee_site_id"]} and regname = \'{heater["regname"]}\' order by timestamp;'
                        res = conn.execute(command)
                        heater_recorder=res.fetchall()
                        heater_recorders.extend([heater_recorder])
                        heater_recorders_labels.extend([heater["circuit_label_type_desc"]+"_"+str(heater["point_id"])])
                
                ev_recorder=[]
                for ev in allEVEntries:
                    if ev["ee_site_id"]==site_id:
                        command=f'SELECT * FROM POWER WHERE ee_site_id={entry["ee_site_id"]} and regname = \'{ev["regname"]}\' order by timestamp;'
                        res = conn.execute(command)
                        ev_recorder=res.fetchall()
                        
                
                dataDump={"main_recorder":main_recorder,"heater_recorders":heater_recorders,"heater_recorders_labels":heater_recorders_labels,"ev_recorder":ev_recorder}
                file = open("pulledRecords"+"\\"+str(site_id)+".pkl", 'wb')

                # dump information to that file
                pickle.dump(dataDump, file)

                # close the file
                file.close()


                '''
                for ix in range(len (main_recorder)):
                    base=main_recorder[ix]
                    extra=[]
                    for heater in heater_recorders:
                        if (heater[ix]==base[2]):
                            extra.extend([heater[ix]])
                        else:
                            #check how far
                            if base[2]>heater[ix]:
                                print (base[2],heater[ix])
                                pass
                            else:
                                print (base[2],heater[ix])
                                pass

                    print (xi,datetime.datetime.fromtimestamp(xi[2]))
                '''
#loadDataLabels("records.db")
  
if __name__ == "__main__":
    pullRecords("records.db")