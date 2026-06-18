"""
Entrypoint: run one matchmaking deliberation over a synthetic pair.

Usage:
    PYTHONPATH=. python3 run.py [profile_file]   # default profiles/pair_01.json

Swap the LLM with env vars (no code change):
    MATCHMAKER_MODEL=claude-sonnet-4-6 PYTHONPATH=. python3 run.py
    MATCHMAKER_MODEL=gemini-3.1-pro-preview PYTHONPATH=. python3 run.py
    # Qwen / local: also set MATCHMAKER_BASE_URL and MATCHMAKER_API_KEY_ENV
"""
import json
import os
import sys

from config import settings
from core.llm import LLMClient
from core.logbook import Logbook
from core.council import Council
from core.critic import make_critic
from core.judge import judge


def main():
    profile_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        settings.PROFILE_DIR, "pair_01.json")
    with open(profile_file) as f:
        profiles = json.load(f)
    profiles_json = json.dumps(profiles, indent=2, ensure_ascii=False)

    log = Logbook()
    client = LLMClient()
    log.note(f"Backend model: {client.model} via {client.base_url}")
    log.note(f"Loop config: MIN/MAX rounds {settings.MIN_ROUNDS}/{settings.MAX_ROUNDS}, "
             f"converge spread<{settings.SCORE_SPREAD_STOP}, plateau gain<{settings.CONVERGENCE_DELTA}")
    log.md(f"\n**Pair:** {profiles.get('pair_id')} — "
           f"{profiles['person_a']['name']} & {profiles['person_b']['name']}\n")

    council = Council(client, log, critic=make_critic(client))
    state = council.deliberate(profiles_json)
    verdict = judge(client, profiles_json, state["final_turns"], state["hill_history"], log)

    summary = {
        "run_id": log.run_id,
        "model": client.model,
        "rounds_run": state["rounds_run"],
        "hill_history": state["hill_history"],
        "verdict": verdict,
    }
    with open(os.path.join(log.dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n=== RUN COMPLETE ===")
    print("Logs:", log.dir)
    print("Rounds:", state["rounds_run"])
    print("Hill:", [round(h, 3) for h in state["hill_history"]])
    print("Decision:", verdict["decision"], "| confidence:", verdict["confidence"])
    print("Headline:", verdict["headline"])


if __name__ == "__main__":
    main()
