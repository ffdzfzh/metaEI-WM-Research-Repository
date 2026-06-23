import uhd
import numpy as np
import time
from scipy.signal import butter, filtfilt, find_peaks, lfilter, lfilter_zi
from vmdpy import VMD
import threading
import warnings
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

warnings.filterwarnings("ignore")

USRP_SAMP_RATE = 1e6
RF_CENTER_FREQ = 3.5e9
BASEBAND_OFFSET = 10e3
DECIMATION_FACTOR = 20000
FS_VITAL = USRP_SAMP_RATE / DECIMATION_FACTOR
WINDOW_SECONDS = 15
VITAL_BUFFER_SIZE = int(FS_VITAL * WINDOW_SECONDS)

RECORD_SECONDS = 100


def butter_bandpass(lowcut, highcut, fs, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, [lowcut / nyq, highcut / nyq], btype='band')
    return b, a


def single_layer_vmd_extraction(phase_signal, fs):
    alpha, tau, DC, init, tol = 2000, 0.0, 0, 1, 1e-7
    u1, _, omega1 = VMD(phase_signal, alpha, tau, 4, DC, init, tol)
    lowest_freq_idx = np.argmin(omega1[-1, :])
    resp_signal = u1[lowest_freq_idx, :]
    return resp_signal


def compute_rate_from_peaks(signal, fs, min_dist_seconds):
    distance_samples = int(fs * min_dist_seconds)
    dynamic_prominence = max(np.std(signal) * 0.3, 1e-6)
    peaks, _ = find_peaks(signal, distance=distance_samples, prominence=dynamic_prominence)

    if len(peaks) >= 2:
        mean_interval_sec = np.mean(np.diff(peaks)) / fs
        return 60.0 / mean_interval_sec
    return 0.0


class VitalSignMonitor:
    def __init__(self):
        self.usrp = uhd.usrp.MultiUSRP()
        self.running = False

        self.last_raw_phase = 0.0
        self.last_unwrapped_phase = 0.0
        self.phase_remainder = []

        self.vital_buffer = np.zeros(VITAL_BUFFER_SIZE)
        self.data_lock = threading.Lock()

        self.total_vital_samples = 0
        self.is_stable = False
        self.record_start_sample = 0

        self.recorded_time = []
        self.recorded_signal = []
        self.recorded_rpm_time = []
        self.recorded_rpm = []

        self.usrp.set_rx_rate(USRP_SAMP_RATE)
        self.usrp.set_rx_freq(uhd.types.TuneRequest(RF_CENTER_FREQ))
        self.usrp.set_rx_gain(50)

        self.usrp.set_tx_rate(USRP_SAMP_RATE)
        self.usrp.set_tx_freq(uhd.types.TuneRequest(RF_CENTER_FREQ))
        self.usrp.set_tx_gain(60)

        self.b_band, self.a_band = butter_bandpass(0.1, 0.8, FS_VITAL, order=4)
        self.b_live, self.a_live = butter_bandpass(0.15, 0.8, FS_VITAL, order=2)
        self.zi = lfilter_zi(self.b_live, self.a_live)

        tx_t = np.arange(0, 10000) / USRP_SAMP_RATE
        self.tx_waveform = 0.7 * np.exp(1j * 2 * np.pi * BASEBAND_OFFSET * tx_t).astype(np.complex64)
        self.tx_waveform = np.tile(self.tx_waveform, (1, 1))

    def extract_continuous_phase(self, iq_data, start_time):
        t = (start_time + np.arange(len(iq_data)) / USRP_SAMP_RATE) % (1.0 / BASEBAND_OFFSET)
        tx_ref = np.exp(-1j * 2 * np.pi * BASEBAND_OFFSET * t)
        mixed = iq_data * tx_ref

        raw_angle = np.angle(mixed)
        chunk_unwrapped = np.unwrap(raw_angle)

        phase_diff = raw_angle[0] - self.last_raw_phase
        wrapped_diff = (phase_diff + np.pi) % (2 * np.pi) - np.pi

        correct_start_phase = self.last_unwrapped_phase + wrapped_diff
        offset = correct_start_phase - chunk_unwrapped[0]
        chunk_unwrapped += offset

        self.last_raw_phase = raw_angle[-1]
        self.last_unwrapped_phase = chunk_unwrapped[-1]

        return chunk_unwrapped

    def _tx_worker(self):
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

    def _vmd_worker(self):
        print("\n[Algorithm] Waiting for the initial 15-second buffer...")
        while self.running and not self.is_stable:
            time.sleep(0.5)

        while self.running:
            with self.data_lock:
                window_data = np.copy(self.vital_buffer)
                current_time_axis = (self.total_vital_samples - self.record_start_sample) / FS_VITAL

            if np.std(window_data) < 1e-6:
                time.sleep(1.0)
                continue

            filtered_data = filtfilt(self.b_band, self.a_band, window_data)

            try:
                resp_sig = single_layer_vmd_extraction(filtered_data, FS_VITAL)
                rr = compute_rate_from_peaks(resp_sig, FS_VITAL, 1.2)

                with self.data_lock:
                    if rr > 0:
                        self.recorded_rpm_time.append(current_time_axis)
                        self.recorded_rpm.append(rr)

                if rr > 0:
                    print(f"[{time.strftime('%H:%M:%S')}] Current respiration rate: {rr:5.1f} RR(bpm)")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] [VMD error] Details: {e}")

            time.sleep(1.0)

    def start_radar_background(self):
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = [0]
        rx_stream = self.usrp.get_rx_stream(st_args)

        recv_buff = np.zeros((1, int(USRP_SAMP_RATE / 10)), dtype=np.complex64)
        metadata = uhd.types.RXMetadata()

        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        stream_cmd.stream_now = True
        rx_stream.issue_stream_cmd(stream_cmd)

        self.running = True

        tx_thread = threading.Thread(target=self._tx_worker)
        tx_thread.daemon = True
        tx_thread.start()

        vmd_thread = threading.Thread(target=self._vmd_worker)
        vmd_thread.daemon = True
        vmd_thread.start()

        print(f"[*] USRP transmit/receive active. Carrier: {RF_CENTER_FREQ / 1e9} GHz.")

        total_samples_processed = 0
        while self.running:
            num_rx = rx_stream.recv(recv_buff, metadata)
            if num_rx == 0: continue

            iq_chunk = recv_buff[0, :num_rx]
            current_time = total_samples_processed / USRP_SAMP_RATE

            raw_phase = self.extract_continuous_phase(iq_chunk, current_time)

            self.phase_remainder.extend(raw_phase)
            num_new_vital_samples = len(self.phase_remainder) // DECIMATION_FACTOR

            if num_new_vital_samples == 0:
                total_samples_processed += num_rx
                continue

            valid_len = num_new_vital_samples * DECIMATION_FACTOR
            samples_to_decimate = np.array(self.phase_remainder[:valid_len])
            self.phase_remainder = self.phase_remainder[valid_len:]

            reshaped_phase = samples_to_decimate.reshape(-1, DECIMATION_FACTOR)
            decimated_phase = np.mean(reshaped_phase, axis=1)

            live_filtered, self.zi = lfilter(self.b_live, self.a_live, decimated_phase, zi=self.zi)

            with self.data_lock:
                if num_new_vital_samples >= VITAL_BUFFER_SIZE:
                    self.vital_buffer[:] = decimated_phase[-VITAL_BUFFER_SIZE:]
                else:
                    self.vital_buffer = np.roll(self.vital_buffer, -num_new_vital_samples)
                    self.vital_buffer[-num_new_vital_samples:] = decimated_phase

                self.total_vital_samples += num_new_vital_samples

                if not self.is_stable and self.total_vital_samples >= VITAL_BUFFER_SIZE:
                    self.is_stable = True
                    self.record_start_sample = self.total_vital_samples
                    print(f"\n[*] Signal stabilized; collecting and displaying {RECORD_SECONDS} seconds of measured data...")
                    total_samples_processed += num_rx
                    continue

                if self.is_stable:
                    start_idx = self.total_vital_samples - num_new_vital_samples - self.record_start_sample
                    t_chunk = start_idx / FS_VITAL + np.arange(num_new_vital_samples) / FS_VITAL

                    self.recorded_time.extend(t_chunk.tolist())
                    self.recorded_signal.extend(live_filtered.tolist())

                    if t_chunk[-1] >= RECORD_SECONDS:
                        self.running = False

            total_samples_processed += num_rx

    def stop(self):
        self.running = False


