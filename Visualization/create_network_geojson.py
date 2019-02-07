import geojson as gj
import os
import sqlite3
import csv

routes_file = r"test_routes.csv"
db_file = r"../thesis_data.db"
outfolder = "shapes"
db = sqlite3.connect(db_file)
cur = db.cursor()
shapes = []
stops = []
stop_ids = []

# First, we assemble the route shapes together.
with open(routes_file) as route_file:
    routes = csv.reader(route_file)
    next(routes)
    for route in routes:
        route_id = route[0]
        route_name = route[1]
        shape_id = route[2]
        # Grab the shape data from the GTFS feed.
        cur.execute("SELECT shape_pt_lon, shape_pt_lat FROM gtfs_shapes WHERE shape_id = ? ORDER BY shape_pt_sequence",
                    (shape_id,))
        shape = cur.fetchall()
        shapes.append(gj.Feature(geometry=gj.LineString(shape), properties={"route_id": route_id, "route_name": route_name}))

        # Now, let's grab all the stops visited by these routes
        cur.execute("""
        select stop.stop_id, stop.stop_lon, stop.stop_lat, stop.stop_name, stop_code from route_stop
        JOIN stop ON stop.stop_id = route_stop.stop_id
        WHERE route_id = ? 
        ORDER BY route_stop.stop_seq""", (route_id,))
        res = cur.fetchall()
        for s in res:
            if s[0] not in stop_ids:
                stops.append(gj.Feature(geometry=gj.Point([s[1], s[2]]), properties={"stop_name": s[3], "stop_code": s[4]}))

with open(os.path.join(outfolder, "network.geojson"), 'w') as outfile:
    gj.dump(gj.FeatureCollection(shapes), outfile)

with open(os.path.join(outfolder, "stops.geojson"), 'w') as outfile:
    gj.dump(gj.FeatureCollection(stops), outfile)