# CoG-SAGE: Stable Color-Evoked EEG Decoding

Research materials for our paper accepted at **IEEE BIBM 2026**.

Yi Wang, Jiaxi Wang, Yongyuan Lin, Tao Ma, and Jianqiang Li.

## Overview

CoG-SAGE studies participant-specific, seven-class color-evoked EEG decoding. It combines posterior-channel EEG with covariance/session features, ordered color-label priors, and checkpoint stabilization.

The study uses 2,359 epochs from the primary participant (Sub1) and an exploratory 350-epoch dataset from a second participant (Sub2). Evaluation covers fixed-split, cross-validation, and held-out-session settings; the results do not establish population-level generalization.

[Framework figure](public_artifact/figures/figure2_overall_framework.pdf) · [Results and figures](public_artifact/README.md)

## Repository Structure

| Directory | Contents |
| --- | --- |
| [`training_code/`](training_code/README.md) | Minimal PyTorch training scaffold and data interface |
| [`configs/`](configs/) | Reported model configuration |
| [`public_artifact/`](public_artifact/README.md) | Result tables, predictions, split/seed metadata, and paper figures |
| [`scripts/`](scripts/) | Result validation and selected figure-generation scripts |

## Installation

Clone the repository and install the dependencies for training and plotting:

```bash
git clone https://github.com/RightAlen/CoG-SAGE.git
cd CoG-SAGE
python -m pip install -r requirements.txt
```

The result-validation script below uses only the Python standard library and can be run without installing these dependencies.

## Usage

### Validate released results

```bash
python scripts/validate_public_artifact.py --root public_artifact
```

This checks the released files and recomputes selected manuscript summaries from the included tables and predictions. A successful run reports `"status": "PASS"`.

### Run the training example

Check model construction without EEG data:

```bash
python training_code/train_color_eeg.py check-models
```

Train on your own permitted, preprocessed data:

```bash
python training_code/train_color_eeg.py train --data path/to/permitted_data.npz --model cog_sage --out results/cog_sage.json
```

The `.npz` file must contain `eeg`, `labels`, and `sessions` arrays, with optional `split` assignments. See the [training guide](training_code/README.md) for shapes, label conventions, and available baseline models.

The training scaffold illustrates the model and training workflow; it is not a complete end-to-end reproduction of all paper experiments. Reported results are checked separately using the validation command above.

### Generate figures

```bash
python scripts/draw_paradigm_timeline.py
python scripts/draw_overall_framework.py
```

Outputs are saved to `generated_figures/`. All four paper figures are available as [PDFs](public_artifact/figures/). The Fig. 3 attribution script is reference code; its required seed-aligned input exports are not included.

## Data Availability

De-identified result tables, predictions, and split/seed metadata are included in [`public_artifact/`](public_artifact/). Raw EEG and the full preprocessing pipeline are not included. Raw-data access is subject to consent scope and institutional policy; see [Code and Data Access](public_artifact/CODE_AND_DATA_ACCESS.md).

## Citation

If you find this work useful, please cite:

```bibtex
@inproceedings{wang2026cogsage,
  title = {{CoG-SAGE}: Stable Color-Evoked {EEG} Decoding},
  author = {Wang, Yi and Wang, Jiaxi and Lin, Yongyuan and Ma, Tao and Li, Jianqiang},
  booktitle = {2026 IEEE International Conference on Bioinformatics and Biomedicine (BIBM)},
  year = {2026},
  note = {Accepted for publication}
}
```

## License

See [LICENSE.md](LICENSE.md) for the terms covering the released code and materials.
