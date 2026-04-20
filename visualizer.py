# ============================================================
# visualizer.py
# Generates a 3-panel dashboard from the report.
# ============================================================

import os
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

RESULTS_DIR = "results"


def plot_results(report: dict):
    os.makedirs(RESULTS_DIR, exist_ok=True)

    orig = report["per_category_original"]
    hard = report["per_category_hardened"]
    cats = sorted(orig.keys())

    orig_rates = [orig[c]["bypass_rate"] for c in cats]
    hard_rates = [hard.get(c, {}).get("bypass_rate", 0.0) for c in cats]

    s = report["summary"]

    fig = plt.figure(figsize=(18, 6))
    fig.suptitle("Adversarial Prompt Stress-Test Report", fontsize=15, fontweight="bold")

    # ── Panel 1: grouped bar per category ─────────────────────
    ax1 = fig.add_subplot(1, 3, 1)
    x     = np.arange(len(cats))
    w     = 0.35
    bars1 = ax1.bar(x - w/2, orig_rates, w, label="Original",  color="#E24B4A", alpha=0.85)
    bars2 = ax1.bar(x + w/2, hard_rates, w, label="Hardened",  color="#1D9E75", alpha=0.85)

    for bar, val in zip(list(bars1) + list(bars2), orig_rates + hard_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f"{val:.0%}", ha="center", va="bottom", fontsize=8)

    ax1.set_xticks(x)
    ax1.set_xticklabels([c.replace("_", "\n") for c in cats], fontsize=8)
    ax1.set_ylim(0, 1.15)
    ax1.set_ylabel("Bypass rate (higher = more vulnerable)")
    ax1.set_title("Bypass Rate by Attack Category")
    ax1.legend(fontsize=9)
    ax1.grid(axis="y", alpha=0.3)

    # ── Panel 2: overall score comparison ─────────────────────
    ax2 = fig.add_subplot(1, 3, 2)
    labels = ["Original\nPrompt", "Hardened\nPrompt"]
    scores = [s["original_robustness_score"], s["hardened_robustness_score"]]
    colors = ["#E24B4A", "#1D9E75"]
    bars   = ax2.bar(labels, scores, color=colors, alpha=0.85, width=0.4)

    for bar, score in zip(bars, scores):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                 f"{score:.3f}", ha="center", va="bottom", fontsize=13, fontweight="bold")

    ax2.set_ylim(0, 1.15)
    ax2.set_ylabel("Robustness score (higher = safer)")
    ax2.set_title("Overall Robustness Score")
    ax2.axhline(y=0.8, color="orange", linestyle="--", alpha=0.6, label="Target (0.8)")
    ax2.legend(fontsize=9)
    ax2.grid(axis="y", alpha=0.3)

    # Improvement arrow
    ax2.annotate(
        f"+{s['improvement_pct']}%",
        xy=(1, scores[1]), xytext=(0, scores[0]),
        arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
        ha="center", fontsize=11, color="black", fontweight="bold"
    )

    # ── Panel 3: delta heatmap ─────────────────────────────────
    ax3 = fig.add_subplot(1, 3, 3)
    deltas = [h - o for o, h in zip(orig_rates, hard_rates)]
    colors_delta = ["#1D9E75" if d <= 0 else "#E24B4A" for d in deltas]
    ax3.barh(cats, deltas, color=colors_delta, alpha=0.85)
    ax3.axvline(x=0, color="black", linewidth=0.8)

    for i, (d, cat) in enumerate(zip(deltas, cats)):
        ax3.text(d + (0.005 if d >= 0 else -0.005), i,
                 f"{d:+.0%}", va="center",
                 ha="left" if d >= 0 else "right", fontsize=9)

    ax3.set_xlabel("Change in bypass rate (negative = improvement)")
    ax3.set_title("Improvement per Category")
    ax3.grid(axis="x", alpha=0.3)

    green_patch = mpatches.Patch(color="#1D9E75", alpha=0.85, label="Improved (lower bypass)")
    red_patch   = mpatches.Patch(color="#E24B4A", alpha=0.85, label="Regressed")
    ax3.legend(handles=[green_patch, red_patch], fontsize=8)

    plt.tight_layout()
    out = f"{RESULTS_DIR}/stress_test_dashboard.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n  Dashboard saved → {out}")


if __name__ == "__main__":
    with open(f"{RESULTS_DIR}/report.json") as f:
        report = json.load(f)
    plot_results(report)