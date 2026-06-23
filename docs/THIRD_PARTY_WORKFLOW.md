# Third-Party Acquisition, Attribution, and Release Workflow

Use this workflow for every external repository used by WM-metaEI.

1. **Classify the relationship.** Record whether the project is a conceptual reference, an installed dependency, a source-code dependency, or the base of a modified derivative.
2. **Use the upstream source.** Link to the original repository or project page. Do not upload an arbitrary downloaded folder whose origin cannot be verified.
3. **Read the license before copying.** A paper citation is not a software license. If no license is present, do not redistribute the code without written permission.
4. **Pin an exact revision.** Clone the repository, check out the branch/tag/commit actually used, and record the full commit hash in `third_party/sources.yml`.
5. **Preserve notices.** If source is redistributed or modified, retain the upstream copyright, license, and NOTICE files. Mark modified files clearly.
6. **Keep modifications isolated.** Prefer a small patch series, fork, or adapter package over silently editing a copied upstream tree. This makes authorship and future updates auditable.
7. **Cite the scholarly method.** Cite the upstream paper in the manuscript whenever its method contributed to the scientific pipeline, even if no source code is redistributed.
8. **Cite the software artifact.** Cite the repository, release, DOI, or commit in the README and software metadata when the implementation itself was used.
9. **Check model and data terms separately.** Model weights, training data, source code, and derived outputs can carry different licenses. SpatialLM is a clear example of mixed component and model licenses.
10. **Archive the final state.** At publication, tag the repository, create a release, archive it with Zenodo or an equivalent service, and add the DOI to `CITATION.cff` and the manuscript.

## Recommended Git Procedure

```bash
git clone <upstream-url> external/<project>
git -C external/<project> checkout <tag-or-commit>
git -C external/<project> rev-parse HEAD
```

Record the output commit and license in `third_party/sources.yml`. Do not commit `external/` unless redistribution is intentional and legally permitted. For most WM-metaEI references, installation instructions plus a pinned source record are preferable to vendoring.

## Modified NimbusRT Work

For the planned semantic scene extension:

1. identify every modified or added file relative to a pinned NimbusRT commit;
2. retain the Apache-2.0 license and any upstream notices;
3. add prominent modification notices to changed files;
4. separate the authors' EM material mapping tables from upstream code;
5. obtain any additional consent agreed with the NimbusRT authors; and
6. publish the extension as a clearly attributed fork or patch set.

## SpotFi Snapshot Warning

The locally collected SpotFi MATLAB folder lacks a reliable repository URL and top-level license. It must not be uploaded as third-party source in its current form. Cite the SpotFi paper, obtain code from a verifiable upstream source, and confirm the license before redistribution.
