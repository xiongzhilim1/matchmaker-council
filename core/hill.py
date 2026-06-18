"""
The "hill" — an explicit, computable quality score for the council's CURRENT
state of judgment. Loop engineering needs a target to climb; "climb the hill"
is meaningless without defining what "higher" means.

We do NOT define quality as "agents agree" (that would just reward groupthink).
We define a GOOD judgment as one that is:

  1. GROUNDED      — agents cite profile facts, not invented ones. (proxy below)
  2. ENGAGED       — later rounds actually react to each other (negotiation,
                     not parallel monologue).
  3. RESOLVED-OR-HONESTLY-UNRESOLVED — either the agents have converged, OR the
                     remaining disagreement is explicit and located (we know
                     WHICH axis is the sticking point), not vague.

For v0 we compute a transparent proxy from the turns + an LLM "referee" pass
that rates groundedness & engagement of the round. Spread (variance of scores)
is reported separately — it measures AGREEMENT, which is an INPUT to stopping,
not the definition of quality.
"""
import statistics
from typing import List

from core.llm import LLMClient, LLMDown


def score_spread(scores: List[float]) -> float:
    """How far apart the agents are. Lower = more agreement. 0..~0.5"""
    if len(scores) < 2:
        return 0.0
    return statistics.pstdev(scores)


REFEREE_SYSTEM = """You are a neutral referee rating the QUALITY of one round of a
matchmaking council's debate. You do NOT judge the match. You judge the DEBATE.
Rate two things 0..1:
- grounded: are the agents' claims tied to the given profile facts (vs invented/vague)?
- engaged: are agents actually responding to each other's points (vs talking past)?
Reply ONLY JSON: {"grounded": <0..1>, "engaged": <0..1>, "note": "<=30 words"}"""


def referee_quality(client: LLMClient, profiles_json: str, round_text: str) -> dict:
    """LLM referee on round quality. Self-healing: if it dies, fall back to a
    neutral estimate so the loop can still proceed."""
    user = f"PROFILES:\n{profiles_json}\n\nROUND TRANSCRIPT:\n{round_text}\n\nRate the debate quality."
    try:
        data = client.complete_json(REFEREE_SYSTEM, user)
        g = float(data.get("grounded", 0.5))
        e = float(data.get("engaged", 0.5))
        return {"grounded": _c(g), "engaged": _c(e), "note": data.get("note", ""), "down": False}
    except (LLMDown, Exception):
        return {"grounded": 0.5, "engaged": 0.5, "note": "(referee unavailable)", "down": True}


def hill_score(grounded: float, engaged: float, spread: float, round_idx: int) -> float:
    """Combine into a single 0..1 hill height.

    - grounded & engaged push the score UP (good debate).
    - we add a 'resolution' term: as rounds progress, LOW spread is good
      (converging) but we only reward it after engagement is high, so we don't
      reward premature groupthink.
    """
    resolution = (1.0 - min(spread / 0.4, 1.0))  # 1 when fully agreed, 0 when far apart
    # engagement gates how much we trust agreement as 'resolution'
    resolution_term = resolution * engaged
    h = 0.45 * grounded + 0.30 * engaged + 0.25 * resolution_term
    return _c(h)


def _c(x: float) -> float:
    return max(0.0, min(1.0, x))
