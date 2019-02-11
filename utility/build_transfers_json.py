# This script builds a JSON file that holds all the relevant information for transfer points
import sqlite3
import json
import itertools

db = "../thesis_data.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

# Build this into a python dictionary first
data = dict()
daily_count = 60

# First, some metadata
data['network'] = "Calgary Transit"
data['details'] = "Data from October-December, 2015"

# We're going to create three specific hubs.
data['hubs'] = []

# Each hub has it's own set of information
hub = dict()
hub['name'] = "University - Craigie Hall"
hub['transfer_time'] = 1
hub['stops'] = []


stop_ids = [1756]
sum_lat = 0.0
sum_lon = 0.0
# Each stop has its own set of information
for stop_id in stop_ids:
    sql = "SELECT stop_code, stop_lat, stop_lon, stop_name FROM stop WHERE stop_id = ?"
    cur.execute(sql, (stop_id,))
    r = cur.fetchone()
    stop = dict()
    stop['stop_code'] = int(r[0])
    stop['stop_id'] = stop_id
    stop['stop_lat'] = float(r[1])
    sum_lat += stop['stop_lat']
    stop['stop_lon'] = float(r[2])
    sum_lon += stop['stop_lon']
    stop['stop_name'] = str(r[3])
    hub['stops'].append(stop)

hub['hub_lat'] = sum_lat / len(stop_ids)
hub['hub_lon'] = sum_lon / len(stop_ids)
hub['transfer_rate'] = 0.2

# Now we grab a set of unique bus routes
hub['routes'] = []
sql = """
SELECT model_data.route_id, stop_seq, nb, na, theta, route_number, route_name
FROM model_data
JOIN route on route.route_id = model_data.route_id
WHERE config_id = 1 AND stop_id IN ({})""".format(",".join([str(i) for i in stop_ids]))
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
    route['daily_count'] = daily_count
    hub['routes'].append(route)

total_nb = sum([r[2] for r in routes])
total_na = sum([r[3] for r in routes])
total_transfer = total_nb*hub['transfer_rate']

hub['transfers'] = []

for pair in itertools.permutations(routes, 2):
    transfer = dict()
    from_id = pair[0][0]
    to_id = pair[1][0]
    na = pair[0][3]
    nb = pair[1][2]
    transfer_frac = (na + nb)/(total_nb + total_na)
    transfer['from_id'] = from_id
    transfer['to_id'] = to_id
    transfer['daily_transfer'] = transfer_frac * total_transfer * daily_count
    hub['transfers'].append(transfer)

data['hubs'].append(hub)

with open("transfers.json", "w") as outfile:
    json.dump(data, outfile, indent=4)
