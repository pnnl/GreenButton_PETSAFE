import datetime
import sqlite3

# Apologies for the sparse comments- I got this code uncommented and did my best to
# document what's going on. It's my best guess, so take it all with a grain of salt.

class DBConn:

    @staticmethod 
    def drop_TABLE(db_file,table_name):
        connection_obj = DBConn.create_connection(db_file)

        # cursor object
        cursor_obj = connection_obj.cursor()
        
        # Drop the table_name table if already exists.
        cursor_obj.execute("DROP TABLE IF EXISTS " + table_name)
        cursor_obj.close()


    @staticmethod
    def create_LablesTABLE(db_file):
        ''' Table structure:
    0 =    '"ee_site_id"'
    1 =    '"point_id"'
    2 =    '"regname"'
    3 =    '"circuit_label_type_id"'
    4 =    '"circuit_label_type_desc"'
    5 =    '"circuit_label"'
    6 =    '"equipment_type_desc"'
    7 =    '"day_zero_dt"'
    '''
        # Creating table
        table_descriptor = """ CREATE TABLE LABELS (
                    ee_site_id INTEGER,
                    point_id PRIMARY KEY UNIQUE,
                    regname CHAR(32) NOT NULL,
                    circuit_label_type_id INTEGER,
                    circuit_label_type_desc CHAR(32),
                    circuit_label CHAR(32),
                    equipment_type_desc CHAR(32),
                    day_zero_dt INT

                ); """
        
        DBConn.create_TABLE(db_file,"LABELS",table_descriptor) 

    @staticmethod
    def create_POWERTABLE(db_file):
        #regname CHAR(32) NOT NULL,
        table_descriptor = """ CREATE TABLE POWER (
                    ee_site_id INTEGER,
                    point_id INTEGER,
                    timestamp INTEGER,
                    duration INTEGER,
                    P REAL ,
                    Q REAL  ,
                    PF REAL,
                    FOREIGN KEY(point_id) REFERENCES LABELS(point_id)
                ); """
        DBConn.create_TABLE(db_file,"POWER",table_descriptor) 
        DBConn.create_INDEX(db_file,"POWER","point_id") 
    


    @staticmethod 
    def create_TABLE(db_file,table_name,table_descriptor):
        connection_obj = DBConn.create_connection(db_file)

        # cursor object
        cursor_obj = connection_obj.cursor()
        
        # Drop the table_name table if already exists.
        # TODO: I don't see any safeguards against data loss.
        cursor_obj.execute("DROP TABLE IF EXISTS " + table_name)
            
        cursor_obj.execute(table_descriptor)
        cursor_obj.close()
        print("Table: " + table_name + " has been created")

    @staticmethod 
    def create_INDEX(db_file,table_name,col_to_index):
        connection_obj = DBConn.create_connection(db_file)

        # cursor object
        cursor_obj = connection_obj.cursor()
        
        # Create index on col_to_index
        statement = "CREATE INDEX IF NOT EXISTS " + col_to_index + " ON " + table_name + "(" + col_to_index + ")"
        cursor_obj.execute(statement)
        print("Index " + col_to_index + "created on " + table_name)
        cursor_obj.close()


    @staticmethod 
    def create_connection(db_file):
        """ create a database connection to the SQLite database
            specified by db_file
        :param db_file: database file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file, cached_statements=100, isolation_level="DEFERRED")
            cursor_obj = conn.cursor()
            # Enable foreign keys
            cursor_obj.execute("PRAGMA foreign_keys = ON;") # Enforce foreign key constraints
            cursor_obj.execute("PRAGMA journal_mode = WAL;") # Write-ahead log, improves performance
            cursor_obj.execute("PRAGMA synchronous = normal;") # Asks WAL to wait for FSYNC, but readers don't have to wait
            # Note on nmap: I/O errors need to be caught by the application and vaccuum may fail silently
            cursor_obj.execute("PRAGMA mmap_size = 15000000000;") # memory mapping, improves performance
            cursor_obj.execute("PRAGMA threads = 3;") # enables threads to assist with queries
            cursor_obj.execute("PRAGMA analysis_limit = 400;") # reduces duration of pragma optimize (run when closing)
            cursor_obj.close()
        except Exception as e:
            print(e)
        return conn
    
    def close_connection(connection):
        cursor_obj = connection.cursor()
        cursor_obj.execute("PRAGMA optimize;") # Collects statistics that speed up queries
        cursor_obj.close()
        connection.close()



    @staticmethod 
    def insert_PowerRecords(conn, records):
        sql = ''' INSERT INTO POWER(ee_site_id,point_id,timestamp,duration,P,Q,PF)
                VALUES(?,?,?,?,?,?,?) '''
        cur = conn.cursor()
        #cur.execute(sql, task)
        cur.executemany(sql, records)
        conn.commit()
        return cur.lastrowid
    
    @staticmethod 
    def insert_LabelRecords(conn, records):

        sql = ''' INSERT INTO LABELS(ee_site_id,point_id,regname,circuit_label_type_id,circuit_label_type_desc,circuit_label,equipment_type_desc,day_zero_dt)
                VALUES(?,?,?,?,?,?,?,?) '''
        cur = conn.cursor()
        #cur.execute(sql, task)
        cur.executemany(sql, records)
        conn.commit()
        return cur.lastrowid
    
    @staticmethod 
    def query(conn, sql):
        cur = conn.cursor()
        try:
            res=cur.execute(sql)
            x=res.fetchall()
        except sqlite3.OperationalError as error:
            print(error)
            x = None
        cur.close()
        return x
    

class helpers:
    def getTime(aStr):
        x=datetime.datetime.strptime(aStr, '%Y-%m-%d %H:%M:%S')
        assert x.strftime('%Y-%m-%d %H:%M:%S')==aStr, "Time mismatch"
        return int(x.timestamp())

    def getValue(aStr):
        if aStr=="NA":
            return None
        else:
            return float(aStr)
    
    def escapeStr(aStr):
        aStr=str(aStr).replace("\"","")
        return aStr