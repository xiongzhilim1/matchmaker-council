"""
Self-correction: the critic pass.

After agents speak in a round, a Critic checks each LIVE turn against the
profile facts and flags claims that are UNSUPPORTED or CONTRADICTED. For any
flagged turn, we give that agent ONE chance to revise its position/score with
the critique in hand. The correction happens WITHIN the same task (this is what
distinguishes self-correction from self-learning, which is across tasks).

Self-healing note: if the critic LLM call dies, we skip correction this round
(log it) rather than crash.
"""
from typing import List

from agents.agent import Agent, Turn
from core.llm import LLMClient, LLMDown
from core.logbook import Logbook
from agents.personas import ALL_AGENTS

CRITIC_SYSTEM = """You are a fact-grounding critic for a matchmaking council.
Given the PROFILES and an agent's claim, decide if the claim is SUPPORTED by the
profile facts, or UNSUPPORTED / CONTRADICTED (invented, exaggerated, or against the data).
Be strict but fair: reasonable inference from stated facts is SUPPORTED.
Reply ONLY JSON: {"verdict": "supported"|"contradicted", "issue": "<=40 words, '' if supported"}"""


def _persona_for(name):
    for p in ALL_AGENTS:
        if p["name"] == name:
            return p
    return None


def make_critic(client: LLMClient):
    """Returns a critic callable compatible with Council(critic=...)."""

    def critic(profiles_json: str, turns: List[Turn], round_idx: int, log: Logbook) -> List[Turn]:
        corrected: List[Turn] = []
        for t in turns:
            if t.down or not t.position:
                corrected.append(t)
                continue
            try:
                check = client.complete_json(
                    CRITIC_SYSTEM,
                    f"PROFILES:\n{profiles_json}\n\nAGENT {t.agent} CLAIM:\n"
                    f"score={t.score:.2f}; position={t.position}\n\nEvaluate this claim.",
                )
            except (LLMDown, Exception):
                log.healing(round_idx, "critic", "Critic call failed; skipping correction for this turn.")
                corrected.append(t)
                continue

            if check.get("verdict") == "contradicted":
                issue = check.get("issue", "claim not supported by profile facts")
                log.correction(round_idx, t.agent,
                               f"Critic flagged: {issue} — asking agent to revise.")
                revised = _ask_agent_to_revise(client, t, profiles_json, issue, round_idx, log)
                corrected.append(revised)
            else:
                corrected.append(t)
        return corrected

    return critic


def _ask_agent_to_revise(client, turn: Turn, profiles_json, issue, round_idx, log) -> Turn:
    persona = _persona_for(turn.agent)
    if persona is None:
        return turn
    agent = Agent(persona, client)
    debate = (f"CRITIC FEEDBACK on your last claim: {issue}\n"
              f"Your previous position was: {turn.position} (score {turn.score:.2f}).\n"
              "Revise to be strictly grounded in the profile facts. Adjust score if warranted.")
    revised = agent.assess(profiles_json, debate)
    if not revised.down:
        log.event("self_correction_applied", round=round_idx, agent=turn.agent,
                  old_score=turn.score, new_score=revised.score,
                  old_position=turn.position, new_position=revised.position)
        log.md(f"> 🔧 `{turn.agent}` revised: score {turn.score:.2f} → "
               f"**{revised.score:.2f}**. New position: {revised.position}\n")
    return revised
