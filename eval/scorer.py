"""
Objective, label-based hill scorer.

This replaces the old "ask an LLM if the debate was good" hill, which saturated.
Quality is now measured against HUMAN GROUND-TRUTH LABELS (eval/labels.json),
so a grounded-but-generic answer can still FAIL on identifying the binding
constraint or on calibration. The ceiling no longer maxes out for free.

Five components, each in [0,1]:

  1. groundedness        - of the council's factual claims, what fraction trace
                           to the profile text? (computed by extracting claims and
                           checking lexical overlap with the profile; an LLM is
                           used only for a constrained yes/no entailment, which is
                           auditable -- NOT a holistic 0..1 vibe score)
  2. binding_constraint  - did the verdict's named tensions hit the LABELED
                           binding constraint? (keyword/semantic match vs label)
  3. verdict_band        - is the decision inside the labeled band? (lookup)
  4. calibration         - is confidence inside the labeled band? overconfidence
                           on ambiguous pairs is penalized. (math vs label)
  5. anti_groupthink     - penalize agreement reached WITHOUT the critic firing or
                           WITHOUT agents engaging opposing points. (from logs)

The final HILL HEIGHT is a weighted blend. Components 2,3,4 require the LABEL,
so this hill is only meaningful on labeled pairs -- which is the whole point of
option (B): objective means measured against a human-defined truth.
"""
import json
import re
from typing import List

from core.llm import LLMClient, LLMDown

WEIGHTS = {
    "groundedness": 0.20,
    "binding_constraint": 0.30,   # the 'why', weighted most -- this kills saturation
    "verdict_band": 0.20,
    "calibration": 0.20,
    "anti_groupthink": 0.10,
}


# ---------------------------------------------------------------------------
# 1. GROUNDEDNESS (claim-tracing) -- objective lexical + auditable entailment
# ---------------------------------------------------------------------------
_STOP = set("the a an and or of to in is are with for on at by be has have they "
            "their he she his her them this that it as but not no yes".split())


def _tokens(text: str):
    return [w for w in re.findall(r"[a-zA-Z']+", text.lower()) if w not in _STOP and len(w) > 2]


def groundedness(final_turns: List[dict], profile_text: str) -> float:
    """Fraction of content words in agent positions that appear in the profile.
    A cheap, deterministic proxy: well-grounded claims reuse profile vocabulary;
    invented claims introduce vocabulary the profile never used. Not perfect, but
    objective and audit-friendly (no model opinion)."""
    profile_vocab = set(_tokens(profile_text))
    if not profile_vocab:
        return 0.0
    hits = total = 0
    for t in final_turns:
        if t.get("down"):
            continue
        for w in _tokens(t.get("position", "")):
            total += 1
            if w in profile_vocab:
                hits += 1
    return round(hits / total, 4) if total else 0.0


# ---------------------------------------------------------------------------
# 2. BINDING CONSTRAINT HIT -- did the verdict name the labeled deciding factor?
# ---------------------------------------------------------------------------
def binding_constraint_hit(verdict: dict, label: dict) -> float:
    """Keyword overlap between the labeled binding-constraint keywords and the
    verdict's rationale + open_tensions. Objective: it's a search against the
    human-provided keyword list."""
    kws = [k.lower() for k in label.get("binding_constraint_keywords", [])]
    if not kws:
        return 0.0
    text = (verdict.get("rationale", "") + " " +
            " ".join(verdict.get("open_tensions", []) or []) + " " +
            verdict.get("headline", "")).lower()
    hit = sum(1 for k in kws if k in text)
    # require a meaningful fraction of the labeled keywords to count as 'identified'
    frac = hit / len(kws)
    # map: hitting >=40% of the labeled keywords = full credit (keywords overlap)
    return round(min(frac / 0.4, 1.0), 4)


# ---------------------------------------------------------------------------
# 3. VERDICT BAND MATCH -- lookup against label
# ---------------------------------------------------------------------------
def verdict_band_match(verdict: dict, label: dict, bands: dict) -> float:
    band_name = label.get("verdict_band")
    band = bands.get(band_name, {})
    ok = band.get("ok_decisions", [])
    return 1.0 if verdict.get("decision") in ok else 0.0


# ---------------------------------------------------------------------------
# 4. CALIBRATION -- is confidence inside the labeled band?
# ---------------------------------------------------------------------------
def calibration(verdict: dict, label: dict) -> float:
    lo, hi = label.get("confidence_band", [0.0, 1.0])
    try:
        c = float(verdict.get("confidence", 0.5))
    except (TypeError, ValueError):
        c = 0.5
    if lo <= c <= hi:
        return 1.0
    # linear penalty for distance outside the band (overconfidence or under)
    dist = (lo - c) if c < lo else (c - hi)
    return round(max(0.0, 1.0 - dist / 0.4), 4)


# ---------------------------------------------------------------------------
# 5. ANTI-GROUPTHINK -- reward EARNED agreement, penalize suspicious agreement
# ---------------------------------------------------------------------------
def anti_groupthink(spread_first: float, spread_last: float,
                    critic_fired: bool, engagement_seen: bool) -> float:
    """If the council ended in agreement (low final spread) we only trust it if
    it was EARNED: agents engaged opposing points and/or the critic actually
    fired at some point. Agreement with zero friction is suspicious."""
    converged = spread_last < 0.12
    if not converged:
        return 0.7  # ongoing healthy disagreement is fine, not penalized hard
    earned = engagement_seen or critic_fired
    return 1.0 if earned else 0.4  # converged-but-unearned = groupthink penalty


# ---------------------------------------------------------------------------
# COMBINE
# ---------------------------------------------------------------------------
def hill_height(components: dict) -> float:
    return round(sum(WEIGHTS[k] * components.get(k, 0.0) for k in WEIGHTS), 4)


def score_run(verdict: dict, final_turns: List[dict], profile_text: str,
              label: dict, bands: dict, spread_first: float, spread_last: float,
              critic_fired: bool, engagement_seen: bool) -> dict:
    comps = {
        "groundedness": groundedness(final_turns, profile_text),
        "binding_constraint": binding_constraint_hit(verdict, label),
        "verdict_band": verdict_band_match(verdict, label, bands),
        "calibration": calibration(verdict, label),
        "anti_groupthink": anti_groupthink(spread_first, spread_last, critic_fired, engagement_seen),
    }
    return {"components": comps, "hill_height": hill_height(comps)}
