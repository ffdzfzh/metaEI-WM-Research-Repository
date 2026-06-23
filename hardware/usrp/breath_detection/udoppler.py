import uhd
from uhd import libpyuhd as lib
import numpy as np
import scipy.io
import threading
import matplotlib.pyplot as plt
import time
from timeit import default_timer as timer

from myConstants import *
from myGUI import *
import myUSRP
from vital_dsp import process_vital_signs
import threading

# USRP selection
# usrpTX = myUSRP.Device("serial=30B0CED")
# #usrpTX.usrp.set_clock_source('external')
# usrpRX = myUSRP.Device("serial=30B0CED")
# #usrpRX.usrp.set_clock_source('external')
usrpTX = myUSRP.Device("")
usrpRX = myUSRP.Device("")

usrpTX.set_tx_config(fLO, fs, channelsTX, gainTX)
usrpRX.set_rx_config(fLO, fs, channelsRX, gainRX)
tx_buffer = 0.7 * np.array(np.exp(2j*np.pi*np.arange(0,ns)/ndiv), dtype=np.complex64)
usrpTX.start_tx_stream(tx_buffer)
usrpRX.start_rx_stream()

effective_phase_fs = 4e6 / ns

buffer_duration = 10
buffer_size = int(effective_phase_fs * buffer_duration)
phase_buffer = np.zeros(buffer_size)
pvals = np.zeros(ns)
dphase = 0
loop_index = 0
data_count = 0


def run_vmd_task(phase_data, fs):
    try:
        print("\n[Background] Running VMD respiration and heartbeat separation...")
        resp_sig, hb_sig, RR, HR = process_vital_signs(phase_data, fs)
        print(f"=================================")
        print(f"Respiration rate (RR): {RR:.1f} per minute")
        print(f"Heart rate (HR): {HR:.1f} per minute")
        print(f"=================================\n")
    except Exception as e:
        print(f"[Error] VMD processing failed: {e}")

print(f"USRP data collection is active; the first estimate is expected after {buffer_duration} seconds.")


while True:
    loop_index = loop_index + 1

    (x0,) = usrpRX.get_rx_buffer()

    X0 = np.fft.fftshift(np.fft.fft(x0, hrf * ns))
    S0 = 10 * np.log(np.abs(X0) / np.sqrt(ns) + 1e-12)
    k = np.argmax(S0)

    current_phase = np.angle(X0[k])
    phase_buffer = np.roll(phase_buffer, -1)
    phase_buffer[-1] = current_phase
    data_count += 1

    dphase = 180 / np.pi * current_phase
    pvals = np.concatenate(([dphase], pvals[0:ns - 1]), axis=None)

    if loop_index % 50 == 0:
        mplt0i.set_ydata(np.real(x0))
        mplt0q.set_ydata(np.imag(x0))
        mplt0s.set_ydata(pvals)
        refresh()

    update_interval = int(effective_phase_fs * 5)
    if data_count >= buffer_size and data_count % update_interval == 0:
        unwrapped_phase = np.unwrap(phase_buffer)

        t = threading.Thread(target=run_vmd_task, args=(unwrapped_phase, effective_phase_fs))
        t.daemon = True
        t.start()

    # mplt0s.set_ydata(pvals)
    # refresh()


# usrpTX.stop_tx_stream()
# usrpRX.stop_rx_stream()


