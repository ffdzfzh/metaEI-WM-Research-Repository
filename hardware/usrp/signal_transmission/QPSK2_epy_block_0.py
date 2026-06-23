import numpy as np
from gnuradio import gr
import math
import time
import datetime
import os
from pathlib import Path


class monitor_metrics(gr.sync_block):
    """Monitor QPSK power, BER, capacity, and constellation samples."""

    def __init__(self, window_size=1000, symbol_rate=1500000):
        gr.sync_block.__init__(self,
                               name='QPSK Metrics Monitor',
                               in_sig=[np.complex64],
                               out_sig=[np.float32, np.float32]  # 0: Log_BER, 1: Cap_Mbps
                               )
        self.window_size = window_size
        self.symbol_rate = symbol_rate

        self.current_ber = 1.0
        self.current_cap = 0.0
        self.current_pwr = 0.0

        self.last_save_time = time.time()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).resolve().parents[3] / "outputs" / "usrp" / "constellation"
        output_dir.mkdir(parents=True, exist_ok=True)
        self.filename = str(output_dir / f"data_{timestamp}.csv")

        try:
            with open(self.filename, 'w') as f:
                f.write("Timestamp,Log10_BER,Capacity_Mbps,Rx_Power_dB\n")
            print(f"[INFO] Data will be saved to: {os.path.abspath(self.filename)}")
        except Exception as e:
            print(f"[ERROR] Cannot create file: {e}")

        self.constellation_buffer = np.zeros(2048, dtype=np.complex64)
        self.buffer_idx = 0
        self.buffer_full = False

    def work(self, input_items, output_items):
        in0 = input_items[0]
        n_input = len(in0)

        if n_input == 0:
            return 0

        if n_input >= len(self.constellation_buffer):
            self.constellation_buffer[:] = in0[-len(self.constellation_buffer):]
            self.buffer_idx = 0
            self.buffer_full = True
        else:
            space_left = len(self.constellation_buffer) - self.buffer_idx
            if n_input <= space_left:
                self.constellation_buffer[self.buffer_idx:self.buffer_idx + n_input] = in0
                self.buffer_idx += n_input
            else:
                self.constellation_buffer[self.buffer_idx:] = in0[:space_left]
                self.constellation_buffer[:n_input - space_left] = in0[space_left:]
                self.buffer_idx = n_input - space_left
                self.buffer_full = True

        rx_power = np.mean(np.abs(in0) ** 2)
        if rx_power < 1e-12: rx_power = 1e-12

        self.current_pwr = 10 * math.log10(rx_power)


        norm_factor = 1.0 / math.sqrt(rx_power)
        in0_norm = in0 * norm_factor

        decisions = np.sign(in0_norm.real) * 0.7071 + 1j * (np.sign(in0_norm.imag) * 0.7071)

        error_vector = in0_norm - decisions
        mean_err_power = np.mean(np.abs(error_vector) ** 2)

        if mean_err_power < 1e-12: mean_err_power = 1e-12

        snr_lin = 1.0 / mean_err_power

        # Capacity (Mbps) = Symbol_Rate * log2(1 + SNR) / 1e6
        cap_bits_per_sym = math.log2(1 + snr_lin)
        cap_mbps = (cap_bits_per_sym * self.symbol_rate) / 1e6

        eb_n0 = snr_lin / 2.0
        ber_linear = 0.5 * math.erfc(math.sqrt(eb_n0))
        if ber_linear < 1e-9: ber_linear = 1e-9
        ber_log = math.log10(ber_linear)

        self.current_ber = ber_linear
        self.current_cap = cap_mbps

        now = time.time()
        if now - self.last_save_time >= 1.0:
            try:
                with open(self.filename, 'a') as f:
                    f.write(f"{now},{ber_log:.4f},{cap_mbps:.4f},{self.current_pwr:.2f}\n")
                self.last_save_time = now
            except Exception:
                pass

        output_items[0][:] = ber_log
        output_items[1][:] = cap_mbps

        return n_input

    def __del__(self):
        """Append buffered constellation samples when the flow graph stops."""
        try:
            if not self.buffer_full:
                data_to_save = self.constellation_buffer[:self.buffer_idx]
            else:
                data_to_save = np.concatenate((self.constellation_buffer[self.buffer_idx:],
                                               self.constellation_buffer[:self.buffer_idx]))

            with open(self.filename, 'a') as f:
                f.write("\n---CONST_DATA_START---\n")
                f.write("I,Q\n")
                for c in data_to_save:
                    f.write(f"{c.real:.6f},{c.imag:.6f}\n")
            print("[INFO] Constellation data appended to CSV.")
        except Exception as e:
            print(f"[ERROR] Failed to save final constellation: {e}")
