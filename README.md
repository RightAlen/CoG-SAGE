# Anonymous Materials For Color-Evoked EEG Decoding

This repository mirrors the reviewer-facing result-checking materials for the BIBM submission. It provides derived tables, figure sources, split/seed metadata, configuration summaries, and validation scripts that can be shared without raw EEG files, machine-specific records, participant identifiers, or training records that could compromise anonymity.

## Contents

- `public_artifact/`: public tables, figures, split/seed metadata, split-role assignments, validation code, and access notes used by the manuscript.
- `scripts/validate_public_artifact.py`: standalone validation script for included files, row counts, CSV schemas, fixed-split role counts, fixed-split seed-run recomputation, Sub2 paired deltas, DeepConvNet paired comparisons, stimulus diagnostics, and selected manuscript values.
- `scripts/draw_paradigm_timeline.py`: source for the paradigm timeline figure.
- `scripts/draw_overall_framework.py`: source for the framework figure.
- `scripts/plot_model_decision_attribution.py`: reference source for the decision/attribution figure; the seed-aligned export files needed to rerun this plot are not included in the anonymous package.
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

## Scope

This anonymous release supports inspection of the reported aggregate values, table sources, and figure sources. It does not include raw EEG recordings, consent documents, ethics records, participant-identifying records, or non-release development records.

Full preprocessing, training, and evaluation runners are outside this anonymous result-checking package because they depend on non-public raw-data paths and acquisition records. Post-acceptance release will remove identifying details where permitted, and raw-data access will follow written consent and institutional permissions.
