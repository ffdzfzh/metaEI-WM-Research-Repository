# USRP and GNU Radio Experiments

## Structure

| Directory | Purpose |
|---|---|
| `breath_detection/` | Continuous-wave transmit/receive, phase extraction, VMD processing, and respiration-rate estimation |
| `signal_transmission/` | GNU Radio QPSK flow graph, generated Python flow graph, and custom metric block |
| `media/images/` | Example transmitted image assets |
| `media/videos/` | Source, received-with-IMS, and received-without-IMS videos |

## Requirements

These programs require compatible Ettus USRP hardware, UHD, GNU Radio, the correct RF front end, and local safety/regulatory approval for the selected carrier and transmit power. The QPSK flow graph was generated with GNU Radio 3.10.1.1 and carries its file-level GPL-3.0 identifier.

The generated flow graph resolves `media/videos/trans.ts` relative to the repository. Hardware addresses, gain values, sample rates, clocking, and device serial numbers must still be checked for the target laboratory setup.

Do not treat these scripts as unattended deployment software. Verify RF connections, attenuation, antenna placement, and local spectrum regulations before transmission.
