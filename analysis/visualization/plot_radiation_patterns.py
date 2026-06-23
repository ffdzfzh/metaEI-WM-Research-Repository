import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.colors import ListedColormap
from pathlib import Path


config = {
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "mathtext.fontset": "stix",
    "font.size": 20,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "axes.linewidth": 1.5,
    "xtick.major.width": 1.5,
    "ytick.major.width": 1.5,
}
rcParams.update(config)
fontsize = 20
plt.rcParams['font.size'] = fontsize

repo_root = Path(__file__).resolve().parents[2]
data = sio.loadmat(repo_root / 'data' / 'radiation_patterns' / 'scene1_area1.mat')

antenna_phase = data['antenna_phase'].T
phase_estimate = data['phase_estimate'].T
code_book = data['code_book']
target_pattern = data['target_pattern']
optimized_pattern = data['optimized_pattern']

theta_vec = data['theta_vec'].flatten()
phi_vec = data['phi_vec'].flatten()

extent_angles = [theta_vec.min(), theta_vec.max(), phi_vec.min(), phi_vec.max()]


cmap_phase = 'twilight_shifted'

cmap_pattern = 'magma'

cmap_binary = ListedColormap(['#F2F2F2', '#2B5C8A'])


def plot_and_save(data_matrix, filename, cmap, extent=None, xlabel=None, ylabel=None, origin='lower',
                  is_first_three=False):
    fig = plt.figure(figsize=(6.5, 5))

    # [left, bottom, width, height]
    ax = fig.add_axes([0.15, 0.15, 0.65, 0.75])

    if extent is not None:
        im = ax.imshow(data_matrix, cmap=cmap, extent=extent, origin=origin, aspect='auto')
    else:
        data_matrix = np.flip(data_matrix, axis=0)
        im = ax.imshow(data_matrix, cmap=cmap, origin=origin, aspect='auto')

    if is_first_three:
        ax.axis('off')

        ax.text(0, -0.02, '0', transform=ax.transAxes, ha='center', va='top', fontsize=fontsize)
        ax.text(1, -0.02, '15', transform=ax.transAxes, ha='center', va='top', fontsize=fontsize)
        ax.text(0, 1.02, '14', transform=ax.transAxes, ha='center', va='bottom', fontsize=fontsize)

        cax = fig.add_axes([0.82, 0.15, 0.03, 0.75])
        cbar = fig.colorbar(im, cax=cax)
        cbar.ax.tick_params(labelsize=12, width=1.2, length=3)
        cbar.outline.set_linewidth(1.0)

    else:
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)

        cax = fig.add_axes([0.82, 0.15, 0.03, 0.75])
        cbar = fig.colorbar(im, cax=cax)
        cbar.ax.tick_params(labelsize=12, width=1.2, length=3)
        cbar.outline.set_linewidth(1.0)

    # plt.savefig(filename)
    plt.show()




plot_and_save(antenna_phase, 'Fig1_Antenna_Phase.pdf', cmap=cmap_phase,
              origin='lower', is_first_three=True)

plot_and_save(phase_estimate, 'Fig2_Phase_Estimate.pdf', cmap=cmap_phase,
              origin='lower', is_first_three=True)

plot_and_save(code_book, 'Fig3_Code_Book.pdf', cmap=cmap_binary,
              origin='lower', is_first_three=True)

plot_and_save(target_pattern, 'Fig4_Target_Pattern.pdf', cmap=cmap_pattern, extent=extent_angles,
              xlabel=r'$\theta$ (deg)', ylabel=r'$\phi$ (deg)', origin='lower', is_first_three=False)

plot_and_save(optimized_pattern, 'Fig5_Optimized_Pattern.pdf', cmap=cmap_pattern, extent=extent_angles,
              xlabel=r'$\theta$ (deg)', ylabel=r'$\phi$ (deg)', origin='lower', is_first_three=False)
