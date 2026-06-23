# Public Release Checklist

- [ ] Replace the temporary all-rights-reserved notice with the selected open-source license.
- [ ] Assign and include the final data license.
- [ ] Add the complete author list, affiliations, repository URL, paper DOI, and software DOI to `CITATION.cff`.
- [ ] Add the corresponding-author email to the root README.
- [ ] Pin every upstream branch/tag/commit in `third_party/sources.yml`.
- [ ] Verify licenses for TARE, SpotFi code, CSI firmware/code, model weights, and all copied assets.
- [ ] Confirm written permission and attribution for the NimbusRT-derived release.
- [ ] Deposit high-resolution point clouds and other large data in a DOI-backed archive.
- [ ] Install Git LFS before adding PLY and video files covered by `.gitattributes`.
- [ ] Regenerate `data/MANIFEST.tsv` and verify checksums.
- [ ] Remove `_local/`, `.idea/`, credentials, absolute paths, device serial numbers, and private metadata from the upload.
- [ ] Confirm that photographs and videos contain no unapproved people, locations, screens, or identifying metadata.
- [ ] Freeze Python, MATLAB, GNU Radio, UHD, CUDA, OptiX, and hardware versions used for the archival release.
- [ ] Add a minimal end-to-end example or explicitly state which stages require unreleased components.
- [ ] Run static checks and the released analyses in a clean environment.
- [ ] Create a versioned GitHub release and archive it with Zenodo or an equivalent service.
