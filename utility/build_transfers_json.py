# This script builds a JSON file that holds all the relevant information for trasnfer points
import sqlite3
import json

db = "../thesis_data.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

# Build this into a python dictionary first
data = dict()

# First, some metadata
data['network'] = "Calgary Transit"
data['details'] = "Data from October-December, 2015"

# We're going to create three specific hubs.
data['hubs'] = []

# Each hub has it's own set of information
hub = dict()
hub['name'] = "University - Craigie Hall"
hub['stops'] = []

# Each stop has its own set of information
for stop_id in [1756]:
    sql = "SELECT stop_code, stop_lat, stop_lon, stop_name FROM stop WHERE stop_id = ?"
    cur.execute(sql, (stop_id,))
    r = cur.fetchone()
    stop = dict()
    stop['stop_code'] = int(r[0])
    stop['stop_id'] = stop_id
    stop['stop_lat'] = float(r[1])
    stop['stop_lon'] = float(r[2])
    stop['stop_name'] = str(r[3])
    hub['stops'].append(stop)

data['hubs'].append(hub)

with open("transfers.json", "w") as outfile:
    json.dump(data, outfile)
