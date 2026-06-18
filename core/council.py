"""
Council orchestrator — the negotiation LOOP.

This is the part you wanted to see naked. The loop:

  for round in 1..MAX_ROUNDS:
      1. each agent assesses (given profiles + last round's debate)   <- self-healing here
      2. (optional) critic pass catches claims contradicting profiles <- self-correction (council_critic.py)
      3. compute score spread + referee quality -> HILL SCORE          <- climb the hill
      4. decide whether to STOP:                                       <- loop engineering
           - must run >= MIN_ROUNDS
           - stop if agents have converged (spread < SCORE_SPREAD_STOP)
           - stop if the hill has PLATEAUED (improvement < CONVERGENCE_DELTA)
           - else continue, feeding this round's debate into the next

Everything is logged: every agent turn, every round, every hill point, every
healing/correction event.
"""
from dataclasses import asdict
from typing import List

from agents.agent import Agent, Turn
from agents.personas import ALL_AGENTS
from core import hill as hillmod
from core.llm import LLMClient
from core.logbook import Logbook
from config import settings


class Council:
    def __init__(self, client: LLMClient, log: Logbook, personas=None, critic=None):
        self.client = client
        self.log = log
        personas = personas or ALL_AGENTS
        self.agents = [Agent(p, client) for p in personas]
        self.critic = critic  # optional callable(profiles_json, turns, round, log) -> corrected turns
        self.history: List[List[Turn]] = []  # per-round list of turns
        self.hill_history: List[float] = []
        self.spread_history: List[float] = []  # score spread per round (for eval)
        self.critic_fired: bool = False        # did self-correction trigger? (for eval)
        self.engagement_seen: bool = False      # did agents react to each other? (for eval)

    def _debate_summary(self, turns: List[Turn]) -> str:
        if not turns:
            return ""
        return "\n".join(
            f"- {t.agent} (score {t.score:.2f}): {t.position}"
            for t in turns if not t.down
        )

    def _round_text(self, turns: List[Turn]) -> str:
        return "\n".join(
            f"{t.agent} [{t.layer}] score={t.score:.2f} | {t.position} | reacts: {t.reaction}"
            for t in turns if not t.down
        )

    def deliberate(self, profiles_json: str) -> dict:
        prev_summary = ""
        for r in range(1, settings.MAX_ROUNDS + 1):
            self.log.round_header(r)

            # --- 1. each agent takes a turn (self-healing inside Agent.assess)
            turns: List[Turn] = []
            for agent in self.agents:
                turn = agent.assess(profiles_json, prev_summary, round_idx=r)
                if turn.down:
                    self.log.healing(r, agent.name,
                                     "LLM call failed; dropped this round, council continues.")
                else:
                    self.log.agent_turn(r, turn.agent, turn.score, turn.position,
                                        turn.reaction, turn.latency_s)
                turns.append(turn)

            # self-healing safeguard: if EVERY agent died, abort cleanly
            live = [t for t in turns if not t.down]
            if not live:
                self.log.healing(r, "council", "All agents down this round; aborting deliberation.")
                break

            # detect engagement: any live agent reacting to others this round
            if any((not t.down) and t.reaction.strip() for t in turns):
                self.engagement_seen = True

            # --- 2. self-correction (optional critic pass)
            if self.critic is not None:
                before_positions = [(t.agent, t.score) for t in turns]
                turns = self.critic(profiles_json, turns, r, self.log)
                live = [t for t in turns if not t.down]
                if [(t.agent, t.score) for t in turns] != before_positions:
                    self.critic_fired = True

            # --- 3. compute the hill
            scores = [t.score for t in live]
            spread = hillmod.score_spread(scores)
            self.spread_history.append(spread)
            ref = hillmod.referee_quality(self.client, profiles_json, self._round_text(turns))
            if ref.get("down"):
                self.log.healing(r, "referee", "Referee unavailable; used neutral quality estimate.")
            h = hillmod.hill_score(ref["grounded"], ref["engaged"], spread, r)
            self.log.hill(r, h, spread, detail={"grounded": ref["grounded"],
                                                "engaged": ref["engaged"],
                                                "referee_note": ref.get("note", "")})
            self.history.append(turns)
            self.hill_history.append(h)

            # --- 4. stopping decision (loop engineering)
            stop, why = self._should_stop(r, spread)
            if stop:
                self.log.note(f"Stopping after round {r}: {why}")
                break
            prev_summary = self._debate_summary(turns)

        return self._final_state()

    def _should_stop(self, r: int, spread: float):
        if r < settings.MIN_ROUNDS:
            return False, "below MIN_ROUNDS"
        if spread < settings.SCORE_SPREAD_STOP:
            return True, f"agents converged (spread {spread:.3f} < {settings.SCORE_SPREAD_STOP})"
        if len(self.hill_history) >= 2:
            gain = self.hill_history[-1] - self.hill_history[-2]
            if gain < settings.CONVERGENCE_DELTA:
                return True, (f"hill plateaued (gain {gain:+.3f} < {settings.CONVERGENCE_DELTA}); "
                              "more rounds won't improve judgment quality")
        if r >= settings.MAX_ROUNDS:
            return True, "reached MAX_ROUNDS"
        return False, ""

    def _final_state(self) -> dict:
        last = self.history[-1] if self.history else []
        return {
            "rounds_run": len(self.history),
            "final_turns": [asdict(t) for t in last],
            "hill_history": self.hill_history,
            "spread_history": self.spread_history,
            "critic_fired": self.critic_fired,
            "engagement_seen": self.engagement_seen,
        }
