"""
This script fixes all the 'NA' values that are created when the make_route_in_db.py script is run.
It fixes mean values by taking the average travel time for all non-null values on the route,
and it fixes the standard deviation by taking the average for the previous and next two non-null values.
"""

import sqlite3

db_file = r"C:\Users\wille\Documents\Code\markov-transit\thesis_data-2019-03-24.db"

db = sqlite3.connect(db_file)
c = db.cursor()

input("WARNING: This will overwrite NA values in the database. Hit enter to continue.")
# Start by fixing the means
sql = """
SELECT route_id, stop_seq FROM model_data
WHERE mu = 'NA'
"""
c.execute(sql)
mus = c.fetchall()

for mu in mus:
    route_id = mu[0]
    stop_seq = mu[1]
    # Get the average for all non-NA stops
    sql = f"SELECT avg(mu) FROM model_data WHERE route_id = {route_id} AND mu != 'NA'"
    c.execute(sql)
    new_mu = c.fetchone()[0]
    sql = f"UPDATE model_data SET mu = {new_mu} WHERE stop_seq = {stop_seq}"
    c.execute(sql)

# Now the sigmas
sql = """
SELECT route_id, stop_seq FROM model_data
WHERE sigma = 'NA'
"""
c.execute(sql)
sigmas = c.fetchall()

for sigma in sigmas:
    route_id = sigma[0]
    stop_seq = int(sigma[1])
    # Get the previous two sigma if non-null and the next two sigma
    sql = f"""
    SELECT avg(sigma) FROM model_data
    WHERE route_id = {route_id} 
    AND stop_seq IN ({stop_seq-1}, {stop_seq-2}, {stop_seq+1}, {stop_seq+2})
    AND sigma != 'NA'"""
    c.execute(sql)
    new_sigma = c.fetchone()[0]
    sql = f"UPDATE model_data SET sigma = {new_sigma} WHERE route_id = {route_id} and stop_seq = {stop_seq}"
    c.execute(sql)

db.commit()