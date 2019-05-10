import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import numpy as np
plt.rcParams.update({'font.size': 10})


hubs = json.load(open('../utility/hub_transfer.json'))
data = []
for hub_idx, hub in enumerate(hubs['hubs']):
    mtxs = hub['transfer_probability_matrix']
    idx = hub['transfer_probability_matrix_index']
    idx = {i:k for k,i in idx.items()}
    for i, mtx in enumerate(mtxs):
        for j, val in enumerate(mtx):
            # print(f"From route {idx[i]} to {idx[j]}: {val}")
            data.append([hub_idx, idx[i], idx[j], val])

df = pd.DataFrame(data, columns=['hub_id', 'from', 'to', 'value'])
df['value'] = np.where(df['from'] == df['to'], np.NaN, df['value'])

hub_id = 1
uc = df[df.hub_id == hub_id].pivot(index='from', columns='to', values='value')

print(uc.head(30))
sns.heatmap(uc,
                annot=True,
                cmap='YlGnBu',
                cbar_kws={'label': 'Probability'})
plt.xlabel('To')
plt.ylabel('From')
plt.title(f"Probability of Missed Transfers at {hubs['hubs'][hub_id]['name']}")
plt.tight_layout()
plt.show()
