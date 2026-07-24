"""
Self-Improvement Loop — single CLI entry point.

Runs the full Diagnose → Optimize → Evaluate → Success Gate cycle in one command.
This is Level 2 automation: the loop is fully wired but manually triggered.

Usage:
  PYTHONPATH=. python3 eval/loop.py [--dry-run]

Flags:
  --dry-run   Run diagnose only; report what would be fixed without running the eval.

Exit codes:
  0  — loop ran, gate passed (or no clusters to fix)
  1  — loop ran, gate FAILED (fix did not improve; reverted)
  2  — error (missing data, broken imports, etc.)
"""
import sys
import os
import json
from datetime import datetime

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from eval.diagnose import diagnose, find_latest_results
from eval.optimize import load_diagnosis, compute_stance_hills, success_gate, load_priors, save_priors


def banner(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def run_loop(dry_run: bool = False) -> int:
    """Run the full self-improvement loop. Returns exit code."""

    # ─── Step 1: Diagnose ───────────────────────────────────────────────────
    banner("STEP 1/4: DIAGNOSE")
    try:
        diagnosis = diagnose()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Run an experiment first: PYTHONPATH=. python3 eval/experiment.py")
        return 2

    clusters = diagnosis.get("clusters", [])
    if not clusters:
        print("\nNo failing clusters. System is at ceiling on current labels.")
        print("Consider: expanding the labeled set, or adjusting thresholds.")
        return 0

    # Filter to actionable clusters (skip groundedness if all runs fail — likely threshold issue)
    actionable = [c for c in clusters if not (
        c["component"] == "groundedness" and len(c.get("affected_pairs", [])) >= 5
    )]

    if not actionable:
        print("\nOnly systemic clusters remain (e.g., groundedness threshold).")
        print("These likely need methodology changes, not prompt fixes.")
        print("Remaining clusters:")
        for c in clusters:
            print(f"  [{c['impact_score']:.4f}] {c['id']}: {c['root_cause']}")
        return 0

    top_cluster = actionable[0]
    print(f"\nTop actionable cluster: {top_cluster['id']}")
    print(f"  Component: {top_cluster['component']}")
    print(f"  Root cause: {top_cluster['root_cause']}")
    print(f"  Impact: {top_cluster['impact_score']}")
    print(f"  Suggested fix: {top_cluster['suggested_fix']}")

    if dry_run:
        banner("DRY RUN — stopping here")
        print("Would attempt fix for the above cluster.")
        print("Re-run without --dry-run to execute the full loop.")
        return 0

    # ─── Step 2: Check if fix is already applied ────────────────────────────
    banner("STEP 2/4: CHECK EXISTING FIXES")
    priors = load_priors()
    existing_patterns = [p.get("pattern") for p in priors]
    if top_cluster["id"] in existing_patterns:
        print(f"Fix already applied as prior '{top_cluster['id']}'.")
        print("The cluster persists despite the fix — may need a different approach.")
        print("Consider: manual investigation or a structural code change.")
        return 0

    # ─── Step 3: Run full eval ──────────────────────────────────────────────
    banner("STEP 3/4: RUN FULL EVAL")
    print("This will take ~45-60 minutes (18 deliberations)...")
    print("Running eval/experiment.py...")

    # Capture baseline before the eval
    baseline_results = find_latest_results()
    baseline_hills = compute_stance_hills(baseline_results)
    print(f"Baseline hills: {json.dumps(baseline_hills)}")

    # Run the experiment
    from eval.experiment import main as run_experiment
    run_experiment()

    # ─── Step 4: Success Gate ───────────────────────────────────────────────
    banner("STEP 4/4: SUCCESS GATE")
    new_results = find_latest_results()
    new_hills = compute_stance_hills(new_results)
    print(f"New hills: {json.dumps(new_hills)}")

    passed, details = success_gate(baseline_hills, new_hills)
    print(f"\nSuccess Gate: {'PASSED ✓' if passed else 'FAILED ✗'}")
    print(details)

    if passed:
        # Update priors with confirmed delta
        for p in priors:
            if p.get("success_gate_delta") == "pending":
                total_old = sum(baseline_hills.values()) / len(baseline_hills)
                total_new = sum(new_hills.values()) / len(new_hills)
                p["success_gate_delta"] = f"+{total_new - total_old:.4f} mean hill"
        save_priors(priors)

        banner("LOOP COMPLETE — GATE PASSED")
        print("The fix improved the system without regression.")
        print("Commit the changes and push to master.")
        print(f"\nNew baseline: {new_results}")
        return 0
    else:
        banner("LOOP COMPLETE — GATE FAILED")
        print("The fix did NOT improve the system (or caused regression).")
        print("The fix should be reverted or refined.")
        print("\nOptions:")
        print("  1. Revert the fix and try a different approach")
        print("  2. Refine the fix (narrow scope, adjust wording)")
        print("  3. Accept the regression if it's a known tradeoff")
        return 1


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    exit_code = run_loop(dry_run=dry_run)
    sys.exit(exit_code)
