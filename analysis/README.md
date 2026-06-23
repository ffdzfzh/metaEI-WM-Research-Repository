# Analysis and Visualization

This directory contains scripts that inspect the released data and reproduce the main quantitative comparisons and visualizations. Run Python scripts from the repository root so that all paths resolve consistently.

## Evaluation

| Script | Purpose |
|---|---|
| `evaluation/evaluate_workplace.py` | Measured/simulated power and BER analysis for the workplace |
| `evaluation/evaluate_residential_apartment.py` | Equivalent analysis for the residential apartment |
| `evaluation/evaluate_multistory_corridor.py` | Equivalent analysis for the multistory corridor |
| `evaluation/summarize_results.py` | Consolidated statistics across the three scenarios |
| `evaluation/evaluate_video_quality.py` | SSIM, blockiness, and freeze/smoothness comparison for transmitted videos |

## Visualization

| Script | Input |
|---|---|
| `visualization/plot_breathing_results.py` | `data/breath_detection/respiration_data.npz` |
| `visualization/plot_constellations.py` | Corridor constellation CSV files |
| `visualization/plot_mobile_channel_capacity.py` | `data/human_tracking/capacity.xlsx` |
| `visualization/plot_radiation_patterns.py` | `data/radiation_patterns/scene1_area1.mat` |
| `visualization/view_point_cloud.py` | Released PLY point cloud |
| `visualization/view_semantic_point_cloud.py` | PLY point cloud plus SpatialLM semantic text |
| `visualization/view_scene_mesh.py` | OBJ/MTL scene mesh |
| `visualization/plot_power_maps_*.m` | JSON radio maps and STL scene geometry |
| `visualization/plot_symbiotic_communication_maps.m` | Corridor coding-state radio maps |

The scripts are research visualization programs rather than a unified command-line package. Default example inputs are declared near the start or end of each file. 
