# ROADMAP — Matchmaker Product

Durable backlog for the Product Development track (Track A). This file is the
memory across sessions: check off what's done, keep the top item as the current
focus. Update it before ending any product session.

## Done (v0 spine — tag `v0-checkpoint`)
- [x] Pluggable LLM client (OpenAI/Claude/Qwen via one config seam) with self-healing
- [x] Structured logging (events.jsonl + transcript.md + hill.csv)
- [x] Two-layer council (compatibility + character) + adversarial RealityCheck agent
- [x] Negotiation loop: rounds, convergence detection, hill-climbing
- [x] Self-correction critic; self-healing routing around dead agents
- [x] Judge with transparent rationale (grace vs skeptic balancing)
- [x] 6 human-labeled synthetic pairs; objective label-based eval harness
- [x] A/B/C calibration experiment (neutral / grace / grace_skeptic)

## Next up (ordered; top = current focus)
- [ ] **Fix the headline weakness: calibration.** System is overconfident on
      ambiguous pairs. Try: calibration instruction in Judge prompt, or a
      confidence-critic pass, or scope the skeptic to trust/safety only (per the
      experiment finding) and re-run the A/B/C to measure improvement.
- [ ] **Scope the skeptic to a safety gate**, not a veto over all ambiguity
      (experiment showed it crushes nuance on the trap pair). Re-measure.
- [ ] **v1: onboarding interviewer agent** — turn a person into a profile via a
      structured interview (deferred from v0).
- [ ] Expand the labeled set beyond 6 pairs (more traps, more ambiguity) for a
      more robust eval signal.
- [ ] Persist runs to a small DB; add a minimal review UI for a human matchmaker
      to read debates and override (supports the option-(c) human-in-the-loop design).
- [ ] **v2: self-learning** — memory/priors across many matches; learn weights
      from human matchmaker overrides (deferred from v0).

## Open design questions (decide before building, don't assume)
- Final collapse: keep Judge-as-arbiter (a), or move toward output-the-tensions
  for a human (c)? Current build does (a) + logs the full debate for (c).
- How to represent "external support (faith/counsel/community)" as a first-class
  profile field the agents can reason over, rather than free text.
- Where real user data + consent + privacy obligations enter (before any real users).
