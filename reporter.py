# ============================================================
# reporter.py
# Aggregates raw attack results into a structured report.
#
# Report contains:
#   - overall robustness scores (before + after hardening)
#   - per-category bypass rates
#   - most vulnerable category
#   - most vulnerable specific attack
#   - improvement percentage
# ============================================================

import json
import os
from collections import defaultdict

RESULTS_DIR = "results"


def generate_report(
    original_results: list[dict],
    hardened_results: list[dict],
) -> dict:
    """
    Computes full report comparing original vs hardened prompt robustness.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)

    def per_category_stats(results):
        """Group bypass counts by attack category."""
        stats = defaultdict(lambda: {"total": 0, "bypassed": 0})
        for r in results:
            cat = r["category"]
            stats[cat]["total"]   += 1
            stats[cat]["bypassed"] += int(r["bypassed"])
        # Convert to bypass rates
        return {
            cat: {
                "total":       v["total"],
                "bypassed":    v["bypassed"],
                "bypass_rate": round(v["bypassed"] / max(v["total"], 1), 3),
            }
            for cat, v in stats.items()
        }

    orig_stats     = per_category_stats(original_results)
    hardened_stats = per_category_stats(hardened_results)

    # Overall scores
    orig_bypassed     = sum(r["bypassed"] for r in original_results)
    hardened_bypassed = sum(r["bypassed"] for r in hardened_results)
    total             = len(original_results)

    orig_score     = round(1 - orig_bypassed     / max(total, 1), 3)
    hardened_score = round(1 - hardened_bypassed / max(total, 1), 3)
    improvement    = round((hardened_score - orig_score) / max(1 - orig_score, 0.01) * 100, 1)

    # Most vulnerable category (highest bypass rate originally)
    most_vulnerable = max(orig_stats, key=lambda c: orig_stats[c]["bypass_rate"])

    # Most improved category
    most_improved = max(
        orig_stats.keys(),
        key=lambda c: orig_stats[c]["bypass_rate"] - hardened_stats.get(c, {}).get("bypass_rate", 0)
    )

    report = {
        "summary": {
            "total_attacks":             total,
            "original_bypassed":         orig_bypassed,
            "hardened_bypassed":         hardened_bypassed,
            "original_robustness_score": orig_score,
            "hardened_robustness_score": hardened_score,
            "improvement_pct":           improvement,
            "most_vulnerable_category":  most_vulnerable,
            "most_improved_category":    most_improved,
        },
        "per_category_original": orig_stats,
        "per_category_hardened": hardened_stats,
    }

    # Save to disk
    with open(f"{RESULTS_DIR}/report.json", "w") as f:
        json.dump(report, f, indent=2)
    with open(f"{RESULTS_DIR}/original_results.json", "w") as f:
        json.dump(original_results, f, indent=2)
    with open(f"{RESULTS_DIR}/hardened_results.json", "w") as f:
        json.dump(hardened_results, f, indent=2)

    return report


def print_report(report: dict):
    """Pretty-print the report to terminal."""
    s   = report["summary"]
    sep = "=" * 58

    print(f"\n{sep}")
    print("  PROMPT ROBUSTNESS REPORT")
    print(sep)
    print(f"  Total attacks tested  : {s['total_attacks']}")
    print(f"  Original robustness   : {s['original_robustness_score']:.3f}  ({s['original_bypassed']} bypassed)")
    print(f"  Hardened robustness   : {s['hardened_robustness_score']:.3f}  ({s['hardened_bypassed']} bypassed)")
    print(f"  Improvement           : +{s['improvement_pct']}%")
    print(f"  Most vulnerable       : {s['most_vulnerable_category']}")
    print(f"  Most improved         : {s['most_improved_category']}")
    print(sep)
    print(f"\n  {'Category':<22} {'Original':>10} {'Hardened':>10} {'Delta':>8}")
    print(f"  {'-'*22} {'-'*10} {'-'*10} {'-'*8}")

    orig = report["per_category_original"]
    hard = report["per_category_hardened"]
    all_cats = sorted(orig.keys())

    for cat in all_cats:
        o_rate = orig[cat]["bypass_rate"]
        h_rate = hard.get(cat, {}).get("bypass_rate", 0.0)
        delta  = h_rate - o_rate
        flag   = " <-- most vulnerable" if cat == s["most_vulnerable_category"] else ""
        print(f"  {cat:<22} {o_rate:>9.1%} {h_rate:>9.1%} {delta:>+7.1%}{flag}")

    print(sep)
    print(f"\n  Results saved to {RESULTS_DIR}/")