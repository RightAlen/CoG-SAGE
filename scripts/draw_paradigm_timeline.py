"""Draw a compact paradigm timeline for the paper.

The figure keeps only structural labels needed to read the paradigm. Details
such as epoch counts, split sizes, preprocessing prose, and control-stimulus
notes belong in the caption or Methods text, not inside the figure.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["svg.fonttype"] = "none"

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = ROOT / "generated_figures"

INK = "#202124"
MUTED = "#6b7280"
BG = "#f7f7f4"
REST = "#d8d3c6"
JITTER = "#b8d8d8"
STIM = "#efb1ad"
BLUE = "#415a77"

TARGET_COLORS = ["#e64b3c", "#f28e2b", "#f4d44d", "#59a14f", "#4ecccc", "#4e79a7", "#9c6ade"]


def rounded_box(ax, x: float, y: float, w: float, h: float, label: str, fill: str):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.03,rounding_size=0.12",
        linewidth=1.6,
        edgecolor=INK,
        facecolor=fill,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=11, color=INK, fontweight="bold")


def marker(ax, x: float, code: str):
    ax.plot([x, x], [1.74, 2.08], color=INK, linewidth=1.2)
    ax.add_patch(Circle((x, 2.35), 0.22, facecolor="#ffffff", edgecolor=INK, linewidth=1.3))
    ax.text(x, 2.35, code, ha="center", va="center", fontsize=9.5, color=INK, fontweight="bold")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11.2, 3.2))
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.plot([0.78, 10.45], [1.44, 1.44], color=INK, linewidth=2.0, solid_capstyle="round")
    ax.add_patch(Polygon([[10.45, 1.44], [10.25, 1.34], [10.25, 1.54]], closed=True, facecolor=INK, edgecolor=INK))

    rounded_box(ax, 0.85, 1.48, 1.65, 0.58, "Rest", REST)
    rounded_box(ax, 3.0, 1.48, 1.9, 0.58, "Jitter\n2.0-2.4 s", JITTER)
    rounded_box(ax, 5.45, 1.48, 2.7, 0.58, "Color patch\n3.0 s", STIM)

    for x, code in [(0.85, "253"), (2.5, "254"), (5.45, "3-9"), (8.15, "240")]:
        marker(ax, x, code)

    ax.text(0.85, 0.78, "Targets", ha="left", va="center", fontsize=10.5, color=INK, fontweight="bold")
    swatch_x = 1.72
    for idx, color in enumerate(TARGET_COLORS):
        ax.add_patch(
            Rectangle(
                (swatch_x + idx * 0.4, 0.59),
                0.32,
                0.32,
                facecolor=color,
                edgecolor=INK,
                linewidth=0.8,
            )
        )

    ax.plot([5.45, 8.15], [0.98, 0.98], color=BLUE, linewidth=1.8, linestyle=(0, (5, 4)))
    ax.plot([5.45, 5.45], [0.9, 1.06], color=BLUE, linewidth=1.8)
    ax.plot([8.15, 8.15], [0.9, 1.06], color=BLUE, linewidth=1.8)
    ax.text(6.8, 0.78, "stimulus interval", ha="center", va="center", fontsize=9.2, color=MUTED)

    for ext in ("svg", "pdf", "png"):
        fig.savefig(FIGURE_DIR / f"figure1_paradigm_timeline.{ext}", format=ext, bbox_inches="tight", facecolor=BG, dpi=240)
    plt.close(fig)


if __name__ == "__main__":
    main()
