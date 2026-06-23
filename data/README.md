# Released Data

This directory contains the currently released subset of simulated and measured WM-metaEI data.

## Scene Mapping

| Raw prefix | Scene name |
|---|---|
| `scene1` | Workplace |
| `scene2` | Residential apartment |
| `scene3` | Multistory corridor |

## Directory Contents

| Directory | Contents | Primary consumer |
|---|---|---|
| `breath_detection/` | Raw echo log, processed respiration signal, and reference/calculated rate data | `analysis/visualization/plot_breathing_results.py` |
| `optimized_codes/` | Optimized IMS coding matrices for target regions | Coding inspection and downstream hardware control |
| `radiation_patterns/` | Incident field, optimized phase, quantized code, target pattern, and synthesized pattern | `analysis/visualization/plot_radiation_patterns.py` |
| `power_maps/` | JSON radio maps for regional enhancement, mobile focusing, and symbiotic communication | MATLAB power-map scripts |
| `scene_models/` | OBJ, MTL, STL, preview images, one released PLY, and cleaned SpatialLM semantic text | Scene viewers and radio-map overlays |
| `human_tracking/` | Channel capacity with and without IMS assistance | `plot_mobile_channel_capacity.py` |
| `workplace/` | Measured and simulated sample-point power, BER, and constellation data | Workplace evaluation |
| `residential_apartment/` | Equivalent data for the residential apartment | Apartment evaluation |
| `multistory_corridor/` | Equivalent data for the corridor | Corridor evaluation |

## Power-Map Naming

- `sceneN_areaM.json`: scene-wide radio map for an optimized target-area code.
- `sceneN_noris.json`: reference map without an IMS contribution.
- `scene1_pointM.json`: mobile-user point focusing under an optimized code.
- `scene3_0.json` and `scene3_1.json`: the two IMS coding states used for symbiotic communication.

## Scene Assets

The `scene_models/sceneN.txt` files contain cleaned semantic object descriptions produced from SpatialLM output. OBJ/STL files support mesh visualization and power-map overlays. The high-resolution workplace and apartment PLY files are not in the uploadable tree because they are approximately 108.6 MB and 277.9 MB, respectively. They should be deposited in a DOI-backed data archive or tracked with Git LFS after the publication decision.

## Integrity

`MANIFEST.tsv` lists the relative path, byte size, and SHA-256 hash of every released data file. Regenerate it after any intentional data change.
