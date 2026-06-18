"""
Score completed runs by reading the verdict event from each run's events.jsonl
(written incrementally), so we can analyze before the full experiment finishes.
"""
import json, os, glob
from statistics import mean
from config import settings
from eval import scorer

with open(os.path.join(settings.ROOT, "eval", "labels.json")) as f:
    labels = json.load(f)
bands = labels["verdict_bands"]


def verdict_from_events(path):
    v = None
    with open(path) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("kind") == "verdict":
                v = rec.get("payload", {})
    return v


rows = []
for d in sorted(glob.glob(os.path.join(settings.LOG_DIR, "exp_pair_*"))):
    name = os.path.basename(d)
    parts = name.split("_")
    pair_id = "_".join(parts[1:3])
    stance = "_".join(parts[3:])
    ev = os.path.join(d, "events.jsonl")
    if not os.path.exists(ev):
        continue
    verdict = verdict_from_events(ev)
    label = labels["pairs"].get(pair_id)
    if not verdict or not label:
        continue
    comp = {
        "binding": scorer.binding_constraint_hit(verdict, label),
        "verdict": scorer.verdict_band_match(verdict, label, bands),
        "calib": scorer.calibration(verdict, label),
    }
    rows.append({"pair_id": pair_id, "stance": stance,
                 "decision": verdict.get("decision"), "conf": verdict.get("confidence"),
                 "label_band": label["verdict_band"], "conf_band": label["confidence_band"],
                 **comp})

by = {}
for r in rows:
    by.setdefault(r["stance"], []).append(r)

print(f"{'stance':16s} {'n':>2s} {'binding':>8s} {'verdict':>8s} {'calib':>7s}")
for s in ["neutral", "grace", "grace_skeptic"]:
    rs = by.get(s, [])
    if not rs:
        continue
    print(f"{s:16s} {len(rs):>2d} "
          f"{mean(r['binding'] for r in rs):>8.3f} "
          f"{mean(r['verdict'] for r in rs):>8.3f} "
          f"{mean(r['calib'] for r in rs):>7.3f}")

print("\nPER-PAIR (decision | confidence vs label):")
for s in ["neutral", "grace", "grace_skeptic"]:
    if s not in by:
        continue
    print(f"\n--- {s} ---")
    for r in sorted(by[s], key=lambda x: x["pair_id"]):
        print(f"  {r['pair_id']} -> {str(r['decision']):<13s} conf={r['conf']} "
              f"| label={r['label_band']} band={r['conf_band']} "
              f"| binding={r['binding']:.2f} verdict={r['verdict']:.0f} calib={r['calib']:.2f}")
