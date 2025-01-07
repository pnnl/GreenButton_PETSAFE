import pymysql
# TODO: document setup


# Open a connection to the database.
def connectDB():
    # TODO: PUT THESE IN ENVIRONMENT VARIABLES.
    conn = pymysql.connect(
        host='localhost',
        #user='string of user',
        #password='string of password goes here',
        db='mydatabase',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

def insertMySQL(record):
    pass
    # conn.commit()

def importFromJSON(filepath):
    pass
    # json_data = pymysql.escape_string(json_data)
    # conn.commit()

def readBuildingMetadata(building_id, conn):
    pass

def closeConn(conn):
    try:
        conn.close()
    except:
        print("Cannot close connection. Does connection exist?")