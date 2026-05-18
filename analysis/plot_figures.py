"""
paper-ready figures for the experiment json outputs.

  fig_detection_bars : weak vs complete observable deviations
  fig_sample_curve   : detection rate vs shot budget
  fig_drift_panel    : pairwise drift across timepoints

visual style aims for a calm three-tone palette
(deep teal, bordeaux, olive) with light grid and
no heavy borders.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl


# --- visual constants ---

TEAL   = "#1f5f6b"   # primary
BORDX  = "#9a3a3a"   # accent for thresholds / sneaky
OLIVE  = "#8a8a3a"   # secondary
SLATE  = "#3a3a44"   # text
MIST   = "#d8d8d2"   # grid

DPI = 220


def apply_style():
    """house style for all figures."""
    mpl.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10.5,
        "axes.titlesize": 11.5,
        "axes.titleweight": "normal",
        "axes.labelsize": 10.5,
        "axes.edgecolor": SLATE,
        "axes.linewidth": 0.8,
        "axes.labelcolor": SLATE,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "grid.color": MIST,
        "grid.linestyle": (0, (2, 2)),
        "grid.linewidth": 0.6,
        "legend.frameon": False,
        "legend.fontsize": 9.5,
    })


def load(p):
    with open(p) as f:
        return json.load(f)


def fig_detection_bars(d, out_path):
    """per-observable honest vs sneaky deviation, weak-family
    entries in olive, complete-family entries in teal, tolerance
    line in bordeaux."""
    weak_set = set(d.get("weak_family", []))
    family = d["complete_family"]
    if weak_set and not (weak_set <= set(family)):
        family = list(weak_set) + family

    fp_h = d["fingerprint_honest"]
    fp_s = d["fingerprint_sneaky"]
    devs = [abs(fp_h[p] - fp_s[p]) for p in family]
    colors = [OLIVE if p in weak_set else TEAL for p in family]
    eps = d["eps"]

    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    ax.set_axisbelow(True)
    ax.yaxis.grid(True)

    bars = ax.bar(family, devs, color=colors, width=0.62)
    ax.axhline(eps, color=BORDX, linestyle="-", linewidth=1.4,
               label=fr"tolerance $\varepsilon = {eps}$")

    ax.set_ylabel(
        r"$|\langle P \rangle_{\mathrm{honest}}"
        r" - \langle P \rangle_{\mathrm{sneaky}}|$"
    )
    ax.set_title("Per-observable deviation: honest vs sneaky channel")

    ymax = max(max(devs), eps) * 1.18
    ax.set_ylim(0, ymax)
    for b, v in zip(bars, devs):
        ax.text(b.get_x() + b.get_width() / 2, v + ymax * 0.018,
                f"{v:.3f}", ha="center", va="bottom",
                fontsize=8.8, color=SLATE)

    from matplotlib.patches import Patch
    handles = [
        Patch(facecolor=OLIVE, label="weak family"),
        Patch(facecolor=TEAL,  label="complete family"),
    ] + ax.get_legend_handles_labels()[0]
    ax.legend(handles=handles, loc="upper right")

    fig.tight_layout()
    fig.savefig(out_path, dpi=DPI)
    print(f"saved {out_path}")
    plt.close(fig)


def fig_sample_curve(d, out_path):
    """log-x line plot of detection rate vs shot budget."""
    labels = list(d["results"].keys())
    shots = [d["results"][k]["shots_per_obs"] for k in labels]
    rates = [d["results"][k]["detection_rate"] for k in labels]
    target = 1 - d["eta"]

    order = np.argsort(shots)
    shots = [shots[i] for i in order]
    rates = [rates[i] for i in order]
    labels = [labels[i] for i in order]

    fig, ax = plt.subplots(figsize=(6.0, 3.7))
    ax.set_axisbelow(True)
    ax.yaxis.grid(True)
    ax.xaxis.grid(True)

    ax.plot(shots, rates, "-", color=TEAL, linewidth=1.6, zorder=2)
    ax.scatter(shots, rates, s=58, color=TEAL,
               edgecolor="white", linewidth=1.0, zorder=3)

    ax.axhline(target, color=BORDX, linestyle="-", linewidth=1.3,
               label=fr"target $1 - \eta = {target:.2f}$")

    for x, y, lab in zip(shots, rates, labels):
        ax.annotate(
            lab, (x, y),
            textcoords="offset points", xytext=(8, -2),
            fontsize=9, color=SLATE,
        )

    ax.set_xscale("log")
    ax.set_xlabel("shots per observable")
    ax.set_ylabel("empirical detection rate")
    ax.set_ylim(-0.04, 1.06)
    ax.set_title("Detection rate vs measurement budget")
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(out_path, dpi=DPI)
    print(f"saved {out_path}")
    plt.close(fig)


def fig_drift_panel(d, out_path):
    """two-panel: fingerprint per timepoint (top), pairwise max
    deviations (bottom)."""
    fps = d["fingerprints"]
    family = list(fps[0].keys())
    n_t = len(fps)
    vals = np.array([[fps[t][p] for p in family] for t in range(n_t)])

    d_drift = d.get("d_drift_typ", None)
    interval = d.get("tolerance_interval", None)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(6.4, 5.4),
        gridspec_kw={"height_ratios": [2, 1.2]},
    )
    for ax in (ax1, ax2):
        ax.set_axisbelow(True)
        ax.yaxis.grid(True)

    colors = [TEAL, OLIVE, BORDX, "#5a5a8a"][:n_t]
    markers = ["o", "s", "^", "D"][:n_t]
    x = np.arange(len(family))
    for t in range(n_t):
        ax1.plot(x, vals[t],
                 color=colors[t],
                 marker=markers[t],
                 markersize=6.5,
                 linewidth=1.5,
                 label=f"timepoint $t_{{{t}}}$")
    ax1.set_xticks(x)
    ax1.set_xticklabels(family)
    ax1.set_ylabel(r"$\langle P \rangle$")
    ax1.set_title("Honest fingerprint across timepoints")
    ax1.legend(loc="best", ncol=n_t)

    pairwise = d.get("pairwise_deviations", {})
    if pairwise:
        labels = list(pairwise.keys())
        values = [pairwise[k] for k in labels]
        y = np.arange(len(labels))
        ax2.barh(y, values, color=TEAL, height=0.5)
        for yi, v in zip(y, values):
            ax2.text(v + max(values) * 0.02, yi,
                     f"{v:.3f}", va="center", fontsize=9, color=SLATE)
        ax2.set_yticks(y)
        ax2.set_yticklabels(labels)
        ax2.set_xlabel("pairwise max deviation")
        if d_drift is not None:
            ax2.axvline(d_drift, color=BORDX, linestyle="-",
                        linewidth=1.3,
                        label=fr"$d_{{\mathrm{{drift}}}}^{{\mathrm{{typ}}}}"
                              fr" = {d_drift:.3f}$")
            ax2.legend(loc="lower right")
        title = "Pairwise observable drift"
        if interval:
            title += (
                f"\ntolerance interval "
                f"[{interval[0]:.3f}, {interval[1]:.3f}]"
            )
        ax2.set_title(title)

    fig.tight_layout()
    fig.savefig(out_path, dpi=DPI)
    print(f"saved {out_path}")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="json files")
    ap.add_argument("--outdir", default="results/figures")
    args = ap.parse_args()

    apply_style()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for p in args.paths:
        d = load(p)
        exp = d.get("experiment", "")
        stem = Path(p).stem
        if exp == "detection":
            fig_detection_bars(d, outdir / f"{stem}_bars.png")
        elif exp == "sample_complexity_validation":
            fig_sample_curve(d, outdir / f"{stem}_curve.png")
        elif exp == "drift_observation":
            fig_drift_panel(d, outdir / f"{stem}_panel.png")
        else:
            print(f"skipping {p}: unknown experiment type")


if __name__ == "__main__":
    main()
