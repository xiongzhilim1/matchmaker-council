"""
The Judge — architecture (a): a boss who listens to the council.

Crucially, the Judge does NOT compute a flat weighted average. Per the design,
CHARACTER agents (EmotionalMaturity, WillingnessToGrow) act as a LENS/MULTIPLIER
on the COMPATIBILITY agents' read. The Judge is instructed to:

  - read the compatibility picture (values/faith, spark, life-stage, emotional fit),
  - modulate it through the character picture (low growth/maturity discounts even
    strong compatibility; high growth can redeem some mismatch),
  - HONOR hard dealbreakers (e.g. faith + kids) rather than averaging them away,
  - output a decision + confidence + a transparent rationale that NAMES the live
    tensions, so a human matchmaker can practice option (c): decide for themselves.
"""
import json
import os
from typing import List

from agents.agent import Turn
from config import settings
from core.llm import LLMClient, LLMDown
from core.logbook import Logbook


def _load_priors() -> str:
    """Load validated priors from config/priors.json for the Judge.
    Returns a formatted string to inject into the user prompt, or '' if none."""
    path = settings.PRIORS_FILE
    if not os.path.exists(path):
        return ""
    try:
        with open(path) as f:
            priors = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ""
    judge_priors = [p for p in priors if p.get("applies_to") == "judge"]
    if not judge_priors:
        return ""
    lines = ["\nVALIDATED PRIORS (from past cases — apply where relevant):"]
    for p in judge_priors:
        lines.append(f"- [{p['pattern']}]: {p['guidance']}")
    return "\n".join(lines) + "\n"

JUDGE_SYSTEM = """You are the Judge of a matchmaking council. You make the final call,
but your real product is a TRANSPARENT rationale a wise human matchmaker could act on.

How to weigh (do NOT just average):
- COMPATIBILITY lenses (values/faith, attraction/spark, life-stage/practical, emotional-pattern fit)
  describe the match "on paper".
- CHARACTER lenses (emotional maturity, willingness to be refined) are a MULTIPLIER on the long term:
  high spark + low growth tends to rot; humility + growth can redeem real mismatch over time.
- HARD DEALBREAKERS must be NAMED and honored, not averaged away. BUT only treat something as a
  dealbreaker if a person ACTUALLY DECLARED it as non-negotiable; do NOT invent dealbreakers.
- Hold GRACE AND HOPE in tension with honesty: attraction can be cultivated when character is
  strong; low maturity can be redeemed over time THROUGH faith, counsel, and community support.
- The RealityCheck (adversarial) lens is a NARROW TRUST & SAFETY GATE, not a general veto. Treat
  it as decisive ONLY when it names a CONCRETE trust/safety hazard: concealment / non-disclosure of
  a material pattern, abuse or coercion, untreated substance abuse, infidelity risk, a severe
  demand-withdraw / stonewalling dynamic, or one partner over-functioning while the other avoids
  accountability (compromising informed choice). When such a hazard is real, it OUTWEIGHS strong
  on-paper fit and hope must never paper over it.
- If RealityCheck scores high / finds NO concrete safety hazard, DO NOT let lingering skeptic
  caution about ordinary ambiguity (mild-but-cultivable spark, slow burn, low-but-redeemable
  maturity, missing 'courting plans') push the verdict harsher or the confidence higher. Ordinary
  ambiguity is for the compatibility/character lenses to weigh, and it should resolve to a
  CALIBRATED, genuinely-uncertain conditional, not a safety veto.

CALIBRATION (this is the system's known weak spot — get it right):
- Confidence is your probability that THIS decision is correct, not how strongly the council argued.
- When the decision is "match" or "not_a_match" on a clear pair, high confidence (~0.8-0.95) is fine.
- When the decision is "conditional" BECAUSE the case is genuinely ambiguous and SAFE (no concrete
  trust/safety hazard) — e.g. the outcome hinges on whether mild spark deepens, or whether a
  redeemable pair actually uses its support — you CANNOT know the outcome from a pre-acquaintance
  profile. Report HONESTLY LOW-TO-MODERATE confidence, roughly 0.45-0.65. Predictive humility is
  REQUIRED: relationship outcomes for ambiguous pairs are not reliably forecastable.
- DISTINGUISH two kinds of "lean-no" situations:
  (a) CONCEALED / INFERRED hazard (e.g., an avoidant pattern the person has not disclosed; a
      trust/safety concern inferred from profile patterns but not confirmed through disclosure,
      therapy records, or direct observation): the correct posture is a HIGH-CONVICTION PAUSE —
      lean-no conditional at MODERATE confidence (~0.55-0.65). You are confident the CONCERN is
      real, but the OUTCOME is not certain — the person may change, disclose, or seek help.
      An inferred, unverified pattern — even a serious one — warrants a firm pause, not a
      certain rejection.
  (b) DECLARED, EXPLICIT dealbreaker contradiction (e.g., one person explicitly states "must share
      my faith" or "children are non-negotiable" and the other person's profile clearly contradicts
      this on the same axis): this IS a confirmed incompatibility. Honor it as "not_a_match" at
      appropriately high confidence (~0.80-0.90). Declared dealbreakers are stated boundaries, NOT
      inferred patterns — they must be respected, not softened by hope.
  Do NOT confuse (a) with (b). A concealed pattern warrants a pause; a declared dealbreaker
  warrants a clear rejection.
- Do NOT report very high (>0.8) confidence on any conditional verdict.
- A hedge-heavy rationale must be matched by a hedged (lower) confidence number; never pair an
  "it depends" rationale with a near-certain confidence.
- Your rationale MUST name the live tensions and show how character modulates the read.

Reply ONLY JSON:
{
 "decision": "match" | "conditional" | "not_a_match",
 "confidence": <0..1>,
 "headline": "<one sentence a matchmaker could say>",
 "rationale": "<150-250 words: name the strengths, the live tensions, how character modulates the read, and what would have to change>",
 "open_tensions": ["<short bullet>", "..."]
}"""


