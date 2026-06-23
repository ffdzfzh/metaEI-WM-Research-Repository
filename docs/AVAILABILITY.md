# Code and Data Availability

## Available in This Version

- processed and selected raw data supporting the released figures and tables;
- measured and simulated power and BER samples for three scenes;
- optimized codes, incident-field products, and radiation-pattern products;
- power maps for regional enhancement, mobile focusing, and symbiotic communication;
- scene meshes, semantic object text, and selected point-cloud data;
- IMS localization demonstration;
- Gerchberg-Saxton coding optimization;
- USRP/GNU Radio experiment files; and
- analysis and visualization scripts.

## Withheld During Review

- complete Qwen-based agent orchestration;
- the NimbusRT-derived extension that ingests PLY geometry and SpatialLM object labels;
- the EM object/material mapping library;
- end-to-end drivers for IMS back-projection and radio-map prediction with and without an IMS; and
- high-resolution workplace and residential-apartment point clouds.

The authors intend to release the withheld original components after publication. Release of modifications derived from NimbusRT is additionally subject to confirmation of upstream attribution and permission requirements. Large point clouds should be distributed through a durable data archive or Git LFS rather than ordinary Git history.

## Suggested Manuscript Statement

> Code and selected data supporting the findings of this study are available in the accompanying repository. The repository includes evaluation and visualization programs, metasurface coding optimization, USRP experiment files, selected scene representations, and processed measurement/simulation data. The complete semantic electromagnetic ray-tracing extension, material-mapping library, and agent orchestration are being withheld during peer review and will be released after publication, subject to applicable third-party permissions. Large high-resolution point clouds will be deposited in a persistent research-data archive. Third-party software is available from the original repositories under the respective licenses listed in the repository documentation.
