import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from vmdpy import VMD


def process_vital_signs(phase_signal, fs):
    """Extract respiration and heartbeat components from unwrapped phase."""
    nyq = 0.5 * fs
    b, a = butter(3, [0.1 / nyq, 5.0 / nyq], btype='band')
    filtered_signal = filtfilt(b, a, phase_signal)

    alpha = 2000  # data-fidelity tolerance
    tau = 0  # time-step of the dual ascent
    K = 4
    DC = 0  # no DC part imposed
    init = 1  # initialize omegas uniformly
    tol = 1e-7

    u, u_hat, omega = VMD(filtered_signal, alpha, tau, K, DC, init, tol)
    freqs = np.mean(omega, axis=1) * fs / 2

    sorted_indices = np.argsort(freqs)

    resp_signal = u[sorted_indices[0], :]

    hb_candidate = None
    for idx in sorted_indices:
        if 0.9 <= freqs[idx] <= 2.0:
            hb_candidate = u[idx, :]
            break

    if hb_candidate is None:
        hb_candidate = u[sorted_indices[-1], :]

    K2 = 5
    u2, u_hat2, omega2 = VMD(hb_candidate, alpha, tau, K2, DC, init, tol)
    freqs2 = np.mean(omega2, axis=1) * fs / 2
    sorted_indices2 = np.argsort(freqs2)

    heartbeat_signal = None
    for idx in sorted_indices2:
        if 0.9 <= freqs2[idx] <= 2.0:
            heartbeat_signal = u2[idx, :]
            break

    if heartbeat_signal is None:
        heartbeat_signal = u2[sorted_indices2[-1], :]

    resp_peaks, _ = find_peaks(resp_signal, distance=fs / 0.5)
    if len(resp_peaks) > 1:
        rr_intervals = np.diff(resp_peaks) / fs
        RR = 60.0 / np.mean(rr_intervals)
    else:
        RR = 0.0

    hb_peaks, _ = find_peaks(heartbeat_signal, distance=fs / 2.5)
    if len(hb_peaks) > 1:
        hr_intervals = np.diff(hb_peaks) / fs
        HR = 60.0 / np.mean(hr_intervals)
    else:
        HR = 0.0

    return resp_signal, heartbeat_signal, RR, HR
