import os
import glob
from pathlib import Path
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

fontsize = 30
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['font.size'] = fontsize
plt.rcParams['axes.linewidth'] = 1.0

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = REPO_ROOT / 'data' / 'multistory_corridor'
BER_DIR = os.path.join(BASE_DIR, 'BER_data')
POWER_DIR = os.path.join(BASE_DIR, 'Power_data')


def load_series_data(folder_path, col_name=None, is_power=False):
    files = sorted(glob.glob(os.path.join(folder_path, '*.csv')))
    values = []
    for f in files:
        try:
            if is_power:
                df = pd.read_csv(f, header=None)
                val = df.iloc[0, 0]
            else:
                df = pd.read_csv(f)
                if col_name in df.columns:
                    val = df[col_name].mean()
                else:
                    idx = 1 if 'BER' in col_name else 2
                    val = df.iloc[:, idx].mean()
            values.append(val)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            values.append(np.nan)
    return values


def willmott_index(measured, simulated):
    """Calculate the Willmott index of agreement."""
    meas = np.array(measured)
    sim = np.array(simulated)
    mean_meas = np.mean(meas)
    numerator = np.sum((sim - meas) ** 2)
    denominator = np.sum((np.abs(sim - mean_meas) + np.abs(meas - mean_meas)) ** 2)
    if denominator == 0:
        return 1.0
    return 1 - (numerator / denominator)


def plot_ber(ax, data_no, data_with, ylabel):
    y1 = np.array(data_no[-20:])
    y2 = np.array(data_with[-20:])

    x = np.arange(1, len(y1) + 1)

    # ax.plot(x, y1, 'k-o', markersize=5, linewidth=1.5, label='Without WM-metaAgent')
    # ax.plot(x, y2, 'r-s', markersize=5, linewidth=1.5, label='With WM-metaAgent')
    ax.plot(x, y1, 'k-o', markersize=5, linewidth=1.5)
    ax.plot(x, y2, 'r-s', markersize=5, linewidth=1.5)

    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.5)
    # ax.set_xlabel('Index of points')
    # ax.set_ylabel(ylabel)
    ax.set_xlim(0.5, len(y1) + 0.5)

    ax.set_xticks(np.arange(0, len(y1) + 1, 5))
    # ax.legend(loc='lower right')


def plot_power_comparison1(ax, meas, sim, ylabel):
    y_meas = np.array(meas[-20:])
    y_sim = np.array(sim[-20:])

    x = np.arange(1, len(y_meas) + 1)

    # ax.plot(x, y_meas, 'k-o', markersize=5, mfc='none', linewidth=1.5, label='Measured')
    # ax.plot(x, y_sim, 'b--s', markersize=5, mfc='none', linewidth=1.5, label='Predicted')
    # ax.fill_between(x, y_meas, y_sim, color='blue', alpha=0.15, label='Error Gap')
    ax.plot(x, y_meas, 'k-o', markersize=5, mfc='none', linewidth=1.5)
    ax.plot(x, y_sim, 'b--s', markersize=5, mfc='none', linewidth=1.5)
    ax.fill_between(x, y_meas, y_sim, color='blue', alpha=0.15)

    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.5)
    # ax.set_xlabel('Index of points')
    # ax.set_ylabel(ylabel)
    ax.set_xlim(0.5, len(y_meas) + 0.5)

    ax.set_xticks(np.arange(0, len(y_meas) + 1, 5))
    # ax.legend(loc='lower left')


def plot_power_comparison2(ax, meas, sim, ylabel):
    y_meas = np.array(meas[-20:])
    y_sim = np.array(sim[-20:])

    x = np.arange(1, len(y_meas) + 1)

    # ax.plot(x, y_meas, 'r-o', markersize=5, mfc='none', linewidth=1.5, label='Measured')
    # ax.plot(x, y_sim, 'g--s', markersize=5, mfc='none', linewidth=1.5, label='Predicted')
    # ax.fill_between(x, y_meas, y_sim, color='green', alpha=0.15, label='Error Gap')
    ax.plot(x, y_meas, 'r-o', markersize=5, mfc='none', linewidth=1.5)
    ax.plot(x, y_sim, 'g--s', markersize=5, mfc='none', linewidth=1.5)
    ax.fill_between(x, y_meas, y_sim, color='green', alpha=0.15)

    ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.5)
    # ax.set_xlabel('Index of points')
    # ax.set_ylabel(ylabel)
    ax.set_xlim(0.5, len(y_meas) + 0.5)

    ax.set_xticks(np.arange(0, len(y_meas) + 1, 5))
    # ax.legend(loc='lower left')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))


def plot_bar_improvement(ax, meas_diff, sim_diff):
    y_meas = np.array(meas_diff[-20:])
    y_sim = np.array(sim_diff[-20:])

    x = np.arange(1, len(y_meas) + 1)

    width = 0.4
    # ax.bar(x - width / 2, y_meas, width, color='purple', alpha=0.7, label='Measured')
    # ax.bar(x + width / 2, y_sim, width, color='orange', alpha=0.7, label='Predicted')
    ax.bar(x - width / 2, y_meas, width, color='purple', alpha=0.7)
    ax.bar(x + width / 2, y_sim, width, color='orange', alpha=0.7)

    ax.grid(True, axis='y', linestyle='--', linewidth=0.5, alpha=0.7)
    # ax.set_xlabel('Index of points')
    # ax.set_ylabel('Power Improvement (dB)')
    ax.set_xlim(0.5, len(y_meas) + 0.5)

    ax.set_xticks(np.arange(0, len(y_meas) + 1, 5))
    # ax.legend(loc='lower right')


