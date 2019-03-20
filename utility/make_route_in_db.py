import sqlite3
from datetime import datetime
import statistics
import numpy as np
from scipy.stats import skew

DB = "../CT81.idb"
thesis_db = "../thesis_data.db"
conn = sqlite3.connect(DB)
c = conn.cursor()
thesis_conn = sqlite3.connect("../thesis_data.db")
thesis_c = thesis_conn.cursor()

# First, we have you put in the "Route Number"
route_no = int(input("Enter Route Number: "))
route_options = []
c.execute("SELECT ROUTEHND, STARTSTOP, ENDSTOP FROM ROUTE WHERE ROUTEMAJOR = ?", (route_no,))
res = c.fetchall()
print("Route {} has {} results.".format(route_no, len(res)))
for r in res:
    c.execute("SELECT STOPWAY FROM STOP WHERE STOPHND = ?", (r[1],))
    start_name = c.fetchone()[0]
    c.execute("SELECT STOPWAY FROM STOP WHERE STOPHND = ?", (r[2],))
    end_name = c.fetchone()[0]
    c.execute("SELECT COUNT(SAMPLEHND) FROM SAMPLE WHERE ROUTEHND = ?", (r[0],))
    sample_count = c.fetchone()[0]
    thesis_c.execute("SELECT COUNT(route_id) FROM route_stop WHERE route_id = ?", (r[0],))
    if int(thesis_c.fetchone()[0]) > 0:
        exists = True
    else:
        exists = False
    route_options.append([r[0], r[1], start_name, r[2], end_name, sample_count, exists])

for idx, route in enumerate(route_options):
    if route[6]:
        print("{}. ({}) {} to {}: {} samples [EXISTS IN DB]".format(idx, route[0], route[2], route[4], route[5]))
    else:
        print("{}. ({}) {} to {}: {} samples".format(idx, route[0], route[2], route[4], route[5]))

choice = int(input("Which choice would you like? "))
route_id = int(route_options[choice][0])
start_stop = int(route_options[choice][1])
end_stop = int(route_options[choice][3])
# First get route stop list
sql = """
SELECT DETAIL.STOPHND,
DETAIL.ROUTESEQ
FROM DETAIL
JOIN SAMPLE ON SAMPLE.SAMPLEHND = DETAIL.SAMPLEHND
WHERE SAMPLE.ROUTEHND = ?

GROUP BY DETAIL.STOPHND
ORDER BY DETAIL.ROUTESEQ"""
c.execute(sql, (route_id,))

res = [[route_id, i[0], i[1]] for i in c.fetchall()]

print("Finding Route Stop Data")
print("Route has {} stops, last stop sequence is {}".format(len(res), res[-1][2]))
input("Press enter to write to database")
for r in res:
    sql = """INSERT INTO route_stop (route_id, stop_id, stop_seq) VALUES (?,?,?)"""
    thesis_c.execute(sql, r)
thesis_conn.commit()

delta_dict = {}
summary_stats = []
db_data = []

# First get route stop list
sql = """
SELECT DETAIL.STOPHND,
DETAIL.ROUTESEQ
FROM DETAIL
JOIN SAMPLE ON SAMPLE.SAMPLEHND = DETAIL.SAMPLEHND
WHERE SAMPLE.ROUTEHND = ?
GROUP BY DETAIL.STOPHND
ORDER BY DETAIL.ROUTESEQ"""
c.execute(sql, (route_id,))

res = [i[0] for i in c.fetchall()]
stop_pairs = []
for i in range(len(res)-1):
    stop_pairs.append([res[i], res[i + 1]])

# Dealing with the a loop in a bad but quick way
if start_stop == end_stop:
    stop_pairs.append([stop_pairs[-1][1], stop_pairs[0][0]])

for pair in stop_pairs:
    delta_dict[tuple(pair)] = []

# First get only
sql = "SELECT SAMPLEHND from SAMPLE WHERE ROUTEHND = ?"
c.execute(sql, (route_id,))
sample_ids = [i[0] for i in c.fetchall()]

