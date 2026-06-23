# Gerchberg-Saxton IMS Coding

## Files

| File | Role |
|---|---|
| `GS.m` | Main far-field Gerchberg-Saxton optimization example |
| `focus_ASK.m` | Near-field focusing code with multiple candidate targets |
| `Creat_FarField_Metrix.m` | Far-field forward and conjugate-backward propagation operators |
| `Creat_metrix.m` | Near-field propagation-matrix construction |
| `codeGen.m` | Maps the optimized array to the controller/sub-board bit stream |
| `array2imageshow.m` | Reshapes array vectors for visualization |
| `data2array.m` | Data reshaping utility |
| `scan_data/` | Measured incident amplitude/phase scans |

## Scan Geometry

All scans place the antenna phase center 61.5 cm from the metasurface center. Each MAT file contains a 128 x 128 matrix over a 64 cm x 64 cm square sampled every 0.5 cm. See [scan_data/README.md](scan_data/README.md) for the renamed files and the original-name mapping.

`GS.m` currently selects `normal_incidence_61p5cm.mat`. Change the selected scan only after confirming that the frequency index, metasurface dimensions, element spacing, and sampled incident-field orientation match the intended hardware.
