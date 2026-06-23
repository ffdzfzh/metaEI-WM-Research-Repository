import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

fontsize = 30
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = fontsize
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'

repo_root = Path(__file__).resolve().parents[2]
capacity_file = repo_root / 'data' / 'human_tracking' / 'capacity.xlsx'
capacity_data = pd.read_excel(capacity_file, header=None, index_col=0)
no_ris = capacity_data.loc['no_ris'].to_numpy(dtype=float)
with_ris = capacity_data.loc['with_ris'].to_numpy(dtype=float)

total_points = len(no_ris)
index = np.arange(1, total_points + 1)

capacity_gain = with_ris - no_ris

fig, ax1 = plt.subplots(figsize=(12, 8))

ax2 = ax1.twinx()
bars = ax2.bar(index, capacity_gain, width=0.45, color='steelblue',
               alpha=0.3, edgecolor='black', linewidth=1.0, label='Capacity Gain')

ax1.plot(index, no_ris, 'k-o', markersize=8, linewidth=2, label='Without WM-metaAgent', zorder=3)
ax1.plot(index, with_ris, 'r-s', markersize=8, linewidth=2, label='With WM-metaAgent', zorder=3)

ax1.set_zorder(ax2.get_zorder() + 1)
ax1.patch.set_visible(False)

ax1.set_xlabel('Index of points')
ax1.set_ylabel('Capacity (Mbps)')
ax2.set_ylabel('Capacity Gain', color='steelblue')
ax2.tick_params(axis='y', labelcolor='steelblue')

ax1.set_xlim(0.5, total_points + 0.5)
ax1.set_xticks(np.arange(0, total_points + 1, 2))

y1_min, y1_max = np.min(no_ris), np.max(with_ris)
ax1.set_ylim(y1_min - 2.5, y1_max + 1.0)

y2_max = np.max(capacity_gain)
ax2.set_ylim(0, y2_max * 3.5)

lines, labels = ax1.get_legend_handles_labels()
bars_h, bars_l = ax2.get_legend_handles_labels()
ax1.legend(lines + bars_h, labels + bars_l, loc='upper left', fontsize=fontsize-6)

ax1.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.5)

plt.tight_layout()
plt.show()
