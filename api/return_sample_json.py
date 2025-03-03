from typing import Optional
from datetime import datetime as dt
import pandas as pd
from flask import Response

def read_json(file):
    jsonfile = open(file, "r")
    jsondata = jsonfile.readlines()
    jsonfile.close()
    return jsondata