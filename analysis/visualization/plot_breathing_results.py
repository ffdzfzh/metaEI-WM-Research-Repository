import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def visualize_from_npz():
    plt.rcParams.update({'font.size': 30})

    RECORD_SECONDS = 100
    cold_bg_colors = ['#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff']

    try:
        repo_root = Path(__file__).resolve().parents[2]
        data = np.load(repo_root / 'data' / 'breath_detection' / 'respiration_data.npz')
    except FileNotFoundError:
        print("Data file not found: respiration_data.npz")
        return

    combined_t_signal = data['t_signal']
    signal_clipped = data['signal']
    combined_t_rpm = data['t_rpm']
    combined_rpm = data['rpm']
    t_smooth = data['t_smooth']
    bpm_smooth = data['bpm_smooth']

    fig1, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(combined_t_signal, signal_clipped, color='blue', linewidth=2.0, label="Receiving signal")
    ax1.set_xlabel("Time(s)")
    ax1.set_ylabel("Amp(norm)")
    ax1.set_xlim(0, RECORD_SECONDS)
    ax1.set_ylim(-1.2, 1.2)
    ax1.set_yticks([-1, 0, 1])
    ax1.grid(True, linestyle='--', alpha=0.6)

    ax1.legend(loc='upper right', fontsize=20)

    for i in range(5):
        ax1.axvspan(i * 20, (i + 1) * 20, facecolor=cold_bg_colors[i], alpha=0.3)

    fig1.tight_layout()

    fig2, ax2 = plt.subplots(figsize=(12, 5))

    if len(t_smooth) > 0:
        ax2.plot(t_smooth, bpm_smooth, color='lightgray',
                 linestyle='-', linewidth=3.0, zorder=1, label="Reference signal")

    if len(combined_t_rpm) > 0:
        ax2.plot(combined_t_rpm, combined_rpm, marker='o', color='red',
                 linestyle='-', markersize=8, linewidth=2.0, zorder=2, label="Calculated signal")
    else:
        ax2.text(50, 20, "No valid data", ha='center', va='center')

    ax2.set_xlabel("Time(s)")
    ax2.set_ylabel("RR(bpm)")
    ax2.set_xlim(0, RECORD_SECONDS)
    ax2.set_ylim(0, 30)
    ax2.set_yticks([0, 10, 20, 30])
    ax2.grid(True, linestyle='--', alpha=0.6)

    ax2.legend(loc='upper right', fontsize=20)

    for i in range(5):
        ax2.axvspan(i * 20, (i + 1) * 20, facecolor=cold_bg_colors[i], alpha=0.3)

    fig2.tight_layout()
    plt.show()


if __name__ == "__main__":
    visualize_from_npz()
