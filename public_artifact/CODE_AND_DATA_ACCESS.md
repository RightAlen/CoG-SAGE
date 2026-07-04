# Code and Data Access

## Included Now

This anonymous package includes public result tables, paired-run summaries, per-class decodability profiles, stimulus-attribute diagnostics, fixed-split sample and prediction summaries, stabilized DeepConvNet fixed-split prediction pairs, manuscript figures, split/seed metadata, an environment summary, and validation scripts.

Run the consistency check from this directory:

```bash
python scripts/validate_public_artifact.py --root .
```

## Code Release Boundary

The anonymous materials include validation code, released-table summaries, configuration values, selected plotting sources, and manuscript figure PDFs suitable for checking the reported aggregate values and paired fixed-split comparisons. Full preprocessing, training, evaluation, and raw-export plotting runners are outside this anonymous result-checking package because they depend on non-public raw-data paths and acquisition records. Any later code release is subject to removing identifying details where permitted. The model-configuration values needed to interpret the reported experiments are included in `metadata/model_configuration_public.csv`.

## Data Access Boundary

Raw EEG recordings are not included in this anonymous package. Access to raw recordings is subject to informed consent and institutional permissions. Post-acceptance data access will use either a de-identified release or a controlled-access route within the consent scope and institutional permissions.

Expected access classes are:

- Public without raw EEG: generated tables, anonymized split/seed metadata, manuscript figures, model-configuration summaries, validation code, and anonymized prediction/sample summaries.
- Available after acceptance when permitted: de-identified raw or minimally processed EEG needed to rerun preprocessing and training, distributed through a public release or controlled-access route subject to consent scope, institutional review, and any required data-use agreement.
- Not released by this package: consent forms, ethics-board records, participant-identifying records, acquisition notes, and machine-specific records.

If raw EEG access cannot be granted, the derived result tables, fixed-split sample/prediction summaries, stabilized DeepConvNet paired predictions, DeepConvNet paired-run tables, per-class decodability profiles, fold/session block summaries, and validation code can still support checking the reported aggregate values and rerunning the analysis on permitted data.

## License

Release terms for the included validation code, generated tables, metadata, and figures are stated in `LICENSE.md`. Raw EEG recordings, consent documents, and participant-identifying records are not licensed by this package.
