# Encrypting all 5 years of data for a single building of size 5 would require querying 
# and encrypting 876,200 records, with one record representing 15 minutes of electrical 
# readings. With each record possessing three sensitive columns, thus requiring an 
# average of 63.6 milliseconds to encrypt without parallelization, this would take 
# approximately 15.5 hours without optimization. This does not include the overheads 
# incurred during aggregation, nor does it account for overheads from querying the 
# database for these metering sites

import plotly.express as plt
import plotly.graph_objects as go
import pandas as pd

points = pd.DataFrame()

def add_record(count, time, colcount, sitecount):
    global points
    record = pd.DataFrame(data={"Record Count Per Site": [count], "Average Time to Encrypt (seconds)": [time], \
                                "Sensitive Columns": [colcount], "Sites in Building": [sitecount]})
    points = pd.concat([points, record])

"""
# Single sensitive column, one site
add_record(1, 0.021, 1, 1) # One record
add_record(96, 2.016, 1, 1) # One day at 15min resolution
add_record(2880, 60.48, 1, 1) # One month at 15min resolution
add_record(35040, 735.84, 1, 1) # One year at 15min resolution
add_record(175200, 3679.221, 1, 1) # Five years at 15min resolution

# Single sensitive column, five sites
add_record(1, 0.105, 1, 5) # One record
add_record(96, 10.08, 1, 5) # One day at 15min resolution
add_record(2880, 302.4, 1, 5) # One month at 15min resolution
add_record(35040, 3679.2, 1, 5) # One year at 15min resolution
add_record(175200, 18396.105, 1, 5) # Five years at 15min resolution
"""

# Three sensitive columns, one site
add_record(1, 0.0636, 3, 1) # One record
add_record(96, 6.1056, 3, 1) # One day at 15min resolution
add_record(2880, 183.168, 3, 1) # One month at 15min resolution
add_record(35040, 2228.544, 3, 1) # One year at 15min resolution
add_record(175200, 11142.7836, 3, 1) # Five years at 15min resolution

# Three sensitive columns, three sites
add_record(1, 0.1908, 3, 3) # One record
add_record(96, 18.3168, 3, 3) # One day at 15min resolution
add_record(2880, 549.504, 3, 3) # One month at 15min resolution
add_record(35040, 6685.632, 3, 3) # One year at 15min resolution
add_record(175200, 33428.3508, 3, 3) # Five years at 15min resolution

# Three sensitive columns, five sites
add_record(1, 0.318, 3, 5) # One record
add_record(96, 30.528, 3, 5) # One day at 15min resolution
add_record(2880, 915.84, 3, 5) # One month at 15min resolution
add_record(35040, 11142.72, 3, 5) # One year at 15min resolution
add_record(175200, 55713.918, 3, 5) # Five years at 15min resolution

# Three sensitive columns, eight sites
add_record(1, 0.5088, 3, 8) # One record
add_record(96, 48.8448, 3, 8) # One day at 15min resolution
add_record(2880, 1465.344, 3, 8) # One month at 15min resolution
add_record(35040, 17828.352, 3, 8) # One year at 15min resolution
add_record(175200, 89142.2688, 3, 8) # Five years at 15min resolution

fig = plt.line(points, x="Record Count Per Site", \
               y="Average Time to Encrypt (seconds)", color="Sites in Building", title="Approximate Encryption Time without Overheads")
fig = fig.update_layout(font_size= 24, font_family="Times New Roman")
fig.show()