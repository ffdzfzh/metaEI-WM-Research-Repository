# Environment Notes

`requirements-analysis.txt` lists the import-level Python dependencies used by the released analysis and visualization scripts. Exact versions were not recoverable from the supplied folder and must be frozen from the authors' working environment before archival release.

Hardware programs additionally require UHD and GNU Radio. NimbusRT, CUDA, OptiX, Sionna, ROS, TARE, R3LIVE, SpatialLM, and RoomFormer belong to separate environments and should be installed from pinned upstream revisions rather than merged into one Python environment.
