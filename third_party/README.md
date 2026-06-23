# Third-Party Software Registry

Third-party source trees are not included in the uploadable repository. Obtain them from the original projects and obey each upstream license, model license, and data license.

| Project | Role in WM-metaEI | Relationship | Upstream terms observed in the supplied snapshot |
|---|---|---|---|
| [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | Reference framework for agent planning, tool use, and memory | Architectural reference; not vendored | Apache-2.0 |
| [TARE Planner](https://github.com/caochao39/tare_planner) | Autonomous exploration and coverage planning | External perception dependency/reference | No top-level license found in the supplied snapshot; verify upstream before redistribution |
| [R3LIVE](https://github.com/hku-mars/r3live) | LiDAR-camera-IMU fusion and dense RGB point-cloud reconstruction | External perception dependency | Upstream README states GPLv2 and an academic-use/commercial-contact notice |
| [SpatialLM](https://github.com/manycore-research/SpatialLM) | Semantic objects and structured scene-as-code from point clouds | External model/code dependency | Mixed terms: model, encoder, code, and weights use different licenses; inspect the selected model card |
| [RoomFormer](https://github.com/ywyue/RoomFormer) | Room topology and floor-plan reconstruction | External perception dependency | MIT |
| SpotFi | AoA/ToF processing principle for CSI-based source localization | Method reference; local code provenance unresolved | Do not redistribute the local snapshot until origin and license are confirmed |
| [Linux 802.11n CSI Tool](https://github.com/dhalperi/linux-80211n-csitool-supplementary) | Intel 5300 CSI acquisition and firmware support | Hardware/software prerequisite | Kernel, driver, firmware, and supplementary code have component-specific terms |
| [newer-kernel CSI port](https://github.com/spanev/linux-80211n-csitool) | Reference for newer Linux kernels | Optional external reference | Verify the selected branch and included component licenses |
| [NimbusRT](https://github.com/nvaara/NimbusRT) | Point-cloud ray launching and EM propagation base | Base of planned modified extension | Apache-2.0 in the supplied snapshot; changed files must carry modification notices |

## Scientific Citations

At minimum, cite the upstream papers corresponding to methods actually used:

- Cao et al., **TARE: A Hierarchical Framework for Efficiently Exploring Complex 3D Environments**, RSS 2021, and/or the relevant later TARE publication.
- Lin and Zhang, **R3LIVE: A Robust, Real-time, RGB-colored, LiDAR-Inertial-Visual Tightly-Coupled State Estimation and Mapping Package**, ICRA 2022.
- Mao et al., **SpatialLM: Training Large Language Models for Structured Indoor Modeling**, NeurIPS 2025.
- Yue et al., **Connecting the Dots: Floorplan Reconstruction Using Two-Level Queries**, CVPR 2023.
- Kotaru et al., **SpotFi: Decimeter Level Localization Using WiFi**, SIGCOMM 2015.
- Vaara et al., the NimbusRT-related point-cloud ray-launching publication matching the branch actually used.

Use [../docs/THIRD_PARTY_WORKFLOW.md](../docs/THIRD_PARTY_WORKFLOW.md) before adding, modifying, or publishing any upstream code.
