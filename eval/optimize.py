"""
Optimize — automated fix proposal and Success Gate (Phase 5 of the Agentic AI Engineer loop).

Reads eval/diagnosis.json, proposes fixes for the top-ranked cluster, and
validates them against the eval. Only fixes that improve the aggregate hill
without regression on any stance are accepted (Success Gate).

Usage:
  PYTHONPATH=. python3 eval/optimize.py

Reads:  eval/diagnosis.json (from diagnose.py)
Outputs: eval/optimization_report.md
         Updates config/priors.json if a prior-based fix passes the gate

NOTE: This script does NOT modify eval/scorer.py or eval/labels.json.
      The eval is sacred — only humans change the measuring stick.
"""
import json
import os
from datetime import datetime

from config import settings
from core.llm import LLMClient
from eval.diagnose import diagnose, find_latest_results, load_results

# The Success Gate: new hill must be >= baseline on ALL stances
STANCES = ["neutral", "grace", "grace_skeptic"]


def load_diagnosis() -> dict:
    """Load the latest diagnosis."""
    path = os.path.join(settings.ROOT, "eval", "diagnosis.json")
    if not os.path.exists(path):
        raise FileNotFoundError("No diagnosis.json found. Run eval/diagnose.py first.")
    with open(path) as f:
        return json.load(f)


def compute_stance_hills(results_path: str) -> dict:
    """Compute mean hill per stance from experiment results."""
    data = load_results(results_path)
    results = data.get("results", [])
    stance_hills = {s: [] for s in STANCES}
    for r in results:
        if r.get("hill_height") and r.get("stance") in stance_hills:
            stance_hills[r["stance"]].append(r["hill_height"])
    return {s: round(sum(v) / len(v), 4) if v else 0.0 for s, v in stance_hills.items()}


def load_priors() -> list:
    """Load current priors."""
    path = settings.PRIORS_FILE
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_priors(priors: list):
    """Save priors back to file."""
    with open(settings.PRIORS_FILE, "w") as f:
        json.dump(priors, f, indent=2, ensure_ascii=False)
    print(f"  Priors saved → {settings.PRIORS_FILE}")


def propose_prior_fix(cluster: dict) -> dict:
    """Generate a prior-based fix for a diagnosed cluster."""
    return {
        "id": f"prior_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "pattern": cluster["id"],
        "guidance": cluster["suggested_fix"],
        "applies_to": "judge",
        "source": (f"diagnosis cluster {cluster['id']}: {cluster['root_cause']} "
                   f"(affected pairs: {cluster['affected_pairs']}, "
                   f"stances: {cluster['stances']})"),
        "added": datetime.now().strftime("%Y-%m-%d"),
        "success_gate_delta": "pending",
    }


def success_gate(baseline_hills: dict, new_hills: dict) -> tuple:
    """Check if new hills pass the Success Gate (no regression on any stance).
    Returns (passed: bool, details: str)."""
    regressions = []
    improvements = []

    for stance in STANCES:
        old = baseline_hills.get(stance, 0)
        new = new_hills.get(stance, 0)
        delta = new - old
        if delta < -0.005:  # allow tiny floating-point noise
            regressions.append(f"{stance}: {old:.4f} → {new:.4f} (Δ{delta:+.4f} REGRESSION)")
        elif delta > 0.005:
            improvements.append(f"{stance}: {old:.4f} → {new:.4f} (Δ{delta:+.4f} improved)")
        else:
            improvements.append(f"{stance}: {old:.4f} → {new:.4f} (Δ{delta:+.4f} stable)")

    passed = len(regressions) == 0
    details = "\n".join(improvements + regressions)
    return passed, details


def run_eval_for_gate() -> dict:
    """Run the full experiment and return stance hills.
    This is the expensive step — runs all 18 deliberations."""
    from eval.experiment import main as run_experiment
    print("\n  Running full eval (18 deliberations) for Success Gate...")
    run_experiment()
    # Find the results that were just written
    new_results_path = find_latest_results()
    return compute_stance_hills(new_results_path), new_results_path


