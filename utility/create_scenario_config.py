"""
This script creates configurations in the database to allow for various scenarios to be tested for the hub system.
If you have the latest data source, you shouldn't have to run this.
It creates two scenarios - a null scenario and a Calgary Transit approximation with a slack time of 3min
"""

import sqlite3

db_file = r"C:\Users\wille\Documents\Code\markov-transit\thesis_data-2019-03-24.db"

db = sqlite3.connect(db_file)
c = db.cursor()

# Let's grab all the distinct routes already in the model_data set:
sql = "SELECT distinct route_id FROM model_data WHERE config_id = 1"
c.execute(sql)

routes = c.fetchall()

for route in routes:
    route_id = route[0]
    sql = f"""
    SELECT route_id, config_id, stop_seq, stop_id, mu, sigma, nb, na, theta, gamma_e, gamma_l, tau, is_tp
    FROM model_data WHERE route_id = {route_id} AND config_id = 1 ORDER BY stop_seq
    """
    c.execute(sql)
    model_data = [list(i) for i in c.fetchall()]
    ct_data = model_data.copy()
    ground_data = model_data.copy()

    # Let's grab the existing CT timepoints:
    sql = f"""
    SELECT stop_seq, is_tp from route_stop 
    JOIN stop on route_stop.stop_id = stop.stop_id
    WHERE route_id = {route_id}
    ORDER BY stop_seq"""
    c.execute(sql)
    tps = c.fetchall()
    for tp in tps:
        if tp[0] < len(ct_data):
            ct_data[int(tp[0])][12] = int(tp[1])
            ct_data[int(tp[0])][11] = 3
            ct_data[int(tp[0])][1] = 98

    for ct in ct_data:
        sql = """
        INSERT INTO model_data (route_id, config_id, stop_seq, stop_id, mu, sigma, nb, na, theta, gamma_e, gamma_l, tau,is_tp)
        VALUES ({})
        """.format(",".join([str(j) for j in ct]))
        c.execute(sql)

        line = [str(j) for j in ct[:-2]]
        line[1] = '99'
        sql = """
        INSERT INTO model_data (route_id, config_id, stop_seq, stop_id, mu, sigma, nb, na, theta, gamma_e, gamma_l, tau,is_tp)
        VALUES ({},0,0)
        """.format(",".join(line))
        c.execute(sql)

    sql = f"""INSERT INTO model_config (route_id, config_id, comments) 
    VALUES ({route_id}, 99, 'Ground state for all time points, 0min slack')"""
    c.execute(sql)
    sql = f"""
    INSERT INTO model_config (route_id, config_id, comments) 
    VALUES ({route_id}, 98, 'Calgary Transit time points, 3min slack');
    """
    c.execute(sql)

db.commit()