count = 0
for sample_id in sample_ids:
    print("Sample {} of {}".format(count, len(sample_ids)))
    count += 1
    sql = """
    SELECT DETAILHND, DETAILSTART, DETAILEND, DLLONG/1000000.0 as lon, DLLAT/1000000.0 as lat, DETAIL.STOPHND, STOP.STOPWAY, ROUTESEQ, TIMEPOINT  from DETAIL
    JOIN SAMPLE ON DETAIL.SAMPLEHND = SAMPLE.SAMPLEHND
    JOIN STOP on STOP.STOPHND = DETAIL.STOPHND
    AND DETAIL.SAMPLEHND = ?
    ORDER BY DETAIL.SAMPLEHND, ROUTESEQ"""
    c.execute(sql, (sample_id,))
    details = c.fetchall()
    for idx in range(len(details)-1):
        if int(details[idx][7])+1 == int(details[idx+1][7]):
            start_time = int(datetime.strptime(details[idx][2], '%Y-%m-%d %H:%M:%S').timestamp())
            end_time = int(datetime.strptime(details[idx+1][1], '%Y-%m-%d %H:%M:%S').timestamp())
            minutes = (end_time-start_time)/60.0
            tup = tuple([details[idx][5], details[idx+1][5]])
            if minutes > 0:
                delta_dict[tup].append(minutes)

for idx in delta_dict:
    print("Inserting stop pair data for {},{}".format(idx[0], idx[1]))
    deltas = delta_dict[idx]

    # Fetch information about the route
    sql = """
                    SELECT stop_name, stop_lat, stop_lon, stop_seq
                    FROM stop
                    JOIN route_stop on stop.stop_id = route_stop.stop_id
                    WHERE stop.stop_id = ?
                    AND route_id = ?"""
    thesis_c.execute(sql, (idx[0], route_id))
    res = thesis_c.fetchone()
    start_name = res[0]
    start_lat = res[1]
    start_lon = res[2]
    seq = res[3]
    thesis_c.execute(sql, (idx[1], route_id))
    res = thesis_c.fetchone()
    end_name = res[0]
    end_lat = res[1]
    end_lon = res[2]
    mean = "NA"
    sd = "NA"

    # Do some stats
    if len(deltas) > 2:
        mean = statistics.mean(deltas)
        sd = statistics.stdev(deltas)
        cov = sd / mean
    if len(deltas) == 1:
        mean = statistics.mean(deltas)
        sd = 0
        cov = 0
    if len(deltas) < 1:
        print("Not Enough Data")
        raise Exception

    print("Inserting model data for {},{}".format(idx[0], idx[1]))
    # Fetch passenger stats about the route
    sql = """SELECT STOPHND, DETAIL.ROUTESEQ, COUNT(STOPHND) AS NUM, AVG(IN0), AVG(OUT0), AVG(BUSLOAD)  from DETAIL
                     JOIN SAMPLE ON SAMPLE.SAMPLEHND = DETAIL.SAMPLEHND
                     WHERE SAMPLE.ROUTEHND = ?
                     AND STOPHND = ?
                     GROUP BY STOPHND
                     ORDER BY DETAIL.ROUTESEQ"""
    c.execute(sql, (route_id, idx[0]))
    psgr = c.fetchone()
    out_data = [route_id, 1, seq, idx[0], mean, sd, psgr[3], psgr[4], psgr[5], 0.0, 0.0, 0]
    sql = """INSERT INTO model_data (route_id, config_id, stop_seq, stop_id, mu, sigma, nb, na, theta, gamma_e, gamma_l, tau)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"""
    thesis_c.execute(sql, out_data)

    print("Inserting travel time data for {},{}".format(idx[0], idx[1]))
    # Insert the travel time data
    for time in deltas:
        sql = """INSERT INTO travel_time (route_id, start_stop, end_stop, travel_time) VALUES (?,?,?,?)"""
        thesis_c.execute(sql, (route_id, idx[0], idx[1], time))
    skewness = skew(np.asarray(deltas, dtype=np.float32))
    sql = """INSERT INTO travel_time_stat (route_id, start_stop, end_stop, mean, sd, skewness) VALUES (?,?,?,?,?,?)"""
    thesis_c.execute(sql, (route_id, idx[0], idx[1], mean, sd, skewness))

    summary_stats.append([seq, idx[0], start_name, start_lat, start_lon, idx[1], end_name, end_lat, end_lon, len(deltas), mean, sd, cov])
thesis_conn.commit()

# Last, we create a model config default
thesis_c.execute("INSERT INTO model_config (route_id, config_id, comments) VALUES (?, 1, 'Standard configuration, slack time of 0min')", (route_id,))
thesis_conn.commit()

with open("route_{}_summary.csv".format(route_id), 'w') as outfile:
    outfile.write("Link,Start ID, Start Name, Start lat, Start lon, End ID, End Name, End lat, End Lon, Counts, Mean, SD, COV\n")
    outfile.write("\n".join([",".join([str(i) for i in x]) for x in summary_stats]))

