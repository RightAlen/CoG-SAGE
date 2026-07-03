# Anonymous Code Release For Color-Evoked EEG Decoding

This directory is a GitHub-ready anonymous release bundle for the BIBM submission. It mirrors the public result-checking materials and includes scripts that can be shared without raw EEG files, machine-specific records, participant identifiers, or training records that could compromise anonymity.

## Contents

- `public_artifact/`: public tables, figures, split/seed metadata, split-role assignments, validation code, and access notes used by the manuscript.
- `scripts/validate_public_artifact.py`: standalone checker for included files, row counts, CSV schemas, fixed-split role counts, fixed-split seed-run recomputation, Sub2 paired deltas, DeepConvNet paired comparisons, and selected manuscript values.
- `scripts/draw_paradigm_timeline.py`: source for the paradigm timeline figure.
- `scripts/draw_overall_framework.py`: source for the framework figure.
- `scripts/plot_model_decision_attribution.py`: source for the decision/attribution figure when seed-aligned export files are available.
- `configs/reported_model_config.json`: public configuration values for the reported model.
- `LICENSE.md`: release terms for included code and generated materials.

## Quick Check

From this directory:

```bash
python scripts/validate_public_artifact.py --root public_artifact
```

Expected result: the JSON report ends with `"status": "PASS"`.

The validation script uses only the Python standard library. The figure scripts require the packages listed in `requirements.txt`; after installing them, run:

```bash
python scripts/draw_paradigm_timeline.py
python scripts/draw_overall_framework.py
```

Generated files are written to `generated_figures/`.

The Fig. 3 plotting script requires seed-aligned export files and is included for transparency; the raw export files are not part of the anonymous package.

## Scope

This anonymous release supports result checking and figure/source inspection. It does not include raw EEG recordings, consent documents, ethics records, participant-identifying records, or non-release development records.

Preprocessing, training, and evaluation source code will be provided with anonymized paths and identifiers. After acceptance, the final release will provide a de-identified data release or controlled-access route when permitted by written consent and institutional permissions.

## Suggested Anonymous GitHub Layout

The contents of this directory can be pushed as the repository root. Keep the repository anonymous during review: do not add author names, institutional identifiers, machine-specific records, or non-anonymous contact details.
