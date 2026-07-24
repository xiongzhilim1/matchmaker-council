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
- [x] **Fix the headline weakness: calibration.** Added explicit calibration
      guidance to the Judge prompt (predictive humility: ambiguous-but-safe
      conditionals must report ~0.45-0.65 confidence; no >0.8 confidence on any
      conditional). Re-ran A/B/C: calibration neutral 0.746->1.00, grace
      0.817->1.00, grace_skeptic 0.838->0.917. Overconfidence on Ade & Joy and
      Ravi & Mei eliminated (both now land inside their confidence bands).
      (2026-06-19, Track A)
- [x] **Scope the skeptic to a safety gate**, not a veto over all ambiguity.
      Narrowed the RealityCheck charter + score scale to fire ONLY on concrete
      trust/safety hazards (concealment, abuse, severe withdrawal, over-functioning
      that compromises informed choice) and default to a high score otherwise;
      tightened the Judge to treat the skeptic as decisive only on a real hazard.
      Result: the skeptic no longer crushes nuance on the safe ambiguous pairs
      (Ade & Joy / Ravi & Mei now match grace), and still correctly gates the
      trap pair (Noah & Grace). (2026-06-19, Track A)

## Next up (ordered; top = current focus)
- [x] **Calibrate the Judge's confidence on the trust/safety GATE itself.**
      Distinguished CONCEALED/INFERRED hazards (→ pause at ~0.60 confidence) from
      DECLARED dealbreaker contradictions (→ honor as not_a_match at ~0.85). Added
      the distinction to Judge prompt + first validated prior in config/priors.json.
      Result: grace_skeptic calibration 0.917→1.000; all stances binding/verdict
      remain 1.000; no regressions (neutral +0.0003, grace +0.0058, grace_skeptic
      +0.0076 hill). Success Gate passed. (2026-07-24, Track A)
- [x] **v2 automation: Diagnose + Optimize + Self-Learning infrastructure.**
      Built eval/diagnose.py (automated failure clustering), eval/optimize.py
      (fix proposal + Success Gate verification), config/priors.json (validated
      cross-run learnings read by Judge). Full loop ran end-to-end: diagnose →
      fix → re-eval → gate passed → prior confirmed. (2026-07-24, Track A)
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
