"""
Directly verify the SELF-CORRECTION path: feed the critic a turn containing a
claim that flatly contradicts the profile, and assert the critic flags it and
the agent revises in-loop.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from core.llm import LLMClient
from core.logbook import Logbook
from core.critic import make_critic
from agents.agent import Turn

with open(os.path.join(settings.PROFILE_DIR, "pair_01.json")) as f:
    profiles_json = json.dumps(json.load(f), indent=2)

client = LLMClient()
log = Logbook("test_self_correction")
critic = make_critic(client)

# A fabricated claim: the profile says they DIFFER on faith; assert they match.
bad = Turn(agent="ValuesFaith", layer="compatibility", score=0.95,
           position=("Maya and Daniel share the exact same devout Catholic faith and have "
                     "already agreed to raise children in the Church on the same timeline."),
           reaction="", latency_s=1.0)

before = bad.score
corrected = critic(profiles_json, [bad], round_idx=1, log=log)
after = corrected[0].score

print("BEFORE position:", bad.position[:80], "... score", before)
print("AFTER  position:", corrected[0].position[:120], "... score", after)
print("Score moved:", before, "->", after)
assert after < before, "self-correction should lower the fabricated high score"
print("\nPASS: critic caught the fabricated claim and the agent revised down.")
print("Log:", log.dir)
