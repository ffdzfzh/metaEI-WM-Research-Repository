# metaEI-WM Research Repository

This repository accompanies the manuscript 'Metasurface embodied intelligence through electromagnetic world model'. It organizes the released code and data used to construct semantic indoor environments, predict electromagnetic (EM) behavior, optimize information metasurface (IMS) coding patterns, operate USRP experiments, and evaluate the three demonstration scenarios.

> **Pre-publication status.** This is a staged research release, not yet the complete end-to-end system. Selected implementation details and large data products will be released after the paper is published and, where required, permission has been obtained from upstream authors.

![WM-metaEI overview](docs/figures/Fig1.png)

## System Logic

WM-metaEI is organized around the three modules described in the manuscript:

1. **Perception and representation.** A mobile platform localizes deployed IMS panels and radio sources, reconstructs dense RGB point clouds, and converts geometry into semantic and topological scene descriptions.
2. **EM dynamics prediction.** Scene geometry, semantic object classes, material assignments, transmitter coordinates, and IMS poses are converted into a radio-propagation model that predicts LoS, environmental multipath, and IMS-assisted paths.
3. **Decision and execution.** Dominant paths are back-projected to the IMS aperture, a modified Gerchberg-Saxton procedure computes a phase profile, and the result is quantized into hardware-executable coding states.

The released analysis layer links these modules to the workplace, residential-apartment, and multistory-corridor experiments reported in the paper.

## Repository Layout

```text
.
|-- analysis/                  # Evaluation and visualization scripts
|-- data/                      # Released measurements, simulations, and scene assets
|-- docs/                      # Figures, availability notes, and release guidance
|-- environment/               # Software dependency notes
|-- hardware/usrp/             # GNU Radio flow graphs and USRP acquisition code
|-- src/perception/            # IMS localization demonstration
|-- src/decision_execution/    # Gerchberg-Saxton coding optimization
|-- third_party/               # Upstream source, license, and citation registry
|-- CITATION.cff
|-- DATA_LICENSE.md
`-- LICENSE
```

The local directory `_local/` is intentionally ignored by Git. It contains working copies of third-party repositories, the high-resolution point clouds that exceed normal GitHub file limits, and code that is withheld during peer review.

## Release Scope

| Component | Current status | Location |
|---|---|---|
| Plotting and evaluation scripts | Released | `analysis/` |
| Workplace, residential, and corridor result data | Released | `data/` |
| Power maps, optimized codes, and radiation-pattern data | Released | `data/` |
| Scene meshes and semantic object descriptions | Partially released | `data/scene_models/` |
| IMS localization ORB demonstration | Released | `src/perception/` |
| Gerchberg-Saxton coding optimization | Released | `src/decision_execution/` |
| USRP/GNU Radio experiment files | Released | `hardware/usrp/` |
| Full Qwen-based agent orchestration | Not released in this version | Planned after publication |
| NimbusRT-derived semantic scene extension | Withheld | Planned after publication and upstream approval |
| EM object/material mapping library | Withheld | Planned after publication and upstream approval |
| End-to-end ray-tracing drivers | Partially released | `local/withheld_code/em_prediction` Planned all after publication and upstream approval |
| High-resolution workplace and apartment point clouds | Released | https://pan.quark.cn/s/275aae59c8c4 |

The withheld ray-tracing drivers implement: target-region back-projection onto the IMS aperture, baseline radio-map simulation without an IMS, and radio-map simulation with an IMS. Their public release depends on completing the manuscript review and resolving redistribution and attribution requirements for the NimbusRT-derived extension.

## Data and Scenarios

The repository uses the following stable scene mapping:

| Identifier used in raw filenames | Descriptive name |
|---|---|
| `scene1` | Workplace |
| `scene2` | Residential apartment |
| `scene3` | Multistory corridor |

See [data/README.md](data/README.md) for the file-level interpretation and the scripts associated with each dataset.

## Reproducing Released Analyses

Run commands from the repository root after installing the analysis dependencies:

```bash
python -m pip install -r environment/requirements-analysis.txt
```

Representative entry points are:

```bash
python analysis/visualization/plot_breathing_results.py
python analysis/visualization/plot_radiation_patterns.py
python analysis/evaluation/evaluate_workplace.py
python analysis/evaluation/evaluate_residential_apartment.py
python analysis/evaluation/evaluate_multistory_corridor.py
python analysis/evaluation/summarize_results.py
python analysis/evaluation/evaluate_video_quality.py
```

MATLAB plotting and coding scripts are documented in [analysis/README.md](analysis/README.md) and [src/decision_execution/gs_algorithm/README.md](src/decision_execution/gs_algorithm/README.md). Hardware programs require the specific USRP, GNU Radio, UHD, and RF configuration described in [hardware/usrp/README.md](hardware/usrp/README.md).

## Third-Party Software

Third-party repositories are **not vendored into the uploadable tree**. Each upstream package must be obtained from its original source and used under its own license. The relationship between WM-metaEI and Qwen-Agent, TARE, R3LIVE, SpatialLM, RoomFormer, SpotFi, the Linux 802.11n CSI Tool, and NimbusRT is documented in [third_party/README.md](third_party/README.md).

The upstream papers must be cited in scholarly work in addition to citing this repository and the WM-metaEI manuscript. A complete acquisition and attribution workflow is provided in [docs/THIRD_PARTY_WORKFLOW.md](docs/THIRD_PARTY_WORKFLOW.md).

## Citation

The final paper DOI and complete author list are not yet available. Before archival release, update `CITATION.cff` and replace this section with the publisher citation. Until then, cite the manuscript by title and cite every upstream method actually used in a reproduced pipeline.

## Licensing and Availability

This pre-publication package does not yet grant a general open-source license for unmarked WM-metaEI code. Files that contain their own SPDX identifier remain governed by that file-level license. Data are governed separately by [DATA_LICENSE.md](DATA_LICENSE.md). Third-party software remains governed exclusively by its upstream terms.

Before making the repository public as an open-source release, complete [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md), select an OSI-approved license for the authors' original code, assign a data license, pin all upstream revisions, and archive the release with a DOI.

## Contact

For daily maintenance, please contact one of the authors: [ZhenhaoFu@seu.edu.cn](mailto:ZhenhaoFu@seu.edu.cn).  
Please use GitHub issues only for questions about the released files; questions about unreleased components should be directed to [ZhenhaoFu@seu.edu.cn](mailto:ZhenhaoFu@seu.edu.cn).
