# BIBM Color-EEG Public Materials Package

This package contains public materials that match the anonymous BIBM manuscript.

## Contents

- `tables/`: reported numerical summaries, fixed-split seed runs, Sub2 seed-paired evidence, per-class decodability profiles, component-level paired evidence, channel-scope comparisons, fixed-split test predictions, Fig. 3 decision/attribution summaries, and DeepConvNet paired-run evidence in CSV format.
- `metadata/`: anonymized split and random-seed metadata, fixed-split sample manifest and split-role assignments, material scope, and environment summary.
- `figures/`: final figure PDFs used by the manuscript.
- `scripts/`: standard-library validation code for checking included files and recomputing reported summary values.
- `CODE_AND_DATA_ACCESS.md`: code-release and raw-data access boundary.
- `LICENSE.md`: release terms for the included code and generated public materials.

## Scope

The primary dataset is an anonymized multi-session participant dataset denoted Sub1, with 2,359 chromatic target epochs. A smaller second participant dataset, denoted Sub2, contains 350 chromatic target epochs and is used as a small-sample participant panel.

The package provides reported aggregate values, per-seed fixed-split rows, figures, split/seed metadata, fixed-split train/validation/test assignments, selected fixed-split predictions, run-level DeepConvNet comparisons, Sub2 paired deltas, per-class decodability profiles, channel-scope comparisons, and fold/session summaries described in the manuscript.

This anonymous release omits raw EEG, participant-identifying records, ethics documents, full preprocessing/training/evaluation runners, and machine-specific records. After acceptance, de-identified data or controlled access will be provided within consent scope and institutional policy, and runnable experiment code will be released where permitted. This release also includes a model-configuration table and explicit terms for the included materials.

## Reporting Conventions

- Accuracy and top-2 values are stored as proportions unless the column name ends with `_percent`.
- Standard deviations are sample standard deviations across the runs stated in each row.
- Sub2 rows form a small-sample feasibility and class-profile analysis; larger matched cohorts are required before population-level claims.
- Per-class decodability values describe model performance by class, not subjective color preference.
- Fixed-split seed rows recompute the five-seed means and sample standard deviations in the main result table.
- Fixed-split assignment rows identify the train, validation, and held-out test role for each anonymized sample index.
- Sub2 seed rows and paired deltas recompute the target-only reference comparisons used in the Sub2 panel.
- Run-level fold/seed and session/seed paired summaries describe robustness across repeated training runs; fold/session summaries aggregate repeated seeds within each block.
- Fixed-split McNemar summaries compare proposed and DeepConvNet predictions on the same held-out epochs for each seed.
- Component-level paired evidence reports full-model minus ablation differences over matched fixed-split seeds. Positive accuracy deltas favor the full model; negative error deltas indicate lower error for the full model.
- Channel-scope comparisons report the posterior-channel configuration and an all-16-channel rerun under the same split, seeds, window, and hyperparameters.
- DeepConvNet paired-run tables report proposed minus DeepConvNet deltas over matched fold/seed or held-out-session/seed units, including the original CE row and the matched-stabilization control.
- Fixed-split sample and prediction tables omit private filenames and participant aliases.
- The Fig. 3 seed-aligned decision/attribution summary is reported in `tables/model_feature_attribution_summary_public.csv`; `tables/fixed_split_test_predictions_public.csv` provides the matching held-out prediction labels.
- The closest-prior matrix is a public positioning table, not a numerical benchmark.

## Local Validation

From the package directory, run:

```bash
python scripts/validate_public_artifact.py --root .
```

The script checks included files, expected row counts, CSV schemas, fixed-split role counts, fixed-split seed-run recomputation, Sub2 paired-delta and top-2 consistency, per-class decodability values, selected manuscript-table values, component-level paired evidence, channel-scope comparisons, DeepConvNet paired-run deltas, Fig. 3 feature/attribution values, and fixed-split prediction membership in the anonymized sample manifest.
