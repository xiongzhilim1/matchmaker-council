"""
Fault injection — FOR TEACHING/DEMO ONLY.

The self-* machinery is built into the real code paths, but on an easy case it
may never visibly fire. To make the concepts demonstrable (and testable), we can
inject controlled faults via env vars, with NO change to production logic:

  MATCHMAKER_KILL_AGENT=AttractionSpark
      -> that agent's LLM call is forced to fail, so SELF-HEALING must route
         around it (drop for the round, council continues).

  MATCHMAKER_OVERREACH_AGENT=LifeStagePractical
      -> that agent is told (once, round 1) to assert an UNSUPPORTED claim, so
         the critic must catch it and force a SELF-CORRECTION.

These are read by Agent.assess via this helper. Leaving the env vars unset
yields the normal, fault-free behaviour.
"""
import os


def killed_agents() -> set:
    raw = os.environ.get("MATCHMAKER_KILL_AGENT", "")
    return {x.strip() for x in raw.split(",") if x.strip()}


def overreach_agents() -> set:
    raw = os.environ.get("MATCHMAKER_OVERREACH_AGENT", "")
    return {x.strip() for x in raw.split(",") if x.strip()}


# A cold-start nudge to make the hill visibly CLIMB: in round 1 agents argue
# with thinner grounding; grounding/engagement then improve across rounds.
def cold_start_enabled() -> bool:
    return os.environ.get("MATCHMAKER_COLD_START", "") == "1"
