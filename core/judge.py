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
from typing import List

from agents.agent import Turn
from core.llm import LLMClient, LLMDown
from core.logbook import Logbook

JUDGE_SYSTEM = """You are the Judge of a matchmaking council. You make the final call,
but your real product is a TRANSPARENT rationale a wise human matchmaker could act on.

How to weigh (do NOT just average):
- COMPATIBILITY lenses (values/faith, attraction/spark, life-stage/practical, emotional-pattern fit)
  describe the match "on paper".
- CHARACTER lenses (emotional maturity, willingness to be refined) are a MULTIPLIER on the long term:
  high spark + low growth tends to rot; humility + growth can redeem real mismatch over time.
- HARD DEALBREAKERS must be NAMED and honored, not averaged away. BUT only treat something as a
  dealbreaker if a person ACTUALLY DECLARED it as non-negotiable; do NOT invent dealbreakers.
- Hold GRACE AND HOPE in tension with the SKEPTIC: attraction can be cultivated when character is
  strong; low maturity can be redeemed over time THROUGH faith, counsel, and community support.
- HOWEVER, weigh the RealityCheck (adversarial) lens seriously: TRUST and SAFETY are a GATE. A
  concealed pattern, non-disclosure, or one partner over-functioning OUTWEIGHS strong on-paper fit.
  Hope must never be used to paper over a safety/trust problem.
- Your rationale MUST show you weighed grace AGAINST the skeptic, not let either win by default.
- It is legitimate to output "conditional" or "not yet" rather than a blunt yes/no. On genuinely
  ambiguous pairs, be HONESTLY UNCERTAIN: do not report high confidence on a hard call.

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
    user = (f"PROFILES:\n{profiles_json}\n\n"
            f"FINAL COUNCIL POSITIONS:\n{council_view}\n\n"
            f"Debate quality climbed across rounds (hill scores): {hill_history}\n{stance_note}\n"
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
