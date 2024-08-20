import os
import csv
import datetime
from commonDB import DBConn
from commonDB import helpers as h
import pickle

#unixepoch
#select *,datetime(timestamp, 'unixepoch') ,unixepoch("2021-01-01") from POwER where  timestamp >unixepoch("2021-01-02") limit 10
def pullRecords(database):
    conn = DBConn.create_connection(database)
    with conn:
        if 1==2:
            res = conn.execute("""
        SELECT * FROM POWER  
        INNER JOIN LABELS 
        ON POWER.ee_site_id = LABELS.ee_site_id AND POWER.regname = LABELS.regname 
        WHERE LABELS.circuit_label_type_id=15
        limit 10;
        """)
        if 1==2:
            res = conn.execute("""
        SELECT * FROM LABELS  
        
        INNER JOIN POWER 
        ON POWER.ee_site_id = LABELS.ee_site_id AND POWER.regname = LABELS.regname 
        WHERE LABELS.circuit_label_type_id=15
        limit 10;
            """)

        if 1==1:
            ###Mains With Solar, Mains Without Solar, Mains
            res = conn.execute("""
            SELECT *  FROM LABELS WHERE LABELS.circuit_label_type_id=15 OR LABELS.circuit_label_type_id=16;
            """)
            x=res.fetchall()
            allMainEntries=[]
            for xi in x:
                entry={"ee_site_id":xi[0],"point_id":xi[1],"regname":xi[2],"circuit_label_type_id":xi[3],"circuit_label_type_desc":xi[4],"circuit_label":xi[5],"equipment_type_desc":xi[6]}
                print(entry["ee_site_id"],entry["circuit_label_type_desc"])
                allMainEntries.extend([entry])
            #############
            ###Electric Baseboard Heaters, Electric Furnace
            res = conn.execute("""
            SELECT *  FROM LABELS WHERE LABELS.circuit_label_type_id=7 OR LABELS.circuit_label_type_id=8 OR LABELS.circuit_label_type_id=28;
            """)
            x=res.fetchall()
            allHeaterEntries=[]
            for xi in x:
                entry={"ee_site_id":xi[0],"point_id":xi[1],"regname":xi[2],"circuit_label_type_id":xi[3],"circuit_label_type_desc":xi[4],"circuit_label":xi[5],"equipment_type_desc":xi[6]}
                print(entry["ee_site_id"],entry["circuit_label_type_desc"])
                allHeaterEntries.extend([entry])
            #################
            ###Electric Vehicle Chargers
            res = conn.execute("""
            SELECT *  FROM LABELS WHERE LABELS.circuit_label_type_id=10;
            """)
            x=res.fetchall()
            allEVEntries=[]
            for xi in x:
                entry={"ee_site_id":xi[0],"point_id":xi[1],"regname":xi[2],"circuit_label_type_id":xi[3],"circuit_label_type_desc":xi[4],"circuit_label":xi[5],"equipment_type_desc":xi[6]}
                print(entry["ee_site_id"],entry["circuit_label_type_desc"])
                allEVEntries.extend([entry])
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
  

pullRecords("records.db")