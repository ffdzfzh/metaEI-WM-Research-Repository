# IMS Localization ORB Demonstration

`localize_ims_orb.py` demonstrates the visual front end used to identify the periodic IMS pattern in an indoor image:

1. load a reference IMS template and a scene image;
2. extract ORB keypoints and binary descriptors;
3. apply K-nearest-neighbor matching and a ratio test;
4. estimate a homography with RANSAC;
5. draw the detected IMS boundary and report the in-plane rotation estimate.

This is a compact demonstration, not the complete six-degree-of-freedom localization pipeline described in the manuscript. Full 6-DoF pose recovery additionally requires camera calibration and homography decomposition.

Inputs are stored in `image_match/` and `image/`. The script resolves these paths relative to its own location.
