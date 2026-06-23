import os
from pathlib import Path
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = 26
plt.rcParams['axes.linewidth'] = 1.0

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = REPO_ROOT / 'data' / 'multistory_corridor'
BER_DIR = os.path.join(BASE_DIR, 'BER_data')
FOLDER_PATH = os.path.join(BER_DIR, 'constellation')


def load_constellation_data(folder_path):
    """Load the paired constellation CSV files from one directory."""
    configs = [
        {'type': 'Without RIS', 'file': os.path.join(folder_path, 'data_without.csv')},
        {'type': 'With RIS', 'file': os.path.join(folder_path, 'data_with.csv')}
    ]

    results = []
    for cfg in configs:
        if not os.path.exists(cfg['file']):
            print(f"Warning: file not found: {cfg['file']}")
            continue

        try:
            df = pd.read_csv(cfg['file'], header=None)
            data_vals = df.iloc[1:, :].apply(pd.to_numeric, errors='coerce').values
            results.append({
                'type': cfg['type'],
                'I': data_vals[1:, 0],
                'Q': data_vals[1:, 1]
            })
        except Exception as e:
            print(f"Error parsing constellation {cfg['file']}: {e}")

    return results


def main():
    const_data = load_constellation_data(FOLDER_PATH)

    if const_data:
        fig = plt.figure(figsize=(12, 6))
        gs = gridspec.GridSpec(1, 2)

        for i, data in enumerate(const_data):
            ax = fig.add_subplot(gs[0, i])

            color = 'black' if data['type'] == 'Without RIS' else 'red'
            ax.scatter(data['I'], data['Q'], s=1, alpha=0.5, c=color)

            ax.set_title(data['type'], fontsize=26, pad=15)

            ax.set_xlabel('I')
            ax.set_ylabel('Q')

            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            ax.set_xticks([-1, 0, 1])
            ax.set_yticks([-1, 0, 1])

            ax.set_aspect('equal', adjustable='box')
            ax.grid(True, linestyle=':', alpha=0.4)

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()