def main():
    ber_no = load_series_data(os.path.join(BER_DIR, 'no_ris'), 'Log10_BER')
    ber_with = load_series_data(os.path.join(BER_DIR, 'with_ris'), 'Log10_BER')

    pow_no = load_series_data(os.path.join(POWER_DIR, 'no_ris'), is_power=True)
    pow_with = load_series_data(os.path.join(POWER_DIR, 'with_ris'), is_power=True)
    pow_no_sim = load_series_data(os.path.join(POWER_DIR, 'no_ris_sim'), is_power=True)
    pow_with_sim = load_series_data(os.path.join(POWER_DIR, 'with_ris_sim'), is_power=True)

    min_len = min(len(pow_no), len(pow_with), len(pow_no_sim), len(pow_with_sim))
    pow_no, pow_with = pow_no[:min_len], pow_with[:min_len]
    pow_no_sim, pow_with_sim = pow_no_sim[:min_len], pow_with_sim[:min_len]

    ber_min_len = min(len(ber_no), len(ber_with))
    ber_no_arr = np.array(ber_no[:ber_min_len])
    ber_with_arr = np.array(ber_with[:ber_min_len])

    r_no = np.corrcoef(pow_no, pow_no_sim)[0, 1] if min_len > 1 else 0
    d_no = willmott_index(pow_no, pow_no_sim)
    r_with = np.corrcoef(pow_with, pow_with_sim)[0, 1] if min_len > 1 else 0
    d_with = willmott_index(pow_with, pow_with_sim)

    print("\n" + "=" * 40)
    print("           Agreement metrics (measured vs simulated)      ")
    print("=" * 40)
    print(f"No-RIS case:\n  - Pearson correlation: {r_no:.4f}\n  - Willmott index of agreement: {d_no:.4f}")
    print(f"RIS-assisted case:\n  - Pearson correlation: {r_with:.4f}\n  - Willmott index of agreement: {d_with:.4f}")

    pow_meas_diff = np.array(pow_with) - np.array(pow_no)
    pow_sim_diff = np.array(pow_with_sim) - np.array(pow_no_sim)

    print("\n" + "=" * 40)
    print("              Mean regional power gain (dB)             ")
    print("=" * 40)
    bounds = [0, 15, 35]
    for i in range(2):
        start = bounds[i]
        end = bounds[i + 1]
        if start < len(pow_meas_diff):
            meas_mean = np.mean(pow_meas_diff[start:min(end, len(pow_meas_diff))])
            sim_mean = np.mean(pow_sim_diff[start:min(end, len(pow_sim_diff))])
            print(
                f"Area {i + 1} (points {start + 1}-{end}): measured mean gain = {meas_mean:5.2f} dB  |  simulated mean gain = {sim_mean:5.2f} dB")

    print("-" * 40)
    print(
        f"Total : overall measured mean gain = {np.mean(pow_meas_diff):5.2f} dB  |  overall simulated mean gain = {np.mean(pow_sim_diff):5.2f} dB")
    print("=" * 40 + "\n")

    ber_log_diff = ber_no_arr - ber_with_arr

    print("\n" + "=" * 45)
    print("       Mean regional Log10(BER) reduction        ")
    print("=" * 45)
    for i in range(2):
        start = bounds[i]
        end = bounds[i + 1]
        if start < len(ber_log_diff):
            ber_mean = np.mean(ber_log_diff[start:min(end, len(ber_log_diff))])
            print(f"Area {i + 1}: measured reduction = {ber_mean:5.2f} orders of magnitude")

    print("-" * 45)
    print(f"Total : overall measured reduction = {np.mean(ber_log_diff):5.2f} orders of magnitude")
    print("=" * 45 + "\n")

    fig1, ax1 = plt.subplots(figsize=(12, 8))
    plot_ber(ax1, ber_no, ber_with, 'Log10(BER)')
    # ax1.set_ylim(-6.5, -3.5)
    # ax1.set_yticks([-6.5, -3.5])
    plt.tight_layout()
    # plt.savefig("Figure_1_BER.png", dpi=300)
    plt.show()

    fig2, ax2 = plt.subplots(figsize=(12, 8))
    plot_power_comparison1(ax2, pow_no, pow_no_sim, 'Rx Power (dBm)')
    plt.tight_layout()
    # plt.savefig("Figure_2_Power_NoRIS.png", dpi=300)
    plt.show()

    fig3, ax3 = plt.subplots(figsize=(12, 8))
    plot_power_comparison2(ax3, pow_with, pow_with_sim, 'Rx Power (dBm)')
    plt.tight_layout()
    # plt.savefig("Figure_3_Power_WithRIS.png", dpi=300)
    plt.show()

    fig4, ax4 = plt.subplots(figsize=(12, 8))
    plot_bar_improvement(ax4, pow_meas_diff, pow_sim_diff)
    plt.tight_layout()
    # plt.savefig("Figure_4_Power_Improvement.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    main()
