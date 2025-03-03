from json import load, dumps

def read_json(filepath):
    try:
        jsonfile = open(filepath, "r")
        jsondata = load(jsonfile)
        jsonfile.close()
    except Exception as ex:
        print("Cannot retrieve JSON from file:", ex)
        jsondata = {"Error": "Cannot retrieve JSON from file"}
        jsondata = dumps(jsondata)
    return jsondata