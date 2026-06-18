"""
A/B/C calibration experiment.

Runs every labeled pair under three stances and scores each run against the
human ground-truth labels using the objective scorer:

  A = neutral        (no grace, no skeptic)        -> expect systematic harshness
  B = grace          (grace, no skeptic)           -> expect over-optimism / poor
                                                       handling of the trap pair
  C = grace_skeptic  (grace + RealityCheck)        -> expect best calibration

Outputs:
  logs/experiment_<ts>/results.json   (per pair x stance: verdict + component scores)
  logs/experiment_<ts>/summary.csv    (aggregate hill height + calibration by stance)
  logs/experiment_<ts>/report.md      (human-readable comparison)

Usage:
  PYTHONPATH=. python3 eval/experiment.py
  MATCHMAKER_MODEL=claude-sonnet-4-6 PYTHONPATH=. python3 eval/experiment.py
"""
import csv
import json
import os
from datetime import datetime

from config import settings
from core.llm import LLMClient
from core.logbook import Logbook
from core.council import Council
from core.critic import make_critic
from core.judge import judge
from agents.personas import build_personas
from eval import scorer

STANCES = ["neutral", "grace", "grace_skeptic"]


def load_labels():
    with open(os.path.join(settings.ROOT, "eval", "labels.json")) as f:
        return json.load(f)


def run_one(client, pair_id, stance, labels):
    with open(os.path.join(settings.PROFILE_DIR, f"{pair_id}.json")) as f:
        profile = json.load(f)
    profile_text = json.dumps(profile, ensure_ascii=False)
    profiles_json = json.dumps(profile, indent=2, ensure_ascii=False)

    log = Logbook(f"exp_{pair_id}_{stance}")
    personas = build_personas(stance)
    council = Council(client, log, personas=personas, critic=make_critic(client))
    state = council.deliberate(profiles_json)
    verdict = judge(client, profiles_json, state["final_turns"],
                    state["hill_history"], log, stance=stance)

    spreads = state.get("spread_history", []) or [0.5]
    label = labels["pairs"][pair_id]
    sc = scorer.score_run(
        verdict=verdict,
        final_turns=state["final_turns"],
        profile_text=profile_text,
        label=label,
        bands=labels["verdict_bands"],
        spread_first=spreads[0],
        spread_last=spreads[-1],
        critic_fired=state.get("critic_fired", False),
        engagement_seen=state.get("engagement_seen", False),
    )
    return {
        "pair_id": pair_id,
        "names": label.get("names"),
        "stance": stance,
        "decision": verdict.get("decision"),
        "confidence": verdict.get("confidence"),
        "label_band": label.get("verdict_band"),
        "label_conf_band": label.get("confidence_band"),
        "components": sc["components"],
        "hill_height": sc["hill_height"],
        "log_dir": log.dir,
    }


def main():
    labels = load_labels()
    pair_ids = list(labels["pairs"].keys())
    client = LLMClient()

    out_dir = os.path.join(settings.LOG_DIR, datetime.now().strftime("experiment_%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)

    results = []
    for stance in STANCES:
        for pid in pair_ids:
            print(f"running {pid} | stance={stance} ...", flush=True)
            try:
                results.append(run_one(client, pid, stance, labels))
            except Exception as e:  # keep the experiment going
                print(f"  !! {pid}/{stance} failed: {e}")
                results.append({"pair_id": pid, "stance": stance, "error": str(e),
                                "hill_height": 0.0, "components": {}})

    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump({"model": client.model, "results": results}, f, indent=2, ensure_ascii=False)

    # aggregate by stance
    agg = {s: {"hill": [], "calib": [], "binding": [], "verdict": []} for s in STANCES}
    for r in results:
        if "components" not in r or not r["components"]:
            continue
        a = agg[r["stance"]]
        a["hill"].append(r["hill_height"])
        a["calib"].append(r["components"].get("calibration", 0))
        a["binding"].append(r["components"].get("binding_constraint", 0))
        a["verdict"].append(r["components"].get("verdict_band", 0))

    def mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else 0.0

    with open(os.path.join(out_dir, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["stance", "mean_hill", "mean_calibration", "mean_binding_hit", "mean_verdict_match"])
        for s in STANCES:
            a = agg[s]
            w.writerow([s, mean(a["hill"]), mean(a["calib"]), mean(a["binding"]), mean(a["verdict"])])

    _write_report(out_dir, results, agg, mean, client.model)
    print("\nEXPERIMENT COMPLETE ->", out_dir)
    for s in STANCES:
        a = agg[s]
        print(f"  {s:14s} hill={mean(a['hill']):.3f}  calib={mean(a['calib']):.3f}  "
              f"binding={mean(a['binding']):.3f}  verdict={mean(a['verdict']):.3f}")


def _write_report(out_dir, results, agg, mean, model):
    lines = [f"# A/B/C Calibration Experiment\n", f"Model: `{model}`\n",
             "Stances: **neutral** (no grace/skeptic), **grace** (grace only), "
             "**grace_skeptic** (grace + RealityCheck).\n",
             "\n## Aggregate (mean over pairs)\n",
             "| Stance | Hill | Calibration | Binding-constraint hit | Verdict-band match |",
             "|---|---|---|---|---|"]
    for s in ["neutral", "grace", "grace_skeptic"]:
        a = agg[s]
        lines.append(f"| {s} | {mean(a['hill']):.3f} | {mean(a['calib']):.3f} | "
                     f"{mean(a['binding']):.3f} | {mean(a['verdict']):.3f} |")
    lines.append("\n## Per-pair detail\n")
    lines.append("| Pair | Stance | Decision | Conf | Label band | Conf band | Binding | Calib | Hill |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        if "components" not in r or not r["components"]:
            lines.append(f"| {r.get('pair_id')} | {r.get('stance')} | ERROR | | | | | | |")
            continue
        c = r["components"]
        lines.append(f"| {r['names']} | {r['stance']} | {r['decision']} | {r['confidence']} | "
                     f"{r['label_band']} | {r['label_conf_band']} | {c['binding_constraint']:.2f} | "
                     f"{c['calibration']:.2f} | {r['hill_height']:.3f} |")
    with open(os.path.join(out_dir, "report.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
