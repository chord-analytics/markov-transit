import sqlite3

class Network:

    def __init__(self, db_file, route_file):
        db = sqlite3.connect(db_file)
        routes = pd.read_csv(route_file)


class Route:

    def __init(self, route_id, db):
        cur = db.cursor()
        cur.execute("SELECT ")