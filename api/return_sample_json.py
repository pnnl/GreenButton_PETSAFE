from json import load

def read_json(filepath):
    jsonfile = open(filepath, "r")
    jsondata = load(jsonfile)
    jsonfile.close()
    return jsondata