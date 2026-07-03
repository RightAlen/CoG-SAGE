"""Plot model decision and attribution diagnostics for the manuscript.

The figure summarizes class-wise decoding, confidence margins, color-ring
error distance, and time/frequency attribution from seed-aligned diagnostic
exports.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["svg.fonttype"] = "none"

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CLASS_NAMES = ["red", "orange", "yellow", "green", "cyan", "blue", "purple"]
CLASS_COLORS = {
    "red": "#d73027",
    "orange": "#f46d43",
    "yellow": "#fddf70",
    "green": "#1a9850",
    "cyan": "#00a6d6",
    "blue": "#4575b4",
    "purple": "#7b3294",
}


def load_archives(diagnostics_dir: Path) -> list[dict[str, np.ndarray]]:
    files = sorted(diagnostics_dir.glob("*_diagnostics.npz"))
    if not files:
        raise FileNotFoundError(f"No *_diagnostics.npz files found in {diagnostics_dir}")
    archives = []
    for path in files:
        loaded = np.load(path, allow_pickle=False)
        archives.append({key: loaded[key] for key in loaded.files})
    return archives


def aligned(archives: list[dict[str, np.ndarray]]) -> bool:
    first_idx = archives[0]["test_idx"]
    first_labels = archives[0]["labels"]
    return all(
        np.array_equal(first_idx, arc["test_idx"]) and np.array_equal(first_labels, arc["labels"])
        for arc in archives[1:]
    )


def combine(archives: list[dict[str, np.ndarray]]) -> tuple[dict[str, np.ndarray], str]:
    if not aligned(archives):
        raise ValueError("This no-tSNE diagnostic figure expects aligned held-out samples across seeds.")
    mean_keys = [
        "probs",
        "time_saliency_gradxinput",
        "band_channel_trueprob_drop",
        "srm_effective_sample_channel_band_gate",
        "srm_channel_band_gate",
    ]
    out = {
        "labels": archives[0]["labels"],
        "test_idx": archives[0]["test_idx"],
        "sessions": archives[0]["sessions"],
        "time_ms_after_onset": archives[0]["time_ms_after_onset"],
        "channel_names": archives[0]["channel_names"],
        "band_names": archives[0]["band_names"],
    }
    for key in mean_keys:
        if all(key in arc for arc in archives):
            out[key] = np.mean(np.stack([arc[key] for arc in archives], axis=0), axis=0)
    out["preds"] = np.argmax(out["probs"], axis=1)
    return out, "seed_aligned_mean"


def circular_distance(labels: np.ndarray, preds: np.ndarray) -> np.ndarray:
    diff = np.abs(labels - preds)
    return np.minimum(diff, len(CLASS_NAMES) - diff)


def per_class_accuracy(labels: np.ndarray, preds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    support = np.zeros(len(CLASS_NAMES), dtype=int)
    accuracy = np.zeros(len(CLASS_NAMES), dtype=float)
    for class_idx in range(len(CLASS_NAMES)):
        mask = labels == class_idx
        support[class_idx] = int(mask.sum())
        accuracy[class_idx] = float((preds[mask] == labels[mask]).mean()) if support[class_idx] else np.nan
    return accuracy, support


def write_per_sample_summary(path: Path, combined: dict[str, np.ndarray]) -> None:
    labels = combined["labels"].astype(int)
    preds = combined["preds"].astype(int)
    probs = combined["probs"]
    sorted_probs = np.sort(probs, axis=1)
    margins = sorted_probs[:, -1] - sorted_probs[:, -2]
    true_probs = probs[np.arange(len(labels)), labels]
    distances = circular_distance(labels, preds)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "sample_order",
                "test_idx",
                "true_class",
                "pred_class",
                "correct",
                "true_class_probability",
                "top1_probability",
                "top1_minus_top2_margin",
                "circular_error_distance",
            ]
        )
        for idx in range(len(labels)):
            writer.writerow(
                [
                    idx,
                    int(combined["test_idx"][idx]),
                    CLASS_NAMES[int(labels[idx])],
                    CLASS_NAMES[int(preds[idx])],
                    int(labels[idx] == preds[idx]),
                    f"{float(true_probs[idx]):.8f}",
                    f"{float(sorted_probs[idx, -1]):.8f}",
                    f"{float(margins[idx]):.8f}",
                    int(distances[idx]),
                ]
            )


def signed_imshow(ax, values, xlabels, ylabels, title, cbar_label):
    limit = float(np.nanmax(np.abs(values))) if values.size else 1.0
    limit = max(limit, 1e-9)
    im = ax.imshow(values, aspect="auto", origin="lower", cmap="coolwarm", vmin=-limit, vmax=limit)
    ax.set_title(title, fontsize=8.5)
    ax.set_xticks(range(len(xlabels)))
    ax.set_xticklabels(xlabels, rotation=45, ha="right", fontsize=6.5)
    ax.set_yticks(range(len(ylabels)))
    ax.set_yticklabels(ylabels, fontsize=6.5)
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cbar.set_label(cbar_label, fontsize=6.5)
    cbar.ax.tick_params(labelsize=6.5)


def plot(combined: dict[str, np.ndarray], out_prefix: Path) -> dict[str, object]:
    labels = combined["labels"].astype(int)
    preds = combined["preds"].astype(int)
    probs = combined["probs"]
    distances = circular_distance(labels, preds)
    sorted_probs = np.sort(probs, axis=1)
    margins = sorted_probs[:, -1] - sorted_probs[:, -2]
    true_probs = probs[np.arange(len(labels)), labels]
    class_acc, class_support = per_class_accuracy(labels, preds)

    channel_names = [str(x) for x in combined["channel_names"]]
    band_names = [str(x).replace("_", " ") for x in combined["band_names"]]
    time_ms = combined["time_ms_after_onset"]
    saliency = combined["time_saliency_gradxinput"].mean(axis=0)
    band_drop = combined.get("band_channel_trueprob_drop")
    srm_gate = combined.get("srm_effective_sample_channel_band_gate")
    if srm_gate is None and "srm_channel_band_gate" in combined:
        srm_gate = combined["srm_channel_band_gate"]
    elif srm_gate is not None:
        srm_gate = srm_gate.mean(axis=0)

    fig = plt.figure(figsize=(7.1, 5.25), constrained_layout=True)
    grid = fig.add_gridspec(2, 3, height_ratios=[0.9, 1.05])
    ax_class = fig.add_subplot(grid[0, 0])
    ax_margin = fig.add_subplot(grid[0, 1])
    ax_ring = fig.add_subplot(grid[0, 2])
    ax_time = fig.add_subplot(grid[1, 0])
    ax_srm = fig.add_subplot(grid[1, 1])
    ax_occ = fig.add_subplot(grid[1, 2])

    y_pos = np.arange(len(CLASS_NAMES))
    ax_class.barh(
        y_pos,
        class_acc,
        color=[CLASS_COLORS[name] for name in CLASS_NAMES],
        edgecolor="#222222",
        linewidth=0.35,
        alpha=0.92,
    )
    ax_class.axvline(1.0 / len(CLASS_NAMES), color="#444444", linewidth=0.8, linestyle="--")
    ax_class.set_title("(a) Per-class decodability", fontsize=8.5)
    ax_class.set_xlim(0.0, 0.85)
    ax_class.set_yticks(y_pos)
    ax_class.set_yticklabels(CLASS_NAMES, fontsize=6.5)
    ax_class.invert_yaxis()
    ax_class.tick_params(axis="x", labelsize=6.5)
    ax_class.set_xlabel("accuracy", fontsize=6.5)
    for y, value in zip(y_pos, class_acc):
        ax_class.text(min(value + 0.018, 0.82), y, f"{100 * value:.0f}%", va="center", fontsize=6.2)

    correct_mask = labels == preds
    margin_groups = [margins[correct_mask], margins[~correct_mask]]
    box = ax_margin.boxplot(
        margin_groups,
        labels=["correct", "error"],
        patch_artist=True,
        widths=0.55,
        showfliers=False,
    )
    for patch, color in zip(box["boxes"], ["#3b82f6", "#f97316"]):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
        patch.set_edgecolor("#222222")
    for median in box["medians"]:
        median.set_color("#111111")
        median.set_linewidth(1.1)
    rng = np.random.default_rng(2026)
    for x, values, color in [(1, margin_groups[0], "#1d4ed8"), (2, margin_groups[1], "#c2410c")]:
        if len(values):
            sample = values if len(values) <= 120 else rng.choice(values, size=120, replace=False)
            jitter = rng.uniform(-0.11, 0.11, size=len(sample))
            ax_margin.scatter(np.full(len(sample), x) + jitter, sample, s=8, alpha=0.32, color=color, edgecolors="none")
    ax_margin.set_title("(b) Prediction margin", fontsize=8.5)
    ax_margin.set_ylabel("top-1 minus top-2 probability", fontsize=6.5)
    ax_margin.tick_params(axis="both", labelsize=6.5)
    ax_margin.set_ylim(0.0, max(0.8, float(np.percentile(margins, 98)) * 1.05))

    distance_counts = np.array([(distances == value).sum() for value in range(4)], dtype=float)
    distance_props = distance_counts / len(distances)
    ring_colors = ["#2563eb", "#93c5fd", "#fbbf24", "#f97316"]
    ax_ring.bar(np.arange(4), distance_props, color=ring_colors, edgecolor="#222222", linewidth=0.35)
    ax_ring.set_title("(c) Circular error distance", fontsize=8.5)
    ax_ring.set_xticks(np.arange(4))
    ax_ring.set_xticklabels(["0", "1", "2", "3"], fontsize=6.5)
    ax_ring.set_xlabel("ring steps", fontsize=6.5)
    ax_ring.set_ylabel("held-out proportion", fontsize=6.5)
    ax_ring.tick_params(axis="y", labelsize=6.5)
    ax_ring.set_ylim(0, max(0.62, float(distance_props.max()) * 1.18))
    for x, value in enumerate(distance_props):
        ax_ring.text(x, value + 0.015, f"{100 * value:.0f}%", ha="center", va="bottom", fontsize=6.2)

    im_time = ax_time.imshow(
        saliency,
        aspect="auto",
        origin="lower",
        cmap="viridis",
        extent=[float(time_ms[0]), float(time_ms[-1]), -0.5, len(channel_names) - 0.5],
    )
    ax_time.set_title("(d) Temporal saliency", fontsize=8.5)
    ax_time.set_xlabel("Time after onset (ms)", fontsize=7)
    ax_time.set_ylabel("Channel", fontsize=7)
    ax_time.set_yticks(range(len(channel_names)))
    ax_time.set_yticklabels(channel_names, fontsize=6.5)
    ax_time.tick_params(axis="x", labelsize=6.5)
    cbar_time = fig.colorbar(im_time, ax=ax_time, fraction=0.046, pad=0.02)
    cbar_time.set_label("|grad x input|", fontsize=6.5)
    cbar_time.ax.tick_params(labelsize=6.5)

    if srm_gate is not None:
        signed_imshow(ax_srm, np.asarray(srm_gate).T, channel_names, band_names, "(e) SRM channel-band gate", "gate")
    else:
        ax_srm.text(0.5, 0.5, "SRM gate unavailable", ha="center", va="center", fontsize=8)
        ax_srm.set_axis_off()

    if band_drop is not None:
        drop_mean = np.asarray(band_drop).mean(axis=0).T
        signed_imshow(ax_occ, drop_mean, channel_names, band_names, "(f) Band occlusion sensitivity", "true-prob drop")
    else:
        ax_occ.text(0.5, 0.5, "Band occlusion unavailable", ha="center", va="center", fontsize=8)
        ax_occ.set_axis_off()

    for ext in ("pdf", "svg", "png"):
        fig.savefig(out_prefix.with_suffix(f".{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)

    return {
        "accuracy": float(np.mean(correct_mask)),
        "n_samples": int(len(labels)),
        "mean_true_class_probability": float(np.mean(true_probs)),
        "correct_mean_margin": float(np.mean(margins[correct_mask])),
        "error_mean_margin": float(np.mean(margins[~correct_mask])),
        "adjacent_error_rate": float(np.mean(distances == 1)),
        "nonadjacent_error_rate": float(np.mean(distances > 1)),
        "mean_circular_distance": float(np.mean(distances)),
        "per_class_accuracy": {
            name: float(class_acc[idx])
            for idx, name in enumerate(CLASS_NAMES)
        },
        "per_class_support": {
            name: int(class_support[idx])
            for idx, name in enumerate(CLASS_NAMES)
        },
        "time_saliency_max": float(np.max(saliency)),
        "time_saliency_mean": float(np.mean(saliency)),
        "srm_gate_absmax": float(np.max(np.abs(srm_gate))) if srm_gate is not None else float("nan"),
        "band_occlusion_max": float(np.max(band_drop)) if band_drop is not None else float("nan"),
        "band_occlusion_mean": float(np.mean(band_drop)) if band_drop is not None else float("nan"),
    }


def write_public_summary(path: Path, summary: dict[str, object]) -> None:
    rows = [
        ("n_samples", summary["n_samples"], "count", "Held-out epochs used for Fig. 3 diagnostic summary."),
        ("n_archives", summary["n_archives"], "count", "Five seed archives used in the seed-aligned summary."),
        ("combine_mode", summary["combine_mode"], "text", "Fig. 3 diagnostic combination mode."),
        ("accuracy", summary["accuracy"], "proportion", "Seed-aligned mean-probability accuracy used only for Fig. 3 diagnostics."),
        ("mean_true_class_probability", summary["mean_true_class_probability"], "probability", "Mean probability assigned to the true class."),
        ("correct_mean_margin", summary["correct_mean_margin"], "probability margin", "Mean top-1 minus top-2 probability margin for correct predictions."),
        ("error_mean_margin", summary["error_mean_margin"], "probability margin", "Mean top-1 minus top-2 probability margin for errors."),
        ("adjacent_error_rate", summary["adjacent_error_rate"], "proportion", "Held-out samples predicted one step away on the color ring."),
        ("nonadjacent_error_rate", summary["nonadjacent_error_rate"], "proportion", "Held-out samples predicted more than one step away on the color ring."),
        ("mean_circular_distance", summary["mean_circular_distance"], "ring steps", "Mean circular distance between true and predicted class."),
        ("time_saliency_max", summary["time_saliency_max"], "standardized attribution", "Maximum temporal gradient-times-input saliency."),
        ("time_saliency_mean", summary["time_saliency_mean"], "standardized attribution", "Mean temporal gradient-times-input saliency."),
        ("srm_gate_absmax", summary["srm_gate_absmax"], "gate magnitude", "Maximum absolute learned SRM gate value."),
        ("band_occlusion_max", summary["band_occlusion_max"], "probability drop", "Maximum channel-band occlusion drop."),
        ("band_occlusion_mean", summary["band_occlusion_mean"], "probability drop", "Mean channel-band occlusion drop."),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value", "unit", "notes"])
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot model decision and attribution diagnostics.")
    parser.add_argument("--diagnostics-dir", required=True)
    parser.add_argument("--out-prefix", default=str(ROOT / "paper" / "figures" / "figure3_model_feature_attribution"))
    parser.add_argument("--analysis-dir", default=str(ROOT / "paper" / "analysis"))
    args = parser.parse_args()

    diagnostics_dir = Path(args.diagnostics_dir)
    out_prefix = Path(args.out_prefix)
    analysis_dir = Path(args.analysis_dir)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    archives = load_archives(diagnostics_dir)
    combined, combine_mode = combine(archives)
    per_sample_path = analysis_dir / f"{out_prefix.stem}_decision_summary.csv"
    write_per_sample_summary(per_sample_path, combined)
    summary = plot(combined, out_prefix)
    summary.update(
        {
            "diagnostics_dir": str(diagnostics_dir),
            "n_archives": len(archives),
            "combine_mode": combine_mode,
            "out_prefix": str(out_prefix),
            "decision_summary_csv": str(per_sample_path),
        }
    )
    summary_path = analysis_dir / f"{out_prefix.stem}_summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_public_summary(ROOT / "paper" / "public_artifact" / "tables" / "model_feature_attribution_summary_public.csv", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
