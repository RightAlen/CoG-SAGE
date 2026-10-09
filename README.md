# CoG-SAGE: Stable Color-Evoked EEG Decoding

Research materials for **CoG-SAGE: Stable Color-Evoked EEG Decoding**, accepted as a **regular paper at IEEE BIBM 2026** (IEEE International Conference on Bioinformatics and Biomedicine), December 1–4, 2026, Dallas, TX, USA.

**Authors:** Yi Wang<sup>*</sup>, Jiaxi Wang<sup>*</sup>, Yongyuan Lin, Tao Ma, and Jianqiang Li<sup>†</sup>

**Affiliation:** School of Artificial Intelligence, Shenzhen University, Shenzhen, China

<sup>*</sup>Yi Wang and Jiaxi Wang are co-first authors. †Corresponding author: Jianqiang Li ([lijq@szu.edu.cn](mailto:lijq@szu.edu.cn)).

- [Conference website](https://www3.cs.stonybrook.edu/~bibm2026/)
- [Public repository](https://github.com/RightAlen/CoG-SAGE)
- Publication status: accepted; final proceedings citation and DOI will be added when available.

## Overview

CoG-SAGE (Color-Order Guided, Session-Aware Gated EEG) studies offline, participant-specific seven-class color-evoked EEG decoding. It combines posterior-channel EEG, covariance/session features, checkpoint stabilization, and ordered color-label priors. The primary dataset contains 2,359 epochs from one participant (Sub1); a smaller 350-epoch Sub2 dataset provides an exploratory participant profile. These results do not establish population-level generalization.

This repository provides derived tables, figure PDFs, selected plotting sources, de-identified split/seed metadata, configuration summaries, validation scripts, and a minimal training scaffold. Raw EEG and participant-identifying records are not included.

## Contents

- `public_artifact/`: public tables, figures, split/seed metadata, split-role assignments, validation code, and access notes used by the manuscript.
- `scripts/validate_public_artifact.py`: standalone validation script for included files, row counts, CSV schemas, fixed-split role counts, fixed-split seed-run recomputation, Sub2 paired deltas, DeepConvNet paired comparisons, stabilized fixed-split prediction checks, stimulus diagnostics, and selected manuscript values.
- `scripts/draw_paradigm_timeline.py`: source for the paradigm timeline figure.
- `scripts/draw_overall_framework.py`: source for the framework figure.
- `scripts/plot_model_decision_attribution.py`: reference source for the decision/attribution figure; the seed-aligned export files needed to rerun this plot are not included in the public package.
- `training_code/`: minimal training code for the proposed model and baseline families. It includes model definitions, a path-neutral NPZ data interface, and a no-data model-construction check; it does not include or generate EEG data.
- `configs/reported_model_config.json`: public configuration values for the reported model.
- `LICENSE.md`: release terms for included code and generated materials.

## Quick Validation

From this directory:

```bash
python scripts/validate_public_artifact.py --root public_artifact
```

Expected result: the JSON report includes `"status": "PASS"`.

The validation script uses only the Python standard library. The figure scripts require the packages listed in `requirements.txt`; after installing them, run:

```bash
python scripts/draw_paradigm_timeline.py
python scripts/draw_overall_framework.py
```

Generated files are written to `generated_figures/`.

The Fig. 3 plotting script is included as reference source. It is not part of the quick-check path because the seed-aligned export files used to generate the published figure are not included in this public package.

The minimal training scaffold can be inspected without data:

```bash
python training_code/train_color_eeg.py check-models
```

Training requires a permitted de-identified `.npz` file matching the interface in `training_code/README.md`.

## Scope

This release supports inspection of the reported aggregate values, paired comparison tables, figure PDFs, selected plotting sources, and minimal training-code structure. It does not include raw EEG recordings, generated EEG surrogates, consent documents, ethics records, participant-identifying records, or non-release development records.

Full preprocessing and raw-data export runners are outside this public materials package because they depend on non-public raw-data paths and acquisition records. Additional runner or raw-data access requires de-identification, consent scope, and institutional permission.

## Citation

Until the proceedings metadata are available, use this provisional citation; no DOI or page range has been assigned here:

```bibtex
@inproceedings{wang2026cogsage,
  title = {{CoG-SAGE}: Stable Color-Evoked {EEG} Decoding},
  author = {Wang, Yi and Wang, Jiaxi and Lin, Yongyuan and Ma, Tao and Li, Jianqiang},
  booktitle = {2026 IEEE International Conference on Bioinformatics and Biomedicine (BIBM)},
  year = {2026},
  note = {Accepted for publication}
}
```

## Acknowledgments

This research was supported by Stable Support Project of Shenzhen (Grant No. 20220809154139001) and Internal Fund of National Engineering Laboratory for Big Data System Computing Technology (Grant No. SZU-BDSC-IF2024-09).

## Data access and reproducibility

The released tables and predictions support verification of reported summaries. The minimal training scaffold is an illustrative implementation, not a complete end-to-end reproduction of every manuscript experiment. Raw-data access is subject to consent scope and institutional policy; acceptance does not imply an unrestricted EEG-data release. See [Code and Data Access](public_artifact/CODE_AND_DATA_ACCESS.md) and [training instructions](training_code/README.md).