if __name__ == "__main__":
    monitor = VitalSignMonitor()

    radar_thread = threading.Thread(target=monitor.start_radar_background)
    radar_thread.daemon = True
    radar_thread.start()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    line1, = ax1.plot([], [], color='blue', linewidth=1.5)
    line2, = ax2.plot([], [], marker='o', color='red', linestyle='-', markersize=6)

    ax1.set_xlabel("Time(s)")
    ax1.set_ylabel("Amplitude")
    ax1.set_xlim(0, RECORD_SECONDS)
    ax1.set_ylim(-1.2, 1.2)
    ax1.set_yticks([-1, 0, 1])
    ax1.grid(True, linestyle='--', alpha=0.6)

    ax2.set_xlabel("Time(s)")
    ax2.set_ylabel("RR(bpm)")
    ax2.set_xlim(0, RECORD_SECONDS)
    ax2.set_ylim(0, 35)
    ax2.set_yticks([0, 10, 20, 30])
    ax2.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()


    def update_gui(frame):
        if not monitor.running:
            plt.close(fig)
            return line1, line2

        with monitor.data_lock:
            if len(monitor.recorded_time) > 0:
                sig = np.clip(monitor.recorded_signal, -1.0, 1.0)
                line1.set_data(monitor.recorded_time, sig)

            if len(monitor.recorded_rpm_time) > 0:
                line2.set_data(monitor.recorded_rpm_time, monitor.recorded_rpm)

        return line1, line2


    ani = animation.FuncAnimation(fig, update_gui, interval=200, blit=False)

    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[*] Stopping transmission and worker threads...")
        monitor.stop()
        radar_thread.join(timeout=2.0)

        if len(monitor.recorded_time) > 0:
            np.savez('data/reference.npz',
                     time=np.array(monitor.recorded_time),
                     signal=np.array(monitor.recorded_signal),
                     rpm_time=np.array(monitor.recorded_rpm_time),
                     rpm=np.array(monitor.recorded_rpm))
            # print("\n=======================================================")
            # print("=======================================================")
