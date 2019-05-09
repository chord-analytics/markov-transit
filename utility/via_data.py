import sqlite3
import pandas as pd

VIA_DATA = r"C:\Users\wille\Documents\Code\via-reliability\data\via_data.db"
db = sqlite3.connect(VIA_DATA)
train = 84

sql = f"""
SELECT station_id, stop_seq, realDep from traintime
JOIN (
SELECT stop_seq, stop_id FROM routestop WHERE routestop.train = {train}) as stop ON stop.stop_id = station_id
WHERE train = {train}
AND realDep IS NOT NULL
ORDER BY realDep
"""

df = pd.read_sql(sql, db)

df['realDep'] = pd.to_datetime(df['realDep'])

df['travel'] = (df['realDep'] - df['realDep'].shift()).dt.total_seconds()/60
df['seq_delta'] = (df['stop_seq'] - df['stop_seq'].shift())
df['to_stop'] = df['station_id']
df['from_stop'] = df['station_id'].shift()
df = df.dropna()
df['from_stop'] = df['from_stop'].astype(int)
df = df[df.seq_delta == 1]
df = df[['from_stop', 'to_stop', 'stop_seq', 'station_id', 'travel']]
df.to_csv(f"via_{train}_travel_times.csv", index=False)
gb = df[['from_stop', 'to_stop', 'travel']].groupby(['from_stop', 'to_stop']).count()
gb['mu'] = df[['from_stop', 'to_stop', 'travel']].groupby(['from_stop', 'to_stop'])['travel'].mean()
gb['sigma'] = df[['from_stop', 'to_stop', 'travel']].groupby(['from_stop', 'to_stop'])['travel'].std()
gb.to_csv(f"via_{train}_travel_time_stats.csv")
print(gb.head(40))