"""
Diagnose — automated failure clustering (Phase 4 of the Agentic AI Engineer loop).

Reads the latest experiment results and clusters failures by eval component,
categorizes root causes from traces, and ranks by impact.

Usage:
  PYTHONPATH=. python3 eval/diagnose.py [path/to/results.json]

If no path is given, uses the most recent experiment_*/results.json in logs/.
Outputs: eval/diagnosis.json
"""
import json
import os
import sys
from glob import glob

from config import settings

# Thresholds below which a component is considered "failing"
THRESHOLDS = {
    "binding_constraint": 1.0,
    "calibration": 1.0,
    "verdict_band": 1.0,
    "anti_groupthink": 0.7,
    "groundedness": 0.6,
}

# Component weights from scorer.py for impact calculation
COMPONENT_WEIGHTS = {
    "groundedness": 0.20,
    "binding_constraint": 0.30,
    "verdict_band": 0.20,
    "calibration": 0.20,
    "anti_groupthink": 0.10,
}


def find_latest_results() -> str:
    """Find the most recent experiment results.json in logs/."""
    pattern = os.path.join(settings.LOG_DIR, "experiment_*/results.json")
    files = sorted(glob(pattern))
    if not files:
        raise FileNotFoundError(f"No experiment results found matching {pattern}")
    return files[-1]


