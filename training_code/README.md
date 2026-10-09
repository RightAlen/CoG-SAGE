# Minimal Training Code

This directory contains a compact training scaffold for the reported
color-evoked EEG decoding setting. It is intended to show the model and baseline
training path without releasing raw EEG or participant-identifying records.

## What Is Included

- `train_color_eeg.py`: a single-file PyTorch runner for:
  - `cog_sage`: compact CoG-SAGE-style raw EEG + covariance/session features + ordered-label heads.
  - `deepconvnet`: DeepConvNet-style convolutional baseline.
  - `eegnet`: EEGNet-style compact convolutional baseline.
  - `conformer_small`: lightweight convolutional self-attention baseline.
- `configs/minimal_training_config.json`: path-neutral defaults matching the public manuscript setting where possible.

## Data Interface

No EEG data are included. To run on permitted data, provide an `.npz` file with:

```text
eeg:      float array shaped (n_trials, n_channels, n_times)
labels:   int array shaped (n_trials,), values 0..6
sessions: int array shaped (n_trials,), anonymized session IDs
split:    optional string array with values train/val/test
```

The code never assumes local machine paths, subject names, raw acquisition file
names, or participant identifiers.

## No-Data Code Check

From the repository root:

```bash
python training_code/train_color_eeg.py check-models
```

This command instantiates the released model definitions and reports parameter
counts. It does not create, include, or simulate EEG data.

To train on permitted de-identified data:

```bash
python training_code/train_color_eeg.py train --data path/to/permitted_data.npz --model cog_sage --out results/cog_sage.json
python training_code/train_color_eeg.py train --data path/to/permitted_data.npz --model deepconvnet --out results/deepconvnet.json
```

## Reproducing Reported Numbers

The manuscript numbers are checked from de-identified released summaries:

```bash
python scripts/validate_public_artifact.py --root public_artifact
```

Raw EEG and full preprocessing are not part of the public release. Access to
de-identified raw or minimally processed EEG is subject to the
original consent scope and institutional policy.