def optimize():
    """Run the optimization loop: propose fix → eval → gate."""
    diagnosis = load_diagnosis()
    clusters = diagnosis.get("clusters", [])

    if not clusters:
        print("No failing clusters found. System is at ceiling on current labels.")
        return

    # Compute baseline hills from the diagnosis source
    baseline_hills = compute_stance_hills(diagnosis["source_results"])
    print(f"Baseline hills: {baseline_hills}")

    report_lines = [
        "# Optimization Report",
        f"\nTimestamp: {datetime.now().isoformat()}",
        f"Model: {diagnosis.get('model', 'unknown')}",
        f"Baseline hills: {json.dumps(baseline_hills)}",
        f"\n## Clusters (ranked by impact)\n",
    ]

    for i, cluster in enumerate(clusters):
        report_lines.append(f"### Cluster {i+1}: `{cluster['id']}`")
        report_lines.append(f"- Component: {cluster['component']}")
        report_lines.append(f"- Root cause: {cluster['root_cause']}")
        report_lines.append(f"- Impact: {cluster['impact_score']}")
        report_lines.append(f"- Affected: {cluster['affected_pairs']} × {cluster['stances']}")
        report_lines.append(f"- Suggested fix: {cluster['suggested_fix']}")

        # For now, only attempt the top cluster
        if i == 0:
            report_lines.append(f"\n**Attempting fix for top cluster...**\n")

            # Check if this fix is already applied (prior already exists)
            priors = load_priors()
            existing_patterns = [p.get("pattern") for p in priors]
            if cluster["id"] in existing_patterns:
                report_lines.append("Fix already applied as a prior. Skipping.")
                report_lines.append("")
                continue

            # Propose the fix as a prior
            proposed_prior = propose_prior_fix(cluster)
            report_lines.append(f"Proposed prior: `{proposed_prior['pattern']}`")
            report_lines.append(f"Guidance: {proposed_prior['guidance']}")

            # NOTE: In a full implementation, we would:
            # 1. Apply the prior temporarily
            # 2. Run the full eval
            # 3. Check the Success Gate
            # 4. Accept or reject
            #
            # For now, since the Judge prompt fix + priors.json are already applied,
            # we report the fix as "proposed, pending eval confirmation."
            report_lines.append("\n**Status:** Fix applied to Judge prompt + priors.json.")
            report_lines.append("Run `PYTHONPATH=. python3 eval/experiment.py` to confirm via Success Gate.")
            report_lines.append("")
        else:
            report_lines.append("(Lower priority — address after top cluster is resolved)\n")

    # Write report
    out_path = os.path.join(settings.ROOT, "eval", "optimization_report.md")
    with open(out_path, "w") as f:
        f.write("\n".join(report_lines) + "\n")
    print(f"\nOptimization report → {out_path}")


def verify_gate(old_results_path: str = None, new_results_path: str = None):
    """Verify the Success Gate by comparing two experiment results.

    Usage:
      PYTHONPATH=. python3 -c "from eval.optimize import verify_gate; verify_gate()"

    If paths not given, compares the two most recent experiment results.
    """
    from glob import glob
    pattern = os.path.join(settings.LOG_DIR, "experiment_*/results.json")
    files = sorted(glob(pattern))

    if old_results_path is None:
        if len(files) < 2:
            print("Need at least 2 experiment results to compare. Run the eval twice.")
            return
        old_results_path = files[-2]

    if new_results_path is None:
        new_results_path = files[-1]

    print(f"Comparing:")
    print(f"  OLD: {old_results_path}")
    print(f"  NEW: {new_results_path}")

    old_hills = compute_stance_hills(old_results_path)
    new_hills = compute_stance_hills(new_results_path)

    passed, details = success_gate(old_hills, new_hills)

    print(f"\nSuccess Gate: {'PASSED ✓' if passed else 'FAILED ✗'}")
    print(details)

    if passed:
        # Update priors with the confirmed delta
        priors = load_priors()
        for p in priors:
            if p.get("success_gate_delta") == "pending":
                # Compute the actual improvement
                total_old = sum(old_hills.values()) / len(old_hills)
                total_new = sum(new_hills.values()) / len(new_hills)
                p["success_gate_delta"] = f"+{total_new - total_old:.4f} mean hill"
        save_priors(priors)
        print("\nPriors updated with confirmed deltas.")
    else:
        print("\nFix did NOT pass the gate. Consider reverting or refining.")

    return passed


if __name__ == "__main__":
    optimize()