def load_results(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def cluster_failures(results: list) -> list:
    """Group failing runs by component and identify affected pairs/stances."""
    clusters = {}

    for run in results:
        components = run.get("components", {})
        if not components:
            continue

        for comp_name, threshold in THRESHOLDS.items():
            score = components.get(comp_name, 1.0)
            if score < threshold:
                key = comp_name
                if key not in clusters:
                    clusters[key] = {
                        "component": comp_name,
                        "threshold": threshold,
                        "affected_runs": [],
                    }
                clusters[key]["affected_runs"].append({
                    "pair_id": run.get("pair_id"),
                    "names": run.get("names"),
                    "stance": run.get("stance"),
                    "score": score,
                    "decision": run.get("decision"),
                    "confidence": run.get("confidence"),
                    "label_band": run.get("label_band"),
                    "label_conf_band": run.get("label_conf_band"),
                })

    return list(clusters.values())


def categorize_root_cause(cluster: dict) -> str:
    """Infer a root cause category from the cluster's component and pattern."""
    comp = cluster["component"]
    runs = cluster["affected_runs"]

    if comp == "calibration":
        # Check if it's overconfidence or underconfidence
        over = sum(1 for r in runs if r.get("confidence", 0) > r.get("label_conf_band", [0, 1])[1])
        under = sum(1 for r in runs if r.get("confidence", 0) < r.get("label_conf_band", [0, 1])[0])
        if over > under:
            # Check if it's related to safety gate
            safety_pairs = [r for r in runs if "conditional_no" in str(r.get("label_band", ""))]
            if safety_pairs:
                return "Judge treats inferred trust/safety gate as certain rejection rather than high-conviction pause"
            return "Judge overconfident on ambiguous pairs — lacks predictive humility"
        return "Judge underconfident — hedging too much on clear cases"

    elif comp == "binding_constraint":
        return "System failed to name the labeled binding constraint in its rationale"

    elif comp == "verdict_band":
        # Check if it's too harsh or too lenient
        return "Verdict outside the labeled acceptable band"

    elif comp == "anti_groupthink":
        return "Agreement reached without meaningful friction (critic did not fire, no engagement)"

    elif comp == "groundedness":
        return "Agent claims not sufficiently grounded in profile text"

    return "Unknown root cause"


def suggest_fix(cluster: dict, root_cause: str) -> str:
    """Suggest a fix based on the root cause."""
    comp = cluster["component"]

    if comp == "calibration" and "trust/safety gate" in root_cause:
        return ("Add Judge calibration guidance: inferred (not confirmed) safety gate = "
                "lean-no conditional at ~0.55-0.65 confidence, not certain rejection at >0.75")

    elif comp == "calibration" and "overconfident" in root_cause:
        return ("Strengthen Judge predictive-humility guidance: ambiguous pairs cannot be "
                "reliably forecasted from pre-acquaintance profiles")

    elif comp == "binding_constraint":
        return ("Review agent prompts to ensure the binding axis is named explicitly; "
                "consider adding a 'name the deciding factor' instruction to the Judge")

    elif comp == "verdict_band":
        return ("Review Judge weighing logic — may be over-weighting one lens or "
                "ignoring the character-as-multiplier instruction")

    elif comp == "anti_groupthink":
        return ("Ensure critic is active and agents are prompted to engage opposing points; "
                "consider lowering SCORE_SPREAD_STOP or adding friction prompts")

    elif comp == "groundedness":
        return ("Tighten agent prompts to require explicit profile citations; "
                "consider making the critic stricter on unsupported claims")

    return "Manual investigation required"


def compute_impact(cluster: dict) -> float:
    """Impact = number of affected runs × weight of the failing component."""
    comp = cluster["component"]
    weight = COMPONENT_WEIGHTS.get(comp, 0.1)
    n_runs = len(cluster["affected_runs"])
    # Normalize: impact per run × weight, expressed as fraction of total possible score
    # Total runs in a full experiment = 6 pairs × 3 stances = 18
    return round(n_runs * weight / 18, 4)


def diagnose(results_path: str = None) -> dict:
    """Run the full diagnosis pipeline."""
    if results_path is None:
        results_path = find_latest_results()

    data = load_results(results_path)
    model = data.get("model", "unknown")
    results = data.get("results", [])

    # Compute baseline hill
    hills = [r.get("hill_height", 0) for r in results if r.get("hill_height")]
    baseline_hill = round(sum(hills) / len(hills), 4) if hills else 0.0

    # Cluster failures
    clusters = cluster_failures(results)

    # Enrich each cluster with root cause, suggested fix, and impact
    diagnosed_clusters = []
    for cluster in clusters:
        root_cause = categorize_root_cause(cluster)
        suggested_fix = suggest_fix(cluster, root_cause)
        impact = compute_impact(cluster)

        diagnosed_clusters.append({
            "id": f"{cluster['component']}_{'_'.join(set(r['stance'] for r in cluster['affected_runs']))}",
            "component": cluster["component"],
            "affected_pairs": list(set(r["pair_id"] for r in cluster["affected_runs"])),
            "stances": list(set(r["stance"] for r in cluster["affected_runs"])),
            "scores": [r["score"] for r in cluster["affected_runs"]],
            "root_cause": root_cause,
            "suggested_fix": suggested_fix,
            "impact_score": impact,
        })

    # Sort by impact (highest first)
    diagnosed_clusters.sort(key=lambda c: c["impact_score"], reverse=True)

    diagnosis = {
        "source_results": results_path,
        "model": model,
        "baseline_hill": baseline_hill,
        "total_runs": len(results),
        "failing_runs": sum(len(c["affected_runs"]) for c in clusters),
        "clusters": diagnosed_clusters,
    }

    # Write output
    out_path = os.path.join(settings.ROOT, "eval", "diagnosis.json")
    with open(out_path, "w") as f:
        json.dump(diagnosis, f, indent=2, ensure_ascii=False)

    print(f"Diagnosis complete → {out_path}")
    print(f"  Model: {model}")
    print(f"  Baseline hill: {baseline_hill}")
    print(f"  Failing runs: {diagnosis['failing_runs']} / {diagnosis['total_runs']}")
    print(f"  Clusters found: {len(diagnosed_clusters)}")
    for c in diagnosed_clusters:
        print(f"    [{c['impact_score']:.4f}] {c['id']}: {c['root_cause']}")

    return diagnosis


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    diagnose(path)
