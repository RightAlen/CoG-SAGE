# Anonymous Materials For Color-Evoked EEG Decoding

This repository contains anonymous public materials accompanying the BIBM submission. It provides derived tables, figure PDFs, selected plotting sources, split/seed metadata, configuration summaries, and validation scripts that can be shared without raw EEG files, machine-specific records, participant identifiers, or training records that could compromise anonymity.

## Contents

- `public_artifact/`: public tables, figures, split/seed metadata, split-role assignments, validation code, and access notes used by the manuscript.
- `scripts/validate_public_artifact.py`: standalone validation script for included files, row counts, CSV schemas, fixed-split role counts, fixed-split seed-run recomputation, Sub2 paired deltas, DeepConvNet paired comparisons, stabilized fixed-split prediction checks, stimulus diagnostics, and selected manuscript values.
- `scripts/draw_paradigm_timeline.py`: source for the paradigm timeline figure.
- `scripts/draw_overall_framework.py`: source for the framework figure.
- `scripts/plot_model_decision_attribution.py`: reference source for the decision/attribution figure; the seed-aligned export files needed to rerun this plot are not included in the anonymous package.
- `training_code/`: anonymous minimal training code for the proposed model and baseline families. It includes model definitions, a path-neutral NPZ data interface, and a no-data model-construction check; it does not include or generate EEG data.
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

The Fig. 3 plotting script is included as reference source. It is not part of the quick-check path because the seed-aligned export files used to generate the published figure are not included in this anonymous package.

The anonymous training scaffold can be inspected without data:

```bash
python training_code/train_color_eeg.py check-models
```

Training requires a permitted de-identified `.npz` file matching the interface in `training_code/README.md`.

## Scope

This anonymous release supports inspection of the reported aggregate values, paired comparison tables, figure PDFs, selected plotting sources, and anonymous training-code structure. It does not include raw EEG recordings, generated EEG surrogates, consent documents, ethics records, participant-identifying records, or non-release development records.

Full preprocessing and raw-data export runners are outside this anonymous materials package because they depend on non-public raw-data paths and acquisition records. Additional runner or raw-data access requires de-identification, consent scope, and institutional permission.
