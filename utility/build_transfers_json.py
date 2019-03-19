# This script builds a JSON file that holds all the relevant information for trasnfer points
import sqlite3
import json

db = "../thesis_data.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

# This is used to populate everything else
hub_info = [
    ['University of Calgary - Craigie Hall', [1756]],
    ['Mount Royal University', [254, 270]],
    ['Heritage LRT Station', [262]],
    ['McKnight-Westwinds LRT Station', [5507]],
    ['Downtown - 6/5 Ave SW at 3/4 St SW', [1492, 1493, 4237, 5749, 1794, 4446, 4447, 4615, 4891, 3157]],
    ['78 Avenue Terminal', [893, 1008, 1425, 1523, 1623, 2470, 4936, 4978]]
]
# Build this into a python dictionary first
data = dict()

# First, some metadata
data['network'] = "Calgary Transit"
data['details'] = "Data from October-December, 2015"

# We're going to create multiple hubs
data['hubs'] = []

for h in hub_info:
    # Each hub has it's own set of information
    hub = dict()
    hub['name'] = h[0]
    hub['transfer_time'] = 5
    hub['stops'] = []
    stop_ids = h[1]
    lats = []
    lons = []
    # Each stop has its own set of information
    for stop_id in stop_ids:
        sql = "SELECT stop_code, stop_lat, stop_lon, stop_name FROM stop WHERE stop_id = ?"
        cur.execute(sql, (stop_id,))
        r = cur.fetchone()
        stop = dict()
        stop['stop_code'] = int(r[0])
        stop['stop_id'] = stop_id
        stop['stop_lat'] = float(r[1])
        stop['stop_lon'] = float(r[2])
        stop['stop_name'] = str(r[3])
        lats.append(float(r[1]))
        lons.append(float(r[2]))
        hub['stops'].append(stop)

    # Now we grab a set of unique bus routes
    hub['routes'] = []
    sql = """
    SELECT model_data.route_id, stop_seq, nb, na, theta, route_number, route_name
    FROM model_data
    JOIN route on route.route_id = model_data.route_id
    WHERE config_id = 1 AND stop_id IN ({})""".format(",".join([str(i) for i in stop_ids]))
    print(sql)
    cur.execute(sql)
    routes = cur.fetchall()
    for r in routes:
        route = dict()
        route['route_id'] = int(r[0])
        route['stop_seq'] = int(r[1])
        route['nb'] = float(r[2])
        route['na'] = float(r[3])
        route['theta'] = float(r[4])
        route['route_number'] = int(r[5])
        route['route_name'] = r[6]
        hub['routes'].append(route)

    hub['hub_lat'] = sum(lats)/len(lats)
    hub['hub_lon'] = sum(lons)/len(lons)
    data['hubs'].append(hub)

with open("transfers.json", "w") as outfile:
    json.dump(data, outfile, indent=4)
