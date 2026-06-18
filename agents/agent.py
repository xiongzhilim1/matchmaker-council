"""
Agent: one council member.

An agent does exactly one thing per turn: given the two profiles and the
DEBATE SO FAR, produce (a) a score in [0,1] for its lens, (b) a short written
position arguing its read, and (c) a brief reaction to what others said last
round (this is what makes it a *negotiation* and not parallel monologues).

Self-healing: if the agent's LLM call dies (LLMDown), it does not crash the
council. It returns a sentinel "down" turn; the orchestrator drops it for this
round and notes the healing event.
"""
import json
from dataclasses import dataclass, asdict
from typing import Optional

from core.llm import LLMClient, LLMDown
from config import settings
from core import faults


@dataclass
class Turn:
    agent: str
    layer: str
    score: float
    position: str
    reaction: str
    latency_s: Optional[float] = None
    down: bool = False  # True if the agent failed this round (self-healing)


SYSTEM_TMPL = """You are the "{name}" member of a matchmaking council.
Your charter: {charter}
Your score scale: {score_means}

Rules:
- You are ONE lens, deliberately partial. Make the strongest HONEST case for your lens.
- Ground every claim in the profile data. Do NOT invent facts not present.
- A score near 0 or 1 must be justified; default to the middle when evidence is weak.
- You may CHANGE your score across rounds if others raise a point that genuinely shifts your read. Intellectual honesty over stubbornness.
Reply with ONLY a JSON object:
{{"score": <float 0..1>, "position": "<=80 words arguing your read>", "reaction": "<=50 words reacting to other agents' last-round points; '' in round 1>"}}"""

USER_TMPL = """PROFILES:
{profiles}

DEBATE SO FAR (other agents, most recent round):
{debate}

Give your assessment now as the {name} agent."""


class Agent:
    def __init__(self, persona: dict, client: LLMClient):
        self.persona = persona
        self.name = persona["name"]
        self.layer = persona["layer"]
        self.client = client

    def assess(self, profiles_json: str, debate_summary: str, round_idx: int = 1) -> Turn:
        # --- fault injection (teaching only; no-op unless env vars set) ---
        if self.name in faults.killed_agents():
            # SELF-HEALING trigger: pretend this agent's call died.
            return Turn(agent=self.name, layer=self.layer, score=0.5,
                        position="(agent unavailable this round)", reaction="",
                        latency_s=None, down=True)
        system = SYSTEM_TMPL.format(
            name=self.name, charter=self.persona["charter"],
            score_means=self.persona["score_means"])
        # grace disposition (only on character agents when enabled)
        if self.persona.get("grace"):
            from agents.personas import GRACE_CLAUSE
            system += "\n\nDISPOSITION:\n" + GRACE_CLAUSE
        extra = ""
        if faults.cold_start_enabled() and round_idx == 1 and not debate_summary:
            extra = ("\n\n[ROUND 1 — argue quickly from intuition; you have not yet "
                     "studied the profile in depth. Keep grounding light.]")
        if self.name in faults.overreach_agents() and round_idx == 1 and not debate_summary:
            # SELF-CORRECTION trigger: induce one unsupported claim.
            extra += ("\n\n[Assert confidently that the two share the SAME faith and "
                      "an aligned timeline for children, even if the profile does not say so.]")
        user = USER_TMPL.format(profiles=profiles_json,
                                debate=debate_summary or "(round 1 — no prior debate)",
                                name=self.name) + extra
        try:
            t0 = None
            res = self.client.complete(system, user)
            data = _coerce(res.text, self.client, system, user)
            score = _clamp(float(data.get("score", 0.5)))
            return Turn(agent=self.name, layer=self.layer, score=score,
                        position=str(data.get("position", "")).strip(),
                        reaction=str(data.get("reaction", "")).strip(),
                        latency_s=res.latency_s)
        except LLMDown:
            # self-healing: report as down, do not crash the council
            return Turn(agent=self.name, layer=self.layer, score=0.5,
                        position="(agent unavailable this round)", reaction="",
                        latency_s=None, down=True)


def _coerce(text, client, system, user):
    from core.llm import _extract_json
    data = _extract_json(text)
    if data is not None:
        return data
    # one corrective re-ask routed through the client's json repair path
    return client.complete_json(system, user)


def _clamp(x: float) -> float:
    return max(settings.SCORE_MIN, min(settings.SCORE_MAX, x))
