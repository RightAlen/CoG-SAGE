"""Compute reviewer-facing stimulus-bias diagnostics from public tables.

The script uses only de-identified held-out predictions and nominal stimulus
attributes. Outputs are descriptive diagnostics, not mechanistic tests.
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path


CLASS_ORDER = ["red", "orange", "yellow", "green", "cyan", "blue", "purple"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda idx: values[idx])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            out[order[k]] = rank
        i = j
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
    return pearson(ranks(xs), ranks(ys))


def hue_distance_deg(a: float, b: float) -> float:
    diff = abs(float(a) - float(b)) % 360.0
    return min(diff, 360.0 - diff)


def ring_distance(a: int, b: int, n: int = 7) -> int:
    diff = abs(int(a) - int(b))
    return min(diff, n - diff)


def rounded(value: float, digits: int = 6) -> str:
    if math.isnan(value):
        return "nan"
    return f"{value:.{digits}f}"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    pred_path = root / "tables" / "fixed_split_test_predictions_public.csv"
    stim_path = root / "metadata" / "stimulus_attributes_public.csv"
    predictions = read_csv(pred_path)
    stimuli = {row["color"]: row for row in read_csv(stim_path)}

    true_labels = [int(row["label"]) for row in predictions]
    pred_labels = [int(row["probability_mean_prediction"]) for row in predictions]
    hard_labels = [int(row["hard_vote_prediction"]) for row in predictions]

    pair_counts = Counter(zip(true_labels, pred_labels))
    true_counts = Counter(true_labels)
    pred_counts = Counter(pred_labels)

    class_rows: list[dict[str, object]] = []
    for idx, name in enumerate(CLASS_ORDER):
        tp = pair_counts[(idx, idx)]
        support = true_counts[idx]
        predicted = pred_counts[idx]
        recall = tp / support if support else float("nan")
        precision = tp / predicted if predicted else float("nan")
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else float("nan")
        hard_tp = sum(1 for t, p in zip(true_labels, hard_labels) if t == idx and p == idx)
        hard_recall = hard_tp / support if support else float("nan")
        stim = stimuli[name]
        class_rows.append(
            {
                "class_index": idx,
                "class_name": name,
                "support": support,
                "predicted_as_count": predicted,
                "probability_mean_recall": rounded(recall),
                "probability_mean_precision": rounded(precision),
                "probability_mean_f1": rounded(f1),
                "hard_vote_recall": rounded(hard_recall),
                "hsv_h_deg": stim["hsv_h_deg"],
                "hsv_s": stim["hsv_s"],
                "hsv_v": stim["hsv_v"],
                "relative_luminance_srgb": stim["relative_luminance_srgb"],
            }
        )

    class_fields = [
        "class_index",
        "class_name",
        "support",
        "predicted_as_count",
        "probability_mean_recall",
        "probability_mean_precision",
        "probability_mean_f1",
        "hard_vote_recall",
        "hsv_h_deg",
        "hsv_s",
        "hsv_v",
        "relative_luminance_srgb",
    ]
    write_csv(root / "tables" / "stimulus_bias_class_metrics_public.csv", class_rows, class_fields)

    confusion_rows: list[dict[str, object]] = []
    for true_idx, true_name in enumerate(CLASS_ORDER):
        for pred_idx, pred_name in enumerate(CLASS_ORDER):
            count = pair_counts[(true_idx, pred_idx)]
            rate = count / true_counts[true_idx] if true_counts[true_idx] else float("nan")
            true_stim = stimuli[true_name]
            pred_stim = stimuli[pred_name]
            confusion_rows.append(
                {
                    "true_class": true_name,
                    "predicted_class": pred_name,
                    "count": count,
                    "row_rate": rounded(rate),
                    "is_correct": int(true_idx == pred_idx),
                    "ring_distance": ring_distance(true_idx, pred_idx),
                    "hue_distance_deg": rounded(
                        hue_distance_deg(float(true_stim["hsv_h_deg"]), float(pred_stim["hsv_h_deg"])),
                        3,
                    ),
                    "abs_yrel_diff": rounded(
                        abs(float(true_stim["relative_luminance_srgb"]) - float(pred_stim["relative_luminance_srgb"]))
                    ),
                    "abs_value_diff": rounded(abs(float(true_stim["hsv_v"]) - float(pred_stim["hsv_v"]))),
                    "abs_saturation_diff": rounded(abs(float(true_stim["hsv_s"]) - float(pred_stim["hsv_s"]))),
                }
            )

    confusion_fields = [
        "true_class",
        "predicted_class",
        "count",
        "row_rate",
        "is_correct",
        "ring_distance",
        "hue_distance_deg",
        "abs_yrel_diff",
        "abs_value_diff",
        "abs_saturation_diff",
    ]
    write_csv(root / "tables" / "stimulus_bias_confusion_profile_public.csv", confusion_rows, confusion_fields)

    recall = [float(row["probability_mean_recall"]) for row in class_rows]
    precision = [float(row["probability_mean_precision"]) for row in class_rows]
    yrel = [float(row["relative_luminance_srgb"]) for row in class_rows]
    value = [float(row["hsv_v"]) for row in class_rows]
    saturation = [float(row["hsv_s"]) for row in class_rows]
    hue_sin = [math.sin(math.radians(float(row["hsv_h_deg"]))) for row in class_rows]
    hue_cos = [math.cos(math.radians(float(row["hsv_h_deg"]))) for row in class_rows]

    offdiag = [row for row in confusion_rows if row["is_correct"] == 0]
    offdiag_rate = [float(row["row_rate"]) for row in offdiag]
    offdiag_hue = [float(row["hue_distance_deg"]) for row in offdiag]
    offdiag_yrel = [float(row["abs_yrel_diff"]) for row in offdiag]
    offdiag_value = [float(row["abs_value_diff"]) for row in offdiag]

    corr_defs = [
        ("class_recall_vs_yrel", recall, yrel, "7 classes", "Class recall from seed-aligned probability predictions vs sRGB-derived relative luminance."),
        ("class_recall_vs_hsv_value", recall, value, "7 classes", "Class recall vs HSV value."),
        ("class_recall_vs_hsv_saturation", recall, saturation, "7 classes", "Class recall vs HSV saturation; saturation is constant for these seven classes."),
        ("class_precision_vs_yrel", precision, yrel, "7 classes", "Class precision vs sRGB-derived relative luminance."),
        ("class_recall_vs_hue_sin", recall, hue_sin, "7 classes", "Linear association with sine component of circular hue."),
        ("class_recall_vs_hue_cos", recall, hue_cos, "7 classes", "Linear association with cosine component of circular hue."),
        ("confusion_rate_vs_hue_distance", offdiag_rate, offdiag_hue, "42 directed off-diagonal class pairs", "Off-diagonal row-normalized confusion rate vs circular HSV hue distance."),
        ("confusion_rate_vs_abs_yrel_diff", offdiag_rate, offdiag_yrel, "42 directed off-diagonal class pairs", "Off-diagonal row-normalized confusion rate vs absolute relative-luminance difference."),
        ("confusion_rate_vs_abs_value_diff", offdiag_rate, offdiag_value, "42 directed off-diagonal class pairs", "Off-diagonal row-normalized confusion rate vs absolute HSV value difference."),
    ]
    corr_rows = []
    for name, xs, ys, unit, notes in corr_defs:
        corr_rows.append(
            {
                "analysis": name,
                "n": len(xs),
                "unit": unit,
                "pearson_r": rounded(pearson(xs, ys)),
                "spearman_r": rounded(spearman(xs, ys)),
                "notes": notes,
            }
        )

    corr_fields = ["analysis", "n", "unit", "pearson_r", "spearman_r", "notes"]
    write_csv(root / "tables" / "stimulus_bias_correlations_public.csv", corr_rows, corr_fields)

    print("Wrote stimulus bias diagnostics:")
    print(root / "tables" / "stimulus_bias_class_metrics_public.csv")
    print(root / "tables" / "stimulus_bias_confusion_profile_public.csv")
    print(root / "tables" / "stimulus_bias_correlations_public.csv")


if __name__ == "__main__":
    main()