def judge(client: LLMClient, profiles_json: str, final_turns: List[Turn],
          hill_history, log: Logbook, stance: str = "grace_skeptic") -> dict:
    council_view = "\n".join(
        f"- {t['agent']} [{t['layer']}] score={t['score']:.2f}: {t['position']}"
        for t in final_turns if not t.get("down")
    )
    stance_note = ""
    if stance == "neutral":
        stance_note = ("\n[STANCE: NEUTRAL — judge purely on the evidence; do not apply any "
                       "special grace/hope disposition and assume no extra skeptic input.]\n")
    priors_block = _load_priors()
    user = (f"PROFILES:\n{profiles_json}\n\n"
            f"FINAL COUNCIL POSITIONS:\n{council_view}\n\n"
            f"Debate quality climbed across rounds (hill scores): {hill_history}\n{stance_note}"
            f"{priors_block}\n"
            "Render your final verdict.")
    try:
        v = client.complete_json(JUDGE_SYSTEM, user)
    except (LLMDown, Exception) as e:
        # self-healing: even if the Judge LLM fails, emit a safe, transparent fallback
        log.healing(None, "judge", f"Judge call failed ({e}); emitting conservative fallback verdict.")
        scores = [t["score"] for t in final_turns if not t.get("down")]
        avg = sum(scores) / len(scores) if scores else 0.5
        v = {
            "decision": "conditional",
            "confidence": 0.3,
            "headline": "Judge unavailable; conservative fallback based on raw council average.",
            "rationale": (f"The Judge model was unavailable, so this is a degraded fallback. "
                          f"Raw council average score was {avg:.2f}. A human should review the "
                          f"transcript directly."),
            "open_tensions": ["Judge unavailable — human review required"],
        }
    # normalize for logging
    payload = {
        "decision": v.get("decision"),
        "confidence": v.get("confidence"),
        "headline": v.get("headline", ""),
        "rationale": v.get("rationale", ""),
        "open_tensions": v.get("open_tensions", []),
    }
    log.verdict(payload)
    if payload["open_tensions"]:
        log.md("**Open tensions for the human matchmaker to weigh (practice option C):**\n")
        for t in payload["open_tensions"]:
            log.md(f"- {t}")
    return payload
