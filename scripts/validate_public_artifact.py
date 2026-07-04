#!/usr/bin/env python3
"""Validate the public materials package without private project files.

The script intentionally uses only the Python standard library so readers can
run it from the artifact directory.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path


PUBLIC_TEXT_PATTERNS = [
    ("local drive path", re.compile(r"\b[A-Za-z]:[\\/]")),
    ("home-directory path", re.compile(r"[\\/][Uu]sers[\\/]")),
]

TEXT_SUFFIXES = {".csv", ".md", ".txt", ".py"}


def csv_header(header: str) -> list[str]:
    return header.split(",")


EXPECTED_COUNTS = {
    "metadata/artifact_scope_public.csv": 20,
    "metadata/splits_and_seeds.csv": 5,
    "tables/fixed_split_seed_runs_public.csv": 50,
    "tables/main_results_public.csv": 12,
    "tables/ablation_public.csv": 10,
    "tables/additional_controls_public.csv": 6,
    "tables/color_neighborhood_error_public.csv": 4,
    "tables/sub2_seed_runs_public.csv": 30,
    "tables/sub2_paired_deltas_public.csv": 25,
    "tables/subject_decodability_per_class_public.csv": 7,
    "tables/component_paired_evidence_public.csv": 9,
    "tables/window_sensitivity_public.csv": 3,
    "tables/deepconvnet_paired_evidence_public.csv": 6,
    "tables/deepconvnet_fixedsplit_mcnemar_public.csv": 6,
    "tables/deepconvnet_session_stratified_5fold_paired_runs_public.csv": 25,
    "tables/deepconvnet_loso_paired_runs_public.csv": 20,
    "tables/deepconvnet_stabilized_session_stratified_5fold_paired_runs_public.csv": 25,
    "tables/deepconvnet_stabilized_loso_paired_runs_public.csv": 20,
    "tables/model_feature_attribution_summary_public.csv": 15,
    "tables/channel_scope_summary_public.csv": 2,
    "tables/channel_scope_paired_public.csv": 5,
    "metadata/model_configuration_public.csv": 29,
    "metadata/stimulus_attributes_public.csv": 7,
    "metadata/closest_prior_matrix_public.csv": 3,
    "metadata/fixed_split_sample_manifest_public.csv": 2359,
    "metadata/fixed_split_assignments_public.csv": 2359,
    "tables/fixed_split_test_predictions_public.csv": 472,
}

EXPECTED_HEADERS = {
    "metadata/artifact_scope_public.csv": csv_header("item,status,public_location,notes"),
    "metadata/closest_prior_matrix_public.csv": csv_header("study_family,citations,main_setting,contribution_to_surrounding_evidence,relevance_to_this_work"),
    "metadata/fixed_split_assignments_public.csv": csv_header("sample_idx,session_index,epoch_idx,raw_label,label,label_name,split_role,split_seed,val_seed"),
    "metadata/fixed_split_sample_manifest_public.csv": csv_header("sample_idx,session_index,epoch_idx,raw_label,label,label_name"),
    "metadata/model_configuration_public.csv": csv_header("parameter,value,scope,notes"),
    "metadata/stimulus_attributes_public.csv": csv_header("color,trigger_id,srgb_hex,psychopy_rgb,hsv_h_deg,hsv_s,hsv_v,relative_luminance_srgb"),
    "metadata/splits_and_seeds.csv": csv_header("dataset,role,total_chromatic_target_epochs,train_epochs,validation_epochs,test_epochs,random_seeds,selection_rule,notes"),
    "tables/ablation_public.csv": csv_header("variant,runs,accuracy_mean,accuracy_sd,kappa_mean,kappa_sd,top2_mean,top2_sd,interpretation"),
    "tables/additional_controls_public.csv": csv_header("control_family,runs,validation_accuracy_percent,validation_accuracy_sd_percent,test_accuracy_percent,test_accuracy_sd_percent,test_kappa_mean,test_kappa_sd,test_top2_percent,test_top2_sd_percent,interpretation"),
    "tables/channel_scope_paired_public.csv": csv_header("seed,posterior6_channel_set,posterior6_n_channels,posterior6_train_samples,posterior6_val_samples,posterior6_test_samples,posterior6_best_epoch,posterior6_final_val_acc,posterior6_test_acc,posterior6_test_kappa,posterior6_test_top2,all16_channel_set,all16_n_channels,all16_train_samples,all16_val_samples,all16_test_samples,all16_best_epoch,all16_final_val_acc,all16_test_acc,all16_test_kappa,all16_test_top2,delta_all16_minus_posterior6_test_acc,delta_all16_minus_posterior6_test_kappa,delta_all16_minus_posterior6_test_top2,delta_all16_minus_posterior6_acc_pp"),
    "tables/channel_scope_summary_public.csv": csv_header("channel_scope,n_seeds,n_channels_mean,train_samples,val_samples,test_samples,test_acc_mean,test_acc_sd,test_kappa_mean,test_kappa_sd,test_top2_mean,test_top2_sd,best_epoch_mean,best_epoch_sd,paired_delta_vs_posterior6_test_acc_mean,paired_delta_vs_posterior6_test_acc_sd,paired_ttest_p_test_acc,wilcoxon_p_test_acc,paired_delta_vs_posterior6_test_kappa_mean,paired_delta_vs_posterior6_test_kappa_sd,paired_ttest_p_test_kappa,wilcoxon_p_test_kappa,paired_delta_vs_posterior6_test_top2_mean,paired_delta_vs_posterior6_test_top2_sd,paired_ttest_p_test_top2,wilcoxon_p_test_top2"),
    "tables/color_neighborhood_error_public.csv": csv_header("method,runs,accuracy_mean,accuracy_sd,top2_mean,top2_sd,observed_nonadjacent_error_mean,observed_nonadjacent_error_sd,observed_mean_circular_distance,observed_mean_circular_distance_sd,random_order_nonadjacent_error_mean,random_order_nonadjacent_error_sd,random_order_mean_circular_distance,random_order_mean_circular_distance_sd,interpretation"),
    "tables/component_paired_evidence_public.csv": csv_header("variant,component_tested,paired_seeds,matched_test_labels_and_indices,full_minus_variant_accuracy_delta_pp_mean,full_minus_variant_accuracy_delta_pp_sd,full_minus_variant_accuracy_delta_pp_ci95,accuracy_positive_seeds,accuracy_negative_seeds,accuracy_tied_seeds,accuracy_sign_p,full_minus_variant_kappa_delta_mean,full_minus_variant_kappa_delta_sd,full_minus_variant_kappa_delta_ci95,full_minus_variant_top2_delta_pp_mean,full_minus_variant_top2_delta_pp_sd,full_minus_variant_top2_delta_pp_ci95,full_minus_variant_nonadjacent_error_delta_pp_mean,full_minus_variant_nonadjacent_error_delta_pp_sd,full_minus_variant_nonadjacent_error_delta_pp_ci95,full_minus_variant_circular_distance_delta_mean,full_minus_variant_circular_distance_delta_sd,full_minus_variant_circular_distance_delta_ci95,interpretation"),
    "tables/window_sensitivity_public.csv": csv_header("window,seed_count,accuracy_mean,accuracy_sd,kappa_mean,kappa_sd,top2_mean,top2_sd"),
    "tables/deepconvnet_fixedsplit_mcnemar_public.csv": csv_header("comparison,seed,n_trials,proposed_correct_deepconvnet_wrong,proposed_wrong_deepconvnet_correct,accuracy_delta,mcnemar_exact_p,scope"),
    "tables/deepconvnet_loso_paired_runs_public.csv": csv_header("protocol,heldout_session_index,seed,proposed_accuracy,deepconvnet_accuracy,accuracy_delta,proposed_kappa,deepconvnet_kappa,kappa_delta,proposed_top2,deepconvnet_top2,top2_delta"),
    "tables/deepconvnet_paired_evidence_public.csv": csv_header("comparison,scope,units,positive_count,negative_count,tie_count,accuracy_delta_pp,exact_p,interpretation"),
    "tables/deepconvnet_session_stratified_5fold_paired_runs_public.csv": csv_header("protocol,fold_index,seed,proposed_accuracy,deepconvnet_accuracy,accuracy_delta,proposed_kappa,deepconvnet_kappa,kappa_delta,proposed_top2,deepconvnet_top2,top2_delta"),
    "tables/deepconvnet_stabilized_session_stratified_5fold_paired_runs_public.csv": csv_header("protocol,fold_index,seed,proposed_accuracy,deepconvnet_stabilized_accuracy,accuracy_delta,proposed_kappa,deepconvnet_stabilized_kappa,kappa_delta,proposed_top2,deepconvnet_stabilized_top2,top2_delta"),
    "tables/deepconvnet_stabilized_loso_paired_runs_public.csv": csv_header("protocol,heldout_session_index,seed,proposed_accuracy,deepconvnet_stabilized_accuracy,accuracy_delta,proposed_kappa,deepconvnet_stabilized_kappa,kappa_delta,proposed_top2,deepconvnet_stabilized_top2,top2_delta"),
    "tables/fixed_split_seed_runs_public.csv": csv_header("method,role,seed,split_seed,val_seed,selection_split,train_samples,validation_samples,test_samples,accuracy,kappa,top2,selection_rule"),
    "tables/fixed_split_test_predictions_public.csv": csv_header("sample_idx,session_index,epoch_idx,raw_label,label,label_name,probability_mean_prediction,hard_vote_prediction"),
    "tables/main_results_public.csv": csv_header("method,role,runs,accuracy_mean,accuracy_sd,kappa_mean,kappa_sd,top2_mean,top2_sd,notes"),
    "tables/model_feature_attribution_summary_public.csv": csv_header("metric,value,unit,notes"),
    "tables/robustness_public.csv": csv_header("protocol,method,role,runs,accuracy_mean_percent,accuracy_sd_percent,top2_mean_percent,top2_sd_percent,paired_delta_accuracy_vs_deepconvnet_pp,paired_sign_summary,exact_sign_p,notes"),
    "tables/sub2_paired_deltas_public.csv": csv_header("reference_method,comparator_method,seed,reference_accuracy,comparator_accuracy,reference_minus_comparator_accuracy_delta_pp,direction"),
    "tables/sub2_panel_public.csv": csv_header("method,test_dataset,runs,source_train_epochs,source_validation_epochs,target_train_epochs,target_validation_epochs,target_test_epochs,accuracy_mean_percent,accuracy_sd_percent,kappa_mean,kappa_sd,top2_mean_percent,top2_sd_percent,interpretation"),
    "tables/sub2_seed_runs_public.csv": csv_header("method,seed,split_seed,val_seed,selection_split,source_train_samples,source_validation_samples,target_train_samples,target_validation_samples,target_test_samples,accuracy,kappa,top2,chance_accuracy,accuracy_delta_vs_chance_pp"),
    "tables/subject_decodability_per_class_public.csv": csv_header("class_name,sub1_proposed_accuracy_mean,sub1_proposed_accuracy_sd,sub1_equal_n_target_only_accuracy_mean,sub1_equal_n_target_only_accuracy_sd,sub2_target_only_accuracy_mean,sub2_target_only_accuracy_sd,sub2_minus_sub1_equal_n_accuracy_diff,bootstrap_ci95_low,bootstrap_ci95_high,bootstrap_p_two_sided,interpretation"),
}

NUMERIC_FIELDS = {
    "metadata/fixed_split_assignments_public.csv": [
        "sample_idx",
        "session_index",
        "epoch_idx",
        "label",
        "split_seed",
        "val_seed",
    ],
    "metadata/fixed_split_sample_manifest_public.csv": [
        "sample_idx",
        "session_index",
        "epoch_idx",
        "label",
    ],
    "metadata/splits_and_seeds.csv": [
        "total_chromatic_target_epochs",
        "train_epochs",
        "validation_epochs",
        "test_epochs",
    ],
    "metadata/stimulus_attributes_public.csv": [
        "trigger_id",
        "hsv_h_deg",
        "hsv_s",
        "hsv_v",
        "relative_luminance_srgb",
    ],
    "tables/main_results_public.csv": [
        "runs",
        "accuracy_mean",
        "accuracy_sd",
        "kappa_mean",
        "kappa_sd",
        "top2_mean",
        "top2_sd",
    ],
    "tables/ablation_public.csv": [
        "runs",
        "accuracy_mean",
        "accuracy_sd",
        "kappa_mean",
        "kappa_sd",
        "top2_mean",
        "top2_sd",
    ],
    "tables/additional_controls_public.csv": [
        "runs",
        "validation_accuracy_percent",
        "validation_accuracy_sd_percent",
        "test_accuracy_percent",
        "test_accuracy_sd_percent",
        "test_kappa_mean",
        "test_kappa_sd",
        "test_top2_percent",
        "test_top2_sd_percent",
    ],
    "tables/channel_scope_paired_public.csv": [
        "seed",
        "posterior6_n_channels",
        "posterior6_train_samples",
        "posterior6_val_samples",
        "posterior6_test_samples",
        "posterior6_best_epoch",
        "posterior6_final_val_acc",
        "posterior6_test_acc",
        "posterior6_test_kappa",
        "posterior6_test_top2",
        "all16_n_channels",
        "all16_train_samples",
        "all16_val_samples",
        "all16_test_samples",
        "all16_best_epoch",
        "all16_final_val_acc",
        "all16_test_acc",
        "all16_test_kappa",
        "all16_test_top2",
        "delta_all16_minus_posterior6_test_acc",
        "delta_all16_minus_posterior6_test_kappa",
        "delta_all16_minus_posterior6_test_top2",
        "delta_all16_minus_posterior6_acc_pp",
    ],
    "tables/channel_scope_summary_public.csv": [
        "n_seeds",
        "n_channels_mean",
        "train_samples",
        "val_samples",
        "test_samples",
        "test_acc_mean",
        "test_acc_sd",
        "test_kappa_mean",
        "test_kappa_sd",
        "test_top2_mean",
        "test_top2_sd",
        "best_epoch_mean",
        "best_epoch_sd",
        "paired_delta_vs_posterior6_test_acc_mean",
        "paired_delta_vs_posterior6_test_acc_sd",
        "paired_ttest_p_test_acc",
        "wilcoxon_p_test_acc",
        "paired_delta_vs_posterior6_test_kappa_mean",
        "paired_delta_vs_posterior6_test_kappa_sd",
        "paired_ttest_p_test_kappa",
        "wilcoxon_p_test_kappa",
        "paired_delta_vs_posterior6_test_top2_mean",
        "paired_delta_vs_posterior6_test_top2_sd",
        "paired_ttest_p_test_top2",
        "wilcoxon_p_test_top2",
    ],
    "tables/color_neighborhood_error_public.csv": [
        "runs",
        "accuracy_mean",
        "accuracy_sd",
        "top2_mean",
        "top2_sd",
        "observed_nonadjacent_error_mean",
        "observed_nonadjacent_error_sd",
        "observed_mean_circular_distance",
        "observed_mean_circular_distance_sd",
        "random_order_nonadjacent_error_mean",
        "random_order_nonadjacent_error_sd",
        "random_order_mean_circular_distance",
        "random_order_mean_circular_distance_sd",
    ],
    "tables/component_paired_evidence_public.csv": [
        "paired_seeds",
        "full_minus_variant_accuracy_delta_pp_mean",
        "full_minus_variant_accuracy_delta_pp_sd",
        "full_minus_variant_accuracy_delta_pp_ci95",
        "accuracy_positive_seeds",
        "accuracy_negative_seeds",
        "accuracy_tied_seeds",
        "accuracy_sign_p",
        "full_minus_variant_kappa_delta_mean",
        "full_minus_variant_kappa_delta_sd",
        "full_minus_variant_kappa_delta_ci95",
        "full_minus_variant_top2_delta_pp_mean",
        "full_minus_variant_top2_delta_pp_sd",
        "full_minus_variant_top2_delta_pp_ci95",
        "full_minus_variant_nonadjacent_error_delta_pp_mean",
        "full_minus_variant_nonadjacent_error_delta_pp_sd",
        "full_minus_variant_nonadjacent_error_delta_pp_ci95",
        "full_minus_variant_circular_distance_delta_mean",
        "full_minus_variant_circular_distance_delta_sd",
        "full_minus_variant_circular_distance_delta_ci95",
    ],
    "tables/deepconvnet_fixedsplit_mcnemar_public.csv": [
        "n_trials",
        "proposed_correct_deepconvnet_wrong",
        "proposed_wrong_deepconvnet_correct",
        "accuracy_delta",
        "mcnemar_exact_p",
    ],
    "tables/deepconvnet_loso_paired_runs_public.csv": [
        "heldout_session_index",
        "seed",
        "proposed_accuracy",
        "deepconvnet_accuracy",
        "accuracy_delta",
        "proposed_kappa",
        "deepconvnet_kappa",
        "kappa_delta",
        "proposed_top2",
        "deepconvnet_top2",
        "top2_delta",
    ],
    "tables/deepconvnet_paired_evidence_public.csv": [
        "positive_count",
        "negative_count",
        "tie_count",
        "accuracy_delta_pp",
        "exact_p",
    ],
    "tables/deepconvnet_session_stratified_5fold_paired_runs_public.csv": [
        "fold_index",
        "seed",
        "proposed_accuracy",
        "deepconvnet_accuracy",
        "accuracy_delta",
        "proposed_kappa",
        "deepconvnet_kappa",
        "kappa_delta",
        "proposed_top2",
        "deepconvnet_top2",
        "top2_delta",
    ],
    "tables/fixed_split_seed_runs_public.csv": [
        "seed",
        "split_seed",
        "val_seed",
        "train_samples",
        "validation_samples",
        "test_samples",
        "accuracy",
        "kappa",
        "top2",
    ],
    "tables/sub2_panel_public.csv": [
        "runs",
        "source_train_epochs",
        "source_validation_epochs",
        "target_train_epochs",
        "target_validation_epochs",
        "target_test_epochs",
        "accuracy_mean_percent",
        "accuracy_sd_percent",
        "kappa_mean",
        "kappa_sd",
        "top2_mean_percent",
        "top2_sd_percent",
    ],
    "tables/sub2_paired_deltas_public.csv": [
        "seed",
        "reference_accuracy",
        "comparator_accuracy",
        "reference_minus_comparator_accuracy_delta_pp",
    ],
    "tables/sub2_seed_runs_public.csv": [
        "seed",
        "split_seed",
        "val_seed",
        "source_train_samples",
        "source_validation_samples",
        "target_train_samples",
        "target_validation_samples",
        "target_test_samples",
        "accuracy",
        "kappa",
        "top2",
        "chance_accuracy",
        "accuracy_delta_vs_chance_pp",
    ],
    "tables/fixed_split_test_predictions_public.csv": [
        "sample_idx",
        "session_index",
        "epoch_idx",
        "label",
        "probability_mean_prediction",
        "hard_vote_prediction",
    ],
    "tables/robustness_public.csv": [
        "runs",
        "accuracy_mean_percent",
        "accuracy_sd_percent",
        "top2_mean_percent",
        "top2_sd_percent",
        "paired_delta_accuracy_vs_deepconvnet_pp",
        "exact_sign_p",
    ],
    "tables/subject_decodability_per_class_public.csv": [
        "sub1_proposed_accuracy_mean",
        "sub1_proposed_accuracy_sd",
        "sub1_equal_n_target_only_accuracy_mean",
        "sub1_equal_n_target_only_accuracy_sd",
        "sub2_target_only_accuracy_mean",
        "sub2_target_only_accuracy_sd",
        "sub2_minus_sub1_equal_n_accuracy_diff",
        "bootstrap_ci95_low",
        "bootstrap_ci95_high",
        "bootstrap_p_two_sided",
    ],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot average an empty list")
    return sum(values) / len(values)


def sample_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    value_mean = mean(values)
    variance = sum((value - value_mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def sign_counts(rows: list[dict[str, str]], field: str) -> tuple[int, int, int]:
    positives = negatives = ties = 0
    for row in rows:
        value = float(row[field])
        if value > 0:
            positives += 1
        elif value < 0:
            negatives += 1
        else:
            ties += 1
    return positives, negatives, ties


def check_manifest(root: Path, errors: list[str]) -> list[str]:
    manifest = root / "MANIFEST.md"
    if not manifest.exists():
        errors.append("MANIFEST.md is missing")
        return []
    text = manifest.read_text(encoding="utf-8")
    paths = re.findall(r"`([^`]+)`", text)
    checked = []
    for item in paths:
        if item in {"figures/"}:
            target = root / item
        else:
            target = root / item
        if not target.exists():
            errors.append(f"manifest item is missing: {item}")
        checked.append(item)
    return checked


def check_public_text_hygiene(root: Path, errors: list[str]) -> int:
    scanned = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(root).as_posix()
        scanned += 1
        for label, regex in PUBLIC_TEXT_PATTERNS:
            if regex.search(text):
                errors.append(f"public text hygiene pattern '{label}' found in {rel}")
    return scanned


def check_row_counts(root: Path, errors: list[str]) -> dict[str, int]:
    counts = {}
    for rel, expected in EXPECTED_COUNTS.items():
        rows = read_csv(root / rel)
        counts[rel] = len(rows)
        if len(rows) != expected:
            errors.append(f"{rel} has {len(rows)} rows; expected {expected}")
    return counts


def check_csv_schemas(root: Path, errors: list[str]) -> dict[str, object]:
    checked = {}
    for rel in sorted(set(EXPECTED_COUNTS) | set(EXPECTED_HEADERS)):
        path = root / rel
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            expected_headers = EXPECTED_HEADERS.get(rel)
            if expected_headers is not None and reader.fieldnames != expected_headers:
                errors.append(
                    f"{rel} header mismatch: got {reader.fieldnames}, expected {expected_headers}"
                )
            rows = list(reader)
        extra_field_rows = []
        numeric_errors = []
        for row_index, row in enumerate(rows, start=2):
            if row.get(None):
                extra_field_rows.append(row_index)
            for field in NUMERIC_FIELDS.get(rel, []):
                value = (row.get(field) or "").strip()
                if value == "":
                    continue
                try:
                    float(value)
                except ValueError:
                    numeric_errors.append(f"row {row_index} field {field}={value!r}")
        if extra_field_rows:
            errors.append(f"{rel} has extra comma-separated fields on rows {extra_field_rows}")
        if numeric_errors:
            errors.append(f"{rel} has non-numeric values in numeric columns: {numeric_errors}")
        checked[rel] = {
            "rows": len(rows),
            "columns": len(reader.fieldnames or []),
            "declared_header": expected_headers is not None,
        }
    return checked


def find_summary_row(rows: list[dict[str, str]], scope_token: str) -> dict[str, str]:
    for row in rows:
        if scope_token.lower() in row["scope"].lower():
            return row
    raise KeyError(f"no summary row contains scope token {scope_token!r}")


def find_row(rows: list[dict[str, str]], field: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(field) == value:
            return row
    raise KeyError(f"no row has {field}={value!r}")


def require_close(
    errors: list[str],
    label: str,
    observed: str | float,
    expected: float,
    tolerance: float = 1e-4,
) -> None:
    value = float(observed)
    if abs(value - expected) > tolerance:
        errors.append(f"{label} is {value}; expected {expected}")


def check_deepconvnet_pairs(root: Path, errors: list[str]) -> dict[str, object]:
    summary = read_csv(root / "tables/deepconvnet_paired_evidence_public.csv")
    fixed_mcnemar = read_csv(root / "tables/deepconvnet_fixedsplit_mcnemar_public.csv")
    fivefold = read_csv(root / "tables/deepconvnet_session_stratified_5fold_paired_runs_public.csv")
    loso = read_csv(root / "tables/deepconvnet_loso_paired_runs_public.csv")

    per_seed_rows = [row for row in fixed_mcnemar if row["scope"] == "per_seed"]
    pooled_rows = [row for row in fixed_mcnemar if row["scope"] == "pooled_seed_trial_pairs_summary"]
    if len(per_seed_rows) != 5:
        errors.append(f"fixed-split McNemar has {len(per_seed_rows)} per-seed rows; expected 5")
    if len(pooled_rows) != 1:
        errors.append(f"fixed-split McNemar has {len(pooled_rows)} pooled rows; expected 1")
    for row in per_seed_rows:
        delta = float(row["accuracy_delta"])
        wins = int(row["proposed_correct_deepconvnet_wrong"])
        losses = int(row["proposed_wrong_deepconvnet_correct"])
        if delta <= 0 or wins <= losses:
            errors.append(f"fixed-split McNemar seed {row['seed']} does not favor the proposed model")
    if pooled_rows:
        require_close(errors, "fixed-split McNemar pooled delta", pooled_rows[0]["accuracy_delta"], 0.077119)
        require_close(errors, "fixed-split McNemar pooled trials", pooled_rows[0]["n_trials"], 2360, tolerance=0)

    results = {
        "fixed_split_mcnemar": {
            "rows": len(fixed_mcnemar),
            "per_seed_rows": len(per_seed_rows),
            "pooled_accuracy_delta": float(pooled_rows[0]["accuracy_delta"]) if pooled_rows else None,
        }
    }
    for name, rows, token, block_field, expected_blocks, block_sign_p in [
        ("session_stratified_5fold", fivefold, "fivefold", "fold_index", 5, 0.0625),
        ("loso", loso, "leave-one-session-out", "heldout_session_index", 4, 0.125),
    ]:
        row = find_summary_row(summary, token)
        deltas = [float(item["accuracy_delta"]) for item in rows]
        mean_delta_pp = 100.0 * mean(deltas)
        positives, negatives, ties = sign_counts(rows, "accuracy_delta")
        block_deltas: dict[str, list[float]] = {}
        for item in rows:
            block_deltas.setdefault(item[block_field], []).append(float(item["accuracy_delta"]))
        block_mean_deltas_pp = {
            block: round(100.0 * mean(values), 4)
            for block, values in sorted(block_deltas.items(), key=lambda pair: int(pair[0]))
        }
        block_positive_count = sum(1 for value in block_mean_deltas_pp.values() if value > 0)
        expected_delta = float(row["accuracy_delta_pp"])
        expected_pos = int(row["positive_count"])
        expected_neg = int(row["negative_count"])
        expected_ties = int(row["tie_count"])
        if abs(mean_delta_pp - expected_delta) > 0.02:
            errors.append(
                f"{name} mean delta {mean_delta_pp:.4f} pp does not match "
                f"summary {expected_delta:.4f} pp"
            )
        if (positives, negatives, ties) != (expected_pos, expected_neg, expected_ties):
            errors.append(
                f"{name} sign counts {(positives, negatives, ties)} do not match "
                f"summary {(expected_pos, expected_neg, expected_ties)}"
            )
        if block_positive_count != expected_blocks:
            errors.append(
                f"{name} block-level positive count {block_positive_count} "
                f"does not match expected {expected_blocks}"
            )
        results[name] = {
            "rows": len(rows),
            "mean_accuracy_delta_pp": round(mean_delta_pp, 4),
            "positive_negative_tie": [positives, negatives, ties],
            "summary_accuracy_delta_pp": expected_delta,
            "block_mean_accuracy_delta_pp": block_mean_deltas_pp,
            "block_positive_count": block_positive_count,
            "block_sign_p": block_sign_p,
        }
    return results


def check_fixed_split_predictions(root: Path, errors: list[str]) -> dict[str, object]:
    manifest = read_csv(root / "metadata/fixed_split_sample_manifest_public.csv")
    predictions = read_csv(root / "tables/fixed_split_test_predictions_public.csv")
    feature_rows = read_csv(root / "tables/model_feature_attribution_summary_public.csv")
    feature = {row["metric"]: row["value"] for row in feature_rows}
    manifest_ids = {row["sample_idx"] for row in manifest}
    missing = [row["sample_idx"] for row in predictions if row["sample_idx"] not in manifest_ids]
    if missing:
        errors.append(f"{len(missing)} prediction rows are not present in the sample manifest")

    valid_labels = {str(i) for i in range(7)}
    invalid = []
    for row in predictions:
        fields = ["label", "probability_mean_prediction", "hard_vote_prediction"]
        for field in fields:
            if row[field] not in valid_labels:
                invalid.append((row["sample_idx"], field, row[field]))
    if invalid:
        errors.append(f"invalid class ids in fixed-split predictions: {invalid[:5]}")

    probability_mean_accuracy = mean(
        [
            1.0 if row["label"] == row["probability_mean_prediction"] else 0.0
            for row in predictions
        ]
    )
    hard_vote_accuracy = mean(
        [
            1.0 if row["label"] == row["hard_vote_prediction"] else 0.0
            for row in predictions
        ]
    )
    require_close(
        errors,
        "fixed-split probability-mean prediction accuracy",
        probability_mean_accuracy,
        float(feature["accuracy"]),
    )

    return {
        "manifest_rows": len(manifest),
        "prediction_rows": len(predictions),
        "prediction_rows_missing_from_manifest": len(missing),
        "probability_mean_accuracy": round(probability_mean_accuracy, 6),
        "hard_vote_accuracy": round(hard_vote_accuracy, 6),
    }


def check_fixed_split_assignments(root: Path, errors: list[str]) -> dict[str, object]:
    manifest = read_csv(root / "metadata/fixed_split_sample_manifest_public.csv")
    assignments = read_csv(root / "metadata/fixed_split_assignments_public.csv")
    predictions = read_csv(root / "tables/fixed_split_test_predictions_public.csv")

    manifest_by_id = {row["sample_idx"]: row for row in manifest}
    assignment_ids = [row["sample_idx"] for row in assignments]
    duplicate_ids = sorted({sample_id for sample_id in assignment_ids if assignment_ids.count(sample_id) > 1})
    if duplicate_ids:
        errors.append(f"fixed-split assignments contain duplicate sample ids: {duplicate_ids[:10]}")
    if set(assignment_ids) != set(manifest_by_id):
        errors.append("fixed-split assignments do not cover the same sample ids as the manifest")

    role_counts: dict[str, int] = {}
    test_ids = set()
    seed_pairs = set()
    for row in assignments:
        role = row["split_role"]
        role_counts[role] = role_counts.get(role, 0) + 1
        seed_pairs.add((row["split_seed"], row["val_seed"]))
        if role == "test":
            test_ids.add(row["sample_idx"])
        manifest_row = manifest_by_id.get(row["sample_idx"])
        if manifest_row:
            for field in ["session_index", "epoch_idx", "raw_label", "label", "label_name"]:
                if row[field] != manifest_row[field]:
                    errors.append(
                        f"fixed-split assignment metadata mismatch for sample "
                        f"{row['sample_idx']} field {field}"
                    )
                    break

    expected_roles = {"train": 1508, "validation": 379, "test": 472}
    if role_counts != expected_roles:
        errors.append(f"fixed-split role counts {role_counts} do not match {expected_roles}")
    if seed_pairs != {("42", "2026")}:
        errors.append(f"fixed-split assignments contain unexpected split/validation seeds: {seed_pairs}")

    prediction_ids = {row["sample_idx"] for row in predictions}
    if prediction_ids != test_ids:
        errors.append("fixed-split prediction sample ids do not match assignment test ids")

    return {
        "assignment_rows": len(assignments),
        "role_counts": role_counts,
        "split_val_seed_pairs": sorted([list(pair) for pair in seed_pairs]),
        "test_predictions_match_assignments": prediction_ids == test_ids,
    }


def check_fixed_split_seed_runs(root: Path, errors: list[str]) -> dict[str, object]:
    main = read_csv(root / "tables/main_results_public.csv")
    seed_rows = read_csv(root / "tables/fixed_split_seed_runs_public.csv")
    by_method: dict[str, list[dict[str, str]]] = {}
    for row in seed_rows:
        by_method.setdefault(row["method"], []).append(row)

    checked: dict[str, dict[str, float]] = {}
    for row in main:
        method = row["method"]
        if method not in by_method:
            continue
        rows = by_method[method]
        expected_runs = int(row["runs"])
        if len(rows) != expected_runs:
            errors.append(f"{method} has {len(rows)} seed rows; expected {expected_runs}")
            continue
        checked[method] = {}
        for metric in ["accuracy", "kappa", "top2"]:
            values = [float(item[metric]) for item in rows]
            observed_mean = mean(values)
            observed_sd = sample_stdev(values)
            require_close(
                errors,
                f"fixed-split seed {method} {metric} mean",
                observed_mean,
                float(row[f"{metric}_mean"]),
            )
            require_close(
                errors,
                f"fixed-split seed {method} {metric} sd",
                observed_sd,
                float(row[f"{metric}_sd"]),
            )
            checked[method][f"{metric}_mean"] = round(observed_mean, 6)
            checked[method][f"{metric}_sd"] = round(observed_sd, 6)

    if len(checked) != 10:
        errors.append(f"fixed-split seed recomputation covered {len(checked)} methods; expected 10")

    return {
        "seed_rows": len(seed_rows),
        "methods_checked": len(checked),
        "recomputed": checked,
    }


def check_channel_scope(root: Path, errors: list[str]) -> dict[str, object]:
    summary = read_csv(root / "tables/channel_scope_summary_public.csv")
    paired = read_csv(root / "tables/channel_scope_paired_public.csv")

    posterior = find_row(summary, "channel_scope", "posterior6")
    all16 = find_row(summary, "channel_scope", "all16")
    require_close(errors, "channel-scope posterior6 accuracy", posterior["test_acc_mean"], 0.530508)
    require_close(errors, "channel-scope posterior6 accuracy sd", posterior["test_acc_sd"], 0.008151)
    require_close(errors, "channel-scope all16 accuracy", all16["test_acc_mean"], 0.516949)
    require_close(errors, "channel-scope all16 accuracy sd", all16["test_acc_sd"], 0.027297)
    require_close(errors, "channel-scope all16 kappa", all16["test_kappa_mean"], 0.436451)
    require_close(errors, "channel-scope all16 top2", all16["test_top2_mean"], 0.731356)
    require_close(
        errors,
        "channel-scope all16 paired accuracy delta",
        all16["paired_delta_vs_posterior6_test_acc_mean"],
        -0.013559,
    )

    acc_deltas = []
    for row in paired:
        expected_delta = float(row["all16_test_acc"]) - float(row["posterior6_test_acc"])
        observed_delta = float(row["delta_all16_minus_posterior6_test_acc"])
        if abs(expected_delta - observed_delta) > 1e-6:
            errors.append(f"channel-scope paired accuracy delta mismatch for seed {row['seed']}")
        acc_deltas.append(observed_delta)
    positives = sum(1 for value in acc_deltas if value > 0)
    negatives = sum(1 for value in acc_deltas if value < 0)
    ties = sum(1 for value in acc_deltas if value == 0)

    return {
        "summary_rows": len(summary),
        "paired_rows": len(paired),
        "all16_accuracy_mean": round(float(all16["test_acc_mean"]), 6),
        "paired_accuracy_delta_mean": round(mean(acc_deltas), 6),
        "positive_negative_tie": [positives, negatives, ties],
    }


def check_sub2_seed_runs(root: Path, errors: list[str]) -> dict[str, object]:
    panel = read_csv(root / "tables/sub2_panel_public.csv")
    seed_rows = read_csv(root / "tables/sub2_seed_runs_public.csv")
    deltas = read_csv(root / "tables/sub2_paired_deltas_public.csv")

    by_method: dict[str, list[dict[str, str]]] = {}
    by_method_seed: dict[tuple[str, str], dict[str, str]] = {}
    for row in seed_rows:
        by_method.setdefault(row["method"], []).append(row)
        by_method_seed[(row["method"], row["seed"])] = row
        expected_delta = (float(row["accuracy"]) - float(row["chance_accuracy"])) * 100.0
        require_close(
            errors,
            f"Sub2 chance delta {row['method']} seed {row['seed']}",
            row["accuracy_delta_vs_chance_pp"],
            expected_delta,
        )

    panel_checked: dict[str, dict[str, float]] = {}
    for row in panel:
        method = row["method"]
        if method not in by_method:
            errors.append(f"Sub2 panel method lacks seed rows: {method}")
            continue
        rows = by_method[method]
        expected_runs = int(row["runs"])
        if len(rows) != expected_runs:
            errors.append(f"{method} has {len(rows)} Sub2 seed rows; expected {expected_runs}")
            continue
        accuracies = [float(item["accuracy"]) for item in rows]
        kappas = [float(item["kappa"]) for item in rows]
        top2s = [float(item["top2"]) for item in rows]
        acc_mean_percent = 100.0 * mean(accuracies)
        acc_sd_percent = 100.0 * sample_stdev(accuracies)
        kappa_mean = mean(kappas)
        kappa_sd = sample_stdev(kappas)
        top2_mean_percent = 100.0 * mean(top2s)
        top2_sd_percent = 100.0 * sample_stdev(top2s)
        require_close(errors, f"Sub2 seed {method} accuracy mean percent", acc_mean_percent, float(row["accuracy_mean_percent"]), tolerance=0.01)
        require_close(errors, f"Sub2 seed {method} accuracy sd percent", acc_sd_percent, float(row["accuracy_sd_percent"]), tolerance=0.01)
        require_close(errors, f"Sub2 seed {method} kappa mean", kappa_mean, float(row["kappa_mean"]))
        require_close(errors, f"Sub2 seed {method} kappa sd", kappa_sd, float(row["kappa_sd"]))
        require_close(errors, f"Sub2 seed {method} top2 mean percent", top2_mean_percent, float(row["top2_mean_percent"]), tolerance=0.01)
        require_close(errors, f"Sub2 seed {method} top2 sd percent", top2_sd_percent, float(row["top2_sd_percent"]), tolerance=0.01)
        count_pairs = [
            ("source_train_epochs", "source_train_samples"),
            ("source_validation_epochs", "source_validation_samples"),
            ("target_train_epochs", "target_train_samples"),
            ("target_validation_epochs", "target_validation_samples"),
            ("target_test_epochs", "target_test_samples"),
        ]
        for panel_field, seed_field in count_pairs:
            expected_count = (row.get(panel_field) or "").strip()
            for seed_row in rows:
                observed_count = (seed_row.get(seed_field) or "").strip()
                if observed_count != expected_count:
                    errors.append(
                        f"Sub2 sample-count mismatch for {method} seed {seed_row['seed']} "
                        f"{seed_field}={observed_count!r}; expected {expected_count!r}"
                    )
        panel_checked[method] = {
            "accuracy_mean_percent": round(acc_mean_percent, 4),
            "accuracy_sd_percent": round(acc_sd_percent, 4),
            "kappa_mean": round(kappa_mean, 6),
            "kappa_sd": round(kappa_sd, 6),
            "top2_mean_percent": round(top2_mean_percent, 4),
            "top2_sd_percent": round(top2_sd_percent, 4),
        }

    delta_summary: dict[str, dict[str, object]] = {}
    for row in deltas:
        ref_key = (row["reference_method"], row["seed"])
        comp_key = (row["comparator_method"], row["seed"])
        if ref_key not in by_method_seed or comp_key not in by_method_seed:
            errors.append(f"Sub2 paired delta references missing seed rows: {ref_key}, {comp_key}")
            continue
        ref_acc = float(by_method_seed[ref_key]["accuracy"])
        comp_acc = float(by_method_seed[comp_key]["accuracy"])
        expected_delta = 100.0 * (ref_acc - comp_acc)
        require_close(
            errors,
            f"Sub2 paired delta {row['comparator_method']} seed {row['seed']}",
            row["reference_minus_comparator_accuracy_delta_pp"],
            expected_delta,
        )
        expected_direction = (
            "target_only_higher"
            if expected_delta > 0
            else "target_only_lower"
            if expected_delta < 0
            else "tie"
        )
        if row["direction"] != expected_direction:
            errors.append(
                f"Sub2 paired direction for {row['comparator_method']} seed {row['seed']} "
                f"is {row['direction']}; expected {expected_direction}"
            )
        delta_summary.setdefault(row["comparator_method"], {"deltas": []})["deltas"].append(expected_delta)

    summarized_deltas = {}
    for comparator, summary in delta_summary.items():
        values = summary["deltas"]
        positives = sum(1 for value in values if value > 0)
        negatives = sum(1 for value in values if value < 0)
        ties = sum(1 for value in values if value == 0)
        summarized_deltas[comparator] = {
            "mean_delta_pp": round(mean(values), 4),
            "positive_negative_tie": [positives, negatives, ties],
        }

    return {
        "seed_rows": len(seed_rows),
        "paired_delta_rows": len(deltas),
        "panel_methods_checked": len(panel_checked),
        "recomputed_panel": panel_checked,
        "paired_delta_summary": summarized_deltas,
    }


def check_public_values(root: Path, errors: list[str]) -> dict[str, object]:
    main = read_csv(root / "tables/main_results_public.csv")
    proposed = find_row(main, "method", "Proposed model")
    deep = find_row(main, "method", "DeepConvNet-CE")
    deep_stabilized = find_row(main, "method", "DeepConvNet-CE + stabilization")
    require_close(errors, "main proposed accuracy", proposed["accuracy_mean"], 0.5305)
    require_close(errors, "main proposed kappa", proposed["kappa_mean"], 0.4523)
    require_close(errors, "main proposed top2", proposed["top2_mean"], 0.7331)
    require_close(errors, "main DeepConvNet accuracy", deep["accuracy_mean"], 0.4534)
    require_close(errors, "main stabilized DeepConvNet accuracy", deep_stabilized["accuracy_mean"], 0.4661)
    require_close(errors, "main stabilized DeepConvNet kappa", deep_stabilized["kappa_mean"], 0.3772)

    robustness = read_csv(root / "tables/robustness_public.csv")
    fivefold_prop = [
        row
        for row in robustness
        if row["protocol"].startswith("Session-stratified")
        and row["method"] == "Proposed model"
    ][0]
    loso_prop = [
        row
        for row in robustness
        if row["protocol"] == "Leave-one-session-out"
        and row["method"] == "Proposed model"
    ][0]
    require_close(errors, "fivefold proposed accuracy percent", fivefold_prop["accuracy_mean_percent"], 51.93)
    require_close(errors, "fivefold proposed top2 percent", fivefold_prop["top2_mean_percent"], 75.19)
    require_close(errors, "LOSO proposed accuracy percent", loso_prop["accuracy_mean_percent"], 48.15)
    require_close(errors, "LOSO proposed top2 percent", loso_prop["top2_mean_percent"], 71.37)

    sub2 = read_csv(root / "tables/sub2_panel_public.csv")
    sub2_target = find_row(sub2, "method", "Sub2 target-only")
    sub2_source = find_row(sub2, "method", "Sub1 source-only")
    require_close(errors, "Sub2 target-only accuracy percent", sub2_target["accuracy_mean_percent"], 32.29)
    require_close(errors, "Sub1 source-only to Sub2 accuracy percent", sub2_source["accuracy_mean_percent"], 17.14)

    class_rows = read_csv(root / "tables/subject_decodability_per_class_public.csv")
    red = find_row(class_rows, "class_name", "red")
    yellow = find_row(class_rows, "class_name", "yellow")
    blue = find_row(class_rows, "class_name", "blue")
    require_close(errors, "Sub1 proposed red class accuracy", red["sub1_proposed_accuracy_mean"], 0.7791)
    require_close(errors, "Sub2 target-only red class accuracy", red["sub2_target_only_accuracy_mean"], 0.6200)
    require_close(errors, "Sub1 equal-N yellow class accuracy", yellow["sub1_equal_n_target_only_accuracy_mean"], 0.5000)
    require_close(errors, "Sub2 target-only yellow class accuracy", yellow["sub2_target_only_accuracy_mean"], 0.1400)
    require_close(errors, "Sub2 target-only blue class accuracy", blue["sub2_target_only_accuracy_mean"], 0.4400)

    ablation = read_csv(root / "tables/ablation_public.csv")
    full = find_row(ablation, "variant", "Full proposed model")
    no_ema = find_row(ablation, "variant", "w/o EMA/checkpoint averaging")
    require_close(errors, "ablation full accuracy", full["accuracy_mean"], 0.5305)
    require_close(errors, "ablation no-EMA accuracy", no_ema["accuracy_mean"], 0.5089)

    component = read_csv(root / "tables/component_paired_evidence_public.csv")
    comp_hsv = find_row(component, "variant", "w/o HSV prototype logits")
    comp_adjacent = find_row(component, "variant", "w/o gated adjacent class query")
    comp_ordered = find_row(component, "variant", "w/o ordered-label terms")
    comp_contrastive = find_row(component, "variant", "w/o color-contrastive loss")
    comp_ema = find_row(component, "variant", "w/o EMA/checkpoint averaging")
    comp_car = find_row(component, "variant", "no CAR front-end")
    require_close(
        errors,
        "component HSV accuracy delta pp",
        comp_hsv["full_minus_variant_accuracy_delta_pp_mean"],
        0.7627,
    )
    require_close(
        errors,
        "component adjacent-query accuracy delta pp",
        comp_adjacent["full_minus_variant_accuracy_delta_pp_mean"],
        0.9746,
    )
    require_close(
        errors,
        "component ordered-label accuracy delta pp",
        comp_ordered["full_minus_variant_accuracy_delta_pp_mean"],
        0.8475,
    )
    require_close(
        errors,
        "component ordered-label circular-distance delta",
        comp_ordered["full_minus_variant_circular_distance_delta_mean"],
        -0.0288,
    )
    require_close(
        errors,
        "component contrastive accuracy delta pp",
        comp_contrastive["full_minus_variant_accuracy_delta_pp_mean"],
        0.0,
    )
    require_close(
        errors,
        "component EMA accuracy delta pp",
        comp_ema["full_minus_variant_accuracy_delta_pp_mean"],
        2.1610,
    )
    require_close(
        errors,
        "component CAR accuracy delta pp",
        comp_car["full_minus_variant_accuracy_delta_pp_mean"],
        0.8051,
    )
    require_close(
        errors,
        "component EMA non-adjacent error delta pp",
        comp_ema["full_minus_variant_nonadjacent_error_delta_pp_mean"],
        -1.4407,
    )
    if any(row["matched_test_labels_and_indices"] != "yes" for row in component):
        errors.append("component paired evidence contains unmatched rows")

    color = read_csv(root / "tables/color_neighborhood_error_public.csv")
    color_prop = find_row(color, "method", "CoG-SAGE")
    color_no_order = find_row(color, "method", "w/o ordered-label terms")
    color_deep_stab = find_row(color, "method", "DeepConvNet-CE + stabilization")
    require_close(errors, "color non-adjacent error", color_prop["observed_nonadjacent_error_mean"], 0.2758)
    require_close(errors, "color circular distance", color_prop["observed_mean_circular_distance"], 0.8924)
    require_close(errors, "w/o ordered-label circular distance", color_no_order["observed_mean_circular_distance"], 0.9212)
    require_close(errors, "stabilized DeepConvNet circular distance", color_deep_stab["observed_mean_circular_distance"], 1.0301)

    controls = read_csv(root / "tables/additional_controls_public.csv")
    prior = find_row(controls, "control_family", "Train class prior scores")
    erp = find_row(controls, "control_family", "Post-onset ERP/bandpower linear SVM")
    require_close(errors, "train-prior test accuracy percent", prior["test_accuracy_percent"], 14.19)
    require_close(errors, "ERP/bandpower test accuracy percent", erp["test_accuracy_percent"], 25.21)

    feature_rows = read_csv(root / "tables/model_feature_attribution_summary_public.csv")
    feature = {row["metric"]: row["value"] for row in feature_rows}
    require_close(errors, "Fig. 3 seed-aligned accuracy", feature["accuracy"], 0.5614406779661016)
    require_close(errors, "Fig. 3 sample count", feature["n_samples"], 472, tolerance=0)
    if feature.get("combine_mode") != "seed_aligned_mean":
        errors.append("Fig. 3 combine mode is not seed_aligned_mean")
    require_close(errors, "Fig. 3 correct mean margin", feature["correct_mean_margin"], 0.20681822299957275)
    require_close(errors, "Fig. 3 error mean margin", feature["error_mean_margin"], 0.13245882093906403)
    require_close(errors, "Fig. 3 adjacent error rate", feature["adjacent_error_rate"], 0.17584745762711865)
    require_close(errors, "Fig. 3 non-adjacent error rate", feature["nonadjacent_error_rate"], 0.2627118644067797)
    require_close(errors, "Fig. 3 mean circular distance", feature["mean_circular_distance"], 0.8411016949152542)

    config = {row["parameter"]: row["value"] for row in read_csv(root / "metadata/model_configuration_public.csv")}
    require_close(errors, "config color contrastive weight", config["color_contrastive_weight"], 0.02)
    require_close(errors, "config HSV prototype scale", config["hsv_prototype_logit_scale"], 0.005)
    require_close(errors, "config class-query scale", config["class_query_logit_scale"], 0.01)
    require_close(errors, "config class-query gate bias", config["class_query_gate_bias"], -2.5)
    require_close(errors, "config EMA decay", config["ema_decay"], 0.99)
    require_close(errors, "config checkpoint average top-k", config["checkpoint_average_top_k"], 5, tolerance=0)
    require_close(errors, "config learning rate", config["learning_rate"], 0.0003)
    require_close(errors, "config weight decay", config["weight_decay"], 0.001)
    require_close(errors, "config batch size", config["batch_size"], 32, tolerance=0)
    require_close(errors, "config max epochs", config["max_epochs"], 150, tolerance=0)
    require_close(errors, "config early-stopping patience", config["early_stopping_patience"], 25, tolerance=0)
    require_close(errors, "config auxiliary feature dimension", config["aux_feature_dim"], 42, tolerance=0)

    stimuli = read_csv(root / "metadata/stimulus_attributes_public.csv")
    red_stim = find_row(stimuli, "color", "red")
    yellow_stim = find_row(stimuli, "color", "yellow")
    purple_stim = find_row(stimuli, "color", "purple")
    require_close(errors, "stimulus red trigger", red_stim["trigger_id"], 3, tolerance=0)
    require_close(errors, "stimulus yellow hue", yellow_stim["hsv_h_deg"], 60, tolerance=0)
    require_close(errors, "stimulus yellow relative luminance", yellow_stim["relative_luminance_srgb"], 0.9278)
    require_close(errors, "stimulus purple relative luminance", purple_stim["relative_luminance_srgb"], 0.0615)

    return {
        "main_values_checked": 6,
        "robustness_values_checked": 4,
        "sub2_values_checked": 2,
        "class_decodability_values_checked": 5,
        "ablation_values_checked": 2,
        "component_values_checked": 9,
        "color_values_checked": 2,
        "control_values_checked": 2,
        "feature_values_checked": 8,
        "configuration_values_checked": 12,
        "stimulus_values_checked": 4,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="artifact root directory",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not (root / "tables").exists() and (root / "public_artifact" / "tables").exists():
        root = root / "public_artifact"
    errors: list[str] = []
    report = {
        "artifact_root": root.name,
        "manifest_items_checked": check_manifest(root, errors),
        "text_files_scanned": check_public_text_hygiene(root, errors),
        "row_counts": check_row_counts(root, errors),
        "schema_checks": check_csv_schemas(root, errors),
        "fixed_split_seed_runs": check_fixed_split_seed_runs(root, errors),
        "channel_scope": check_channel_scope(root, errors),
        "sub2_seed_runs": check_sub2_seed_runs(root, errors),
        "public_values": check_public_values(root, errors),
        "deepconvnet_pairs": check_deepconvnet_pairs(root, errors),
        "fixed_split_predictions": check_fixed_split_predictions(root, errors),
        "fixed_split_assignments": check_fixed_split_assignments(root, errors),
    }

    if errors:
        report["status"] = "FAIL"
        report["errors"] = errors
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    report["status"] = "PASS"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
