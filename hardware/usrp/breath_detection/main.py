import uhd
import numpy as np
import time
from scipy.signal import butter, filtfilt, find_peaks
from vmdpy import VMD
import threading
import warnings

warnings.filterwarnings("ignore")

USRP_SAMP_RATE = 1e6
RF_CENTER_FREQ = 3.5e9
BASEBAND_OFFSET = 10e3
DECIMATION_FACTOR = 20000
FS_VITAL = USRP_SAMP_RATE / DECIMATION_FACTOR
WINDOW_SECONDS = 15
VITAL_BUFFER_SIZE = int(FS_VITAL * WINDOW_SECONDS)


def butter_bandpass(lowcut, highcut, fs, order=4):
    """Build a Butterworth band-pass filter for physiological motion."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def extract_doppler_phase(iq_data, start_time, samp_rate):
    """Down-convert the complex samples and extract unwrapped phase."""
    t = start_time + np.arange(len(iq_data)) / samp_rate
    tx_ref = np.exp(-1j * 2 * np.pi * BASEBAND_OFFSET * t)
    mixed = iq_data * tx_ref
    phase_unwrapped = np.unwrap(np.angle(mixed))
    return phase_unwrapped


def select_imf_by_frequency(u_matrix, fs, target_min, target_max):
    """Select the VMD mode with maximum energy in a target frequency band."""
    max_energy = -1
    best_idx = 0
    N = u_matrix.shape[1]
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)

    for i in range(u_matrix.shape[0]):
        spectrum = np.abs(np.fft.rfft(u_matrix[i, :]))
        band_mask = (freqs >= target_min) & (freqs <= target_max)
        energy = np.sum(spectrum[band_mask] ** 2)
        if energy > max_energy:
            max_energy = energy
            best_idx = i

    return u_matrix[best_idx, :]


def multi_layer_vmd_extraction(phase_signal, fs):
    """Apply two-stage VMD respiration and heartbeat separation."""
    alpha = 2000
    tau = 0.0
    DC = 0
    init = 1
    tol = 1e-7

    K1 = 4
    u1, _, omega1 = VMD(phase_signal, alpha, tau, K1, DC, init, tol)

    lowest_freq_idx = np.argmin(omega1[:, -1])
    resp_signal = u1[lowest_freq_idx, :]

    hr_candidate = select_imf_by_frequency(u1, fs, 0.8, 2.0)

    K2 = 5
    u2, _, _ = VMD(hr_candidate, alpha, tau, K2, DC, init, tol)

    heartbeat_signal = select_imf_by_frequency(u2, fs, 0.8, 2.0)

    return resp_signal, heartbeat_signal


def compute_rate_from_peaks(signal, fs, min_dist_seconds):
    """Estimate events per minute from peak intervals."""
    distance_samples = int(fs * min_dist_seconds)
    peaks, _ = find_peaks(signal, distance=distance_samples)
    if len(peaks) >= 2:
        mean_interval_sec = np.mean(np.diff(peaks)) / fs
        rate_per_min = 60.0 / mean_interval_sec
        return rate_per_min
    return 0.0


class VitalSignMonitor:
    def __init__(self):
        self.usrp = uhd.usrp.MultiUSRP()
        self.running = False
        self.vital_buffer = np.zeros(VITAL_BUFFER_SIZE)

        # self.usrp.set_rx_rate(USRP_SAMP_RATE)
        # self.usrp.set_rx_freq(uhd.lib.types.tune_request(RF_CENTER_FREQ))
        # self.usrp.set_rx_gain(50)
        #
        # self.usrp.set_tx_rate(USRP_SAMP_RATE)
        # self.usrp.set_tx_freq(uhd.lib.types.tune_request(RF_CENTER_FREQ))
        # self.usrp.set_tx_gain(60)

        self.usrp.set_rx_rate(USRP_SAMP_RATE)
        self.usrp.set_rx_freq(uhd.types.TuneRequest(RF_CENTER_FREQ))
        self.usrp.set_rx_gain(50)

        self.usrp.set_tx_rate(USRP_SAMP_RATE)
        self.usrp.set_tx_freq(uhd.types.TuneRequest(RF_CENTER_FREQ))
        self.usrp.set_tx_gain(60)

        self.b_band, self.a_band = butter_bandpass(0.1, 5.0, FS_VITAL, order=4)

        tx_t = np.arange(0, 10000) / USRP_SAMP_RATE
        self.tx_waveform = 0.7 * np.exp(1j * 2 * np.pi * BASEBAND_OFFSET * tx_t).astype(np.complex64)
        self.tx_waveform = np.tile(self.tx_waveform, (1, 1))

    def _tx_worker(self):
        """Continuously transmit the configured waveform."""
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = [0]
        tx_stream = self.usrp.get_tx_stream(st_args)
        metadata = uhd.types.TXMetadata()
        metadata.has_time_spec = False

        while self.running:
            tx_stream.send(self.tx_waveform, metadata)
            time.sleep(1e-4)

        metadata.end_of_burst = True
        tx_stream.send(np.zeros_like(self.tx_waveform), metadata)

    def process_vital_signs(self):
        """Run VMD periodically without blocking the receive loop."""
        while self.running:
            time.sleep(3.0)
            window_data = np.copy(self.vital_buffer)
            filtered_data = filtfilt(self.b_band, self.a_band, window_data)

            try:
                resp_sig, hr_sig = multi_layer_vmd_extraction(filtered_data, FS_VITAL)
                rr = compute_rate_from_peaks(resp_sig, FS_VITAL, 1.2)
                hr = compute_rate_from_peaks(hr_sig, FS_VITAL, 0.4)

                if hr > 0 and rr > 0:
                    print(f"[Live] Respiration rate: {rr:5.1f} per minute | heart rate: {hr:5.1f} per minute")
            except Exception as e:
                pass

    def run_stream(self):
        """Manage USRP streaming and signal decimation."""
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = [0]
        rx_stream = self.usrp.get_rx_stream(st_args)

        recv_buff = np.zeros((1, int(USRP_SAMP_RATE / 10)), dtype=np.complex64)
        metadata = uhd.types.RXMetadata()

        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        stream_cmd.stream_now = True
        rx_stream.issue_stream_cmd(stream_cmd)

        self.running = True

        processor_thread = threading.Thread(target=self.process_vital_signs)
        processor_thread.start()

        tx_thread = threading.Thread(target=self._tx_worker)
        tx_thread.start()

        print(f"[*] Metasurface-assisted monitoring active. Carrier: {RF_CENTER_FREQ / 1e9} GHz. Starting focused monitoring...")

        total_samples_processed = 0
        try:
            while self.running:
                num_rx = rx_stream.recv(recv_buff, metadata)
                if num_rx == 0:
                    continue

                iq_chunk = recv_buff[0, :num_rx]
                current_time = total_samples_processed / USRP_SAMP_RATE

                raw_phase = extract_doppler_phase(iq_chunk, current_time, USRP_SAMP_RATE)

                valid_len = (len(raw_phase) // DECIMATION_FACTOR) * DECIMATION_FACTOR
                if valid_len == 0:
                    total_samples_processed += num_rx
                    continue

                reshaped_phase = raw_phase[:valid_len].reshape(-1, DECIMATION_FACTOR)
                decimated_phase = np.mean(reshaped_phase, axis=1)

                num_new_vital_samples = len(decimated_phase)

                self.vital_buffer[:-num_new_vital_samples] = self.vital_buffer[num_new_vital_samples:]
                self.vital_buffer[-num_new_vital_samples:] = decimated_phase

                total_samples_processed += num_rx

        except KeyboardInterrupt:
            print("\n[*] Interrupt received; stopping transmission.")
            self.running = False
        finally:
            stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
            rx_stream.issue_stream_cmd(stream_cmd)
            processor_thread.join()
            tx_thread.join()


if __name__ == "__main__":
    monitor = VitalSignMonitor()
    monitor.run_stream()
