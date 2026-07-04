"""Draw the paper overview framework figure.

The figure is intentionally count-free: it describes the experimental and
model story without dataset-size or train/validation/test split numbers.
"""

from __future__ import annotations

import math
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["svg.fonttype"] = "none"

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = ROOT / "generated_figures"

INK = "#202124"
MUTED = "#5f6368"
BG = "#f7f7f4"
PANEL_EDGE = "#202124"
BLUE = "#b8d8d8"
GREEN = "#cfe8d4"
PURPLE = "#d8c7e8"
ORANGE = "#f3cf9d"
PINK = "#f0b7b3"
GRAY = "#e6e2d8"

COLOR_RING = [
    ("red", "#e64b3c"),
    ("orange", "#f28e2b"),
    ("yellow", "#f4d44d"),
    ("green", "#59a14f"),
    ("cyan", "#4ecccc"),
    ("blue", "#4e79a7"),
    ("purple", "#9c6ade"),
]


def rounded_box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    *,
    fill: str = "#ffffff",
    edge: str = PANEL_EDGE,
    fontsize: float = 9.4,
    weight: str = "normal",
    radius: float = 0.12,
    text_color: str = INK,
    linewidth: float = 1.3,
):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.025,rounding_size={radius}",
        linewidth=linewidth,
        edgecolor=edge,
        facecolor=fill,
    )
    ax.add_patch(patch)
    wrapped = "\n".join(textwrap.wrap(label, width=max(14, int(w * 10.5))))
    ax.text(
        x + w / 2,
        y + h / 2,
        wrapped,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=text_color,
        fontweight=weight,
        linespacing=1.12,
    )
    return patch


def stage_panel(ax, x: float, y: float, w: float, h: float, title: str, fill: str):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.04,rounding_size=0.16",
        linewidth=1.5,
        edgecolor=PANEL_EDGE,
        facecolor="#ffffff",
    )
    ax.add_patch(patch)
    ax.add_patch(
        FancyBboxPatch(
            (x + 0.12, y + h - 0.72),
            w - 0.24,
            0.52,
            boxstyle="round,pad=0.02,rounding_size=0.11",
            linewidth=0,
            facecolor=fill,
        )
    )
    ax.text(x + 0.26, y + h - 0.37, title, ha="left", va="center", fontsize=12, fontweight="bold", color=INK)
    return patch


def arrow(ax, xy1, xy2, *, color=INK, linewidth=1.8, mutation_scale=14, rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            xy1,
            xy2,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            linewidth=linewidth,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=3,
            shrinkB=3,
        )
    )


def draw_color_patch_stack(ax, x: float, y: float):
    size = 0.27
    gap = 0.035
    for idx, (_, color) in enumerate(COLOR_RING):
        ax.add_patch(Rectangle((x + idx * (size + gap), y), size, size, facecolor=color, edgecolor=INK, linewidth=0.55))


def draw_eeg_wave(ax, x: float, y: float, w: float, h: float):
    xs = [x + i * w / 120 for i in range(121)]
    for ch in range(5):
        base = y + h * (0.16 + ch * 0.17)
        ys = [
            base
            + 0.045 * math.sin(2 * math.pi * (i / 22 + ch * 0.2))
            + 0.025 * math.sin(2 * math.pi * (i / 9 + ch * 0.3))
            for i in range(121)
        ]
        ax.plot(xs, ys, color="#415a77", linewidth=0.9)
    rounded_box(ax, x - 0.02, y - 0.06, w + 0.04, h + 0.12, "", fill="none", linewidth=1.0, radius=0.08)


