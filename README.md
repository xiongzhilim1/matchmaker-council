# Matchmaker Spine — A Multi-Agent Council for Compatibility Judgment

A v0 "spine" of a multi-agent matchmaking system. Multiple agents with distinct
capabilities divide the judgment, debate across rounds, negotiate, and a Judge
renders a transparent verdict — grounded in a *growth & grace* worldview and
balanced by an adversarial skeptic.

This repo is also a teaching artifact: it demonstrates **loop engineering,
hill-climbing, self-correction, and self-healing** in plain Python (no heavy
agent framework), plus an **objective, human-labeled evaluation harness**.

See `docs/post_final.md` for the full design narrative and the A/B/C calibration
experiment results.

## Quick start

```bash
# from repo root
PYTHONPATH=. python3 run.py                       # single deliberation on pair_01

# swap the model (any OpenAI-compatible model id on the proxy)
MATCHMAKER_MODEL=claude-sonnet-4-6 PYTHONPATH=. python3 run.py

# point at a different provider (e.g. Qwen / DashScope / local Ollama)
MATCHMAKER_BASE_URL=https://your-endpoint/v1 MATCHMAKER_API_KEY=... \
  MATCHMAKER_MODEL=qwen2.5-72b-instruct PYTHONPATH=. python3 run.py

# demo the self-* machinery (cold start climb + killed agent + overreach)
MATCHMAKER_COLD_START=1 MATCHMAKER_KILL_AGENT=AttractionSpark \
  MATCHMAKER_OVERREACH_AGENT=LifeStagePractical PYTHONPATH=. python3 run.py

# run the full A/B/C calibration experiment (6 pairs x 3 stances)
PYTHONPATH=. python3 eval/experiment.py
```

After any run, read the generated `logs/<run>/transcript.md` for the readable
debate, `events.jsonl` for machine-readable events, and `hill.csv` for the climb.

## Architecture

```
config/settings.py     central config: model, base_url, loop knobs (one swappable place)
core/llm.py            pluggable LLM client: retries, JSON repair, graceful LLMDown (self-healing)
core/logbook.py        structured logging: events.jsonl + transcript.md + hill.csv
core/council.py        the negotiation loop: rounds, convergence, hill, self-healing routing
core/hill.py           round-level debate-quality hill (referee-based)
core/critic.py         self-correction: flags claims contradicting profile facts, forces revision
core/judge.py          final verdict + transparent rationale; weighs grace vs skeptic
agents/personas.py     two-layer council + RealityCheck skeptic; stance modes (neutral/grace/grace_skeptic)
agents/agent.py        one council member; grace disposition injection; fault hooks
core/faults.py         deterministic fault injection for teaching the self-* concepts
eval/labels.json       HUMAN GROUND TRUTH: per-pair binding constraint, verdict band, confidence band
eval/scorer.py         objective hill: groundedness, binding-constraint hit, verdict match, calibration, anti-groupthink
eval/experiment.py     A/B/C harness: runs all pairs x stances, scores vs labels
profiles/pair_0*.json  6 synthetic pairs spanning clean-yes / clean-no / ambiguous / trap
```

## Key design decisions

- **Matchmaking has no scalar truth.** Agents are personified objectives forced
  to negotiate; the Judge collapses the debate into a legible verdict, not a
  weighted average.
- **Character is a multiplier, not an axis.** Emotional maturity and willingness
  to grow modulate the read of on-paper compatibility.
- **Grace + an adversarial skeptic.** A hopeful disposition (spark is cultivable,
  growth aided by faith/counsel, no invented dealbreakers) is balanced by a
  `RealityCheck` agent that guards trust & safety so hope never papers over risk.
- **The hill must be objective.** An LLM grading an LLM saturates. We measure
  against human labels instead — so calibration (not verdict) becomes the real
  differentiator.

## Status (checkpoint)

v0 spine complete and evaluated. Deferred: real onboarding interviewer (v1),
self-learning across many matches with memory/priors (v2), DB/UI/real users.

## Experiment headline

Across 6 labeled pairs x 3 stances (gpt-5-mini): the council reliably nails the
binding constraint and verdict band (1.00), but is **overconfident on genuinely
ambiguous pairs** (calibration ~0.84). Grace does not skew the verdict; the
skeptic is a blunt safety override that should be scoped to trust/safety rather
than given a veto over all ambiguity. Full detail in `docs/post_final.md`.
