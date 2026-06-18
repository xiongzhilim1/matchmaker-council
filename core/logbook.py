"""
Logbook: capture EVERYTHING so the journey is reconstructable and the
multi-part post writes itself.

For every run we produce, under logs/<run_id>/:
  - events.jsonl   : one machine-readable line per event (agent turn, round
                     summary, hill-score, critic catch, healing event, verdict)
  - transcript.md  : a human-readable narrative of the same, in order
  - hill.csv       : round, hill_score, score_spread  (so you can chart the climb)

Every event carries: timestamp, run_id, phase, round, agent (if any), and a
free-form payload. The point is that NOTHING the council does is invisible.
"""
import csv
import json
import os
import time
from datetime import datetime, timezone

from config import settings


class Logbook:
    def __init__(self, run_id: str = None):
        self.run_id = run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")
        self.dir = os.path.join(settings.LOG_DIR, self.run_id)
        os.makedirs(self.dir, exist_ok=True)
        self.events_path = os.path.join(self.dir, "events.jsonl")
        self.transcript_path = os.path.join(self.dir, "transcript.md")
        self.hill_path = os.path.join(self.dir, "hill.csv")
        # init transcript + hill files
        with open(self.transcript_path, "w") as f:
            f.write(f"# Council transcript — run `{self.run_id}`\n\n")
        with open(self.hill_path, "w", newline="") as f:
            csv.writer(f).writerow(["round", "hill_score", "score_spread"])

    # -- core writer ---------------------------------------------------------
    def event(self, kind: str, *, round: int = None, agent: str = None, **payload):
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "kind": kind,
            "round": round,
            "agent": agent,
            "payload": payload,
        }
        with open(self.events_path, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    # -- human-readable transcript helpers ----------------------------------
    def md(self, text: str):
        with open(self.transcript_path, "a") as f:
            f.write(text + "\n")

    def round_header(self, n: int):
        self.md(f"\n## Round {n}\n")

    def agent_turn(self, round: int, agent: str, score: float, position: str,
                   critique_of_others: str = "", latency_s: float = None):
        self.event("agent_turn", round=round, agent=agent, score=score,
                   position=position, critique_of_others=critique_of_others,
                   latency_s=latency_s)
        self.md(f"**{agent}** — score `{score:.2f}`"
                + (f"  _(latency {latency_s}s)_" if latency_s is not None else ""))
        self.md(f"\n> {position}\n")
        if critique_of_others:
            self.md(f"_Reacting to others:_ {critique_of_others}\n")

    def hill(self, round: int, hill_score: float, score_spread: float, detail: dict = None):
        self.event("hill_score", round=round, hill_score=hill_score,
                   score_spread=score_spread, detail=detail or {})
        with open(self.hill_path, "a", newline="") as f:
            csv.writer(f).writerow([round, f"{hill_score:.4f}", f"{score_spread:.4f}"])
        self.md(f"_Hill-score after round {round}: **{hill_score:.3f}** "
                f"(quality of the judgment) | score spread among agents: {score_spread:.3f}_\n")

    def healing(self, round: int, agent: str, what: str):
        self.event("self_healing", round=round, agent=agent, what=what)
        self.md(f"> ⚕️ **Self-healing:** agent `{agent}` — {what}\n")

    def correction(self, round: int, agent: str, what: str):
        self.event("self_correction", round=round, agent=agent, what=what)
        self.md(f"> 🔧 **Self-correction:** {what} (agent `{agent}`)\n")

    def verdict(self, payload: dict):
        self.event("verdict", **payload)
        self.md("\n## Final verdict (Judge)\n")
        self.md(f"**Decision:** {payload.get('decision')}  |  "
                f"**Confidence:** {payload.get('confidence')}\n")
        self.md(f"\n{payload.get('rationale','')}\n")

    def note(self, text: str):
        """A design/narration note, for the post."""
        self.event("note", text=text)
        self.md(f"\n> _Note: {text}_\n")