def draw_color_ring(ax, cx: float, cy: float, r: float):
    node_radius = max(0.1, r * 0.24)
    ax.add_patch(Circle((cx, cy), r, fill=False, edgecolor="#415a77", linewidth=1.2, linestyle=(0, (4, 3))))
    for idx, (_, color) in enumerate(COLOR_RING):
        angle = math.pi / 2 - idx * 2 * math.pi / len(COLOR_RING)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        ax.add_patch(Circle((px, py), node_radius, facecolor=color, edgecolor=INK, linewidth=0.8))
    ax.text(cx, cy, "color\nring", ha="center", va="center", fontsize=8.0, color=INK, fontweight="bold")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(13.8, 5.7))
    ax.set_xlim(0, 13.8)
    ax.set_ylim(0, 5.7)
    ax.axis("off")
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    panels = [
        (0.45, 0.36, 2.75, 4.95, "1. Paradigm", BLUE),
        (3.55, 0.36, 2.75, 4.95, "2. EEG Epochs", GREEN),
        (6.65, 0.36, 3.1, 4.95, "3. Representation", ORANGE),
        (10.1, 0.36, 3.25, 4.95, "4. Color Geometry", PURPLE),
    ]
    for panel in panels:
        stage_panel(ax, *panel)

    # Panel 1: paradigm.
    rounded_box(ax, 0.78, 3.86, 2.08, 0.62, "jittered fixation", fill=GRAY, fontsize=8.8, weight="bold")
    rounded_box(ax, 0.78, 2.92, 2.08, 0.72, "full-field color patch", fill=PINK, fontsize=8.8, weight="bold")
    rounded_box(ax, 0.78, 1.94, 2.08, 0.66, "flip-synchronized trigger", fill="#ffffff", fontsize=8.3)
    draw_color_patch_stack(ax, 0.86, 1.3)
    arrow(ax, (1.82, 3.84), (1.82, 3.67), color="#6b7280", mutation_scale=11)
    arrow(ax, (1.82, 2.9), (1.82, 2.62), color="#6b7280", mutation_scale=11)

    # Panel 2: signal construction.
    draw_eeg_wave(ax, 3.9, 3.42, 2.04, 0.82)
    rounded_box(ax, 3.95, 2.5, 1.94, 0.6, "epoch around color onset", fill="#ffffff", fontsize=8.3)
    rounded_box(ax, 3.95, 1.75, 1.94, 0.6, "baseline correction + filtering", fill="#ffffff", fontsize=8.3)
    rounded_box(ax, 3.95, 0.99, 1.94, 0.6, "short post-onset decoding window", fill="#ffffff", fontsize=8.3)
    arrow(ax, (4.92, 3.36), (4.92, 3.12), color="#6b7280", mutation_scale=11)
    arrow(ax, (4.92, 2.48), (4.92, 2.37), color="#6b7280", mutation_scale=11)
    arrow(ax, (4.92, 1.73), (4.92, 1.61), color="#6b7280", mutation_scale=11)

    # Panel 3: representation and fusion.
    rounded_box(ax, 6.95, 3.75, 2.48, 0.6, "raw EEG temporal backbone", fill="#ffffff", fontsize=8.4)
    rounded_box(ax, 6.95, 2.91, 2.48, 0.6, "covariance / Riemannian auxiliary features", fill="#ffffff", fontsize=8.0)
    rounded_box(ax, 6.95, 2.07, 2.48, 0.6, "session-aware SRM alignment", fill="#ffffff", fontsize=8.2)
    rounded_box(ax, 7.35, 1.1, 1.68, 0.64, "fusion logits", fill=ORANGE, fontsize=8.8, weight="bold")
    arrow(ax, (8.19, 3.73), (8.19, 1.78), color="#6b7280", mutation_scale=12)
    arrow(ax, (8.19, 2.89), (8.19, 1.78), color="#6b7280", mutation_scale=12)
    arrow(ax, (8.19, 2.05), (8.19, 1.78), color="#6b7280", mutation_scale=12)

    # Panel 4: color geometry and outputs.
    draw_color_ring(ax, 11.2, 3.9, 0.48)
    rounded_box(ax, 10.78, 2.6, 2.36, 0.55, "HSV prototype logits", fill="#ffffff", fontsize=8.2)
    rounded_box(ax, 10.78, 1.94, 2.36, 0.55, "prototype logit regularization", fill="#ffffff", fontsize=8.2)
    rounded_box(ax, 10.78, 1.28, 2.36, 0.55, "adjacent class-query residuals", fill="#ffffff", fontsize=8.0)
    rounded_box(ax, 10.78, 0.88, 2.36, 0.28, "prediction + error analysis", fill=PURPLE, fontsize=7.2, weight="bold")
    arrow(ax, (11.2, 3.38), (11.2, 3.18), color="#6b7280", mutation_scale=11)
    arrow(ax, (11.96, 2.59), (11.96, 2.5), color="#6b7280", mutation_scale=11)
    arrow(ax, (11.96, 1.93), (11.96, 1.84), color="#6b7280", mutation_scale=11)
    arrow(ax, (11.96, 1.27), (11.96, 1.18), color="#6b7280", mutation_scale=11)

    # Inter-stage arrows.
    arrow(ax, (3.2, 3.18), (3.55, 3.18), linewidth=2.2, mutation_scale=17)
    arrow(ax, (6.3, 3.18), (6.65, 3.18), linewidth=2.2, mutation_scale=17)
    arrow(ax, (9.75, 3.18), (10.1, 3.18), linewidth=2.2, mutation_scale=17)

    for ext in ("svg", "pdf", "png"):
        fig.savefig(FIGURE_DIR / f"figure2_overall_framework.{ext}", format=ext, bbox_inches="tight", facecolor=BG, dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()
