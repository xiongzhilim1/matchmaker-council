# SESSION LOG

Append-only ledger. One entry per working session. The point is that a fresh
session can read the latest entries and resume without re-reading any chat.

Format:
```
## YYYY-MM-DD — <track> — <short title>
- What changed:
- Where it lives (files/commits):
- NEXT (what the next session should pick up):
```

---

## 2026-06-17 — Setup/Checkpoint — v0 spine + eval harness + handoff scaffolding
- What changed: Built the v0 multi-agent matchmaker spine (council, loop, critic,
  judge, self-healing), authored 6 human-labeled synthetic pairs, built an objective
  label-based eval harness, and ran the A/B/C calibration experiment
  (neutral / grace / grace_skeptic). Wrote the design narrative (docs/post_final.md).
  Added project handoff scaffolding (PROJECT_GUIDE, ROADMAP, learning-notes index,
  research brief, this log).
- Where it lives: whole repo; tag `v0-checkpoint`. Key reads: README.md,
  docs/post_final.md, docs/PROJECT_GUIDE.md.
- Key finding: council nails binding-constraint + verdict (1.00) but is
  OVERCONFIDENT on ambiguous pairs (calibration ~0.84). Skeptic is a blunt safety
  override; should be scoped to trust/safety, not a veto over all ambiguity.
- NEXT: Split into 3 separate chat sessions per docs/PROJECT_GUIDE.md —
  (A) Product: fix calibration / scope the skeptic (top of ROADMAP.md);
  (B) Learning: start with loop engineering using core/council.py;
  (C) Research: execute docs/research/RESEARCH_BRIEF.md.
  Also: user will edit before pushing an article + hackathon submission.

## 2026-06-19 — Track C — Deep Research on Dating & Compatibility
- What changed: Executed the deep research brief. Gathered peer-reviewed literature on relationship predictors (Joel et al. 2020), attraction (Eastwick/Finkel), predictive humility (Heyman 2001, Joel 2017), attachment (TARA model), and safety/concealment. Synthesized findings into a structured report mapping research to the council's existing agents and ROADMAP priorities. Validated the `ValuesFaith`, `AttractionSpark`, and `RealityCheck` charters, while providing empirical backing to the ROADMAP priority of scoping the skeptic to safety/trust gates rather than ambiguity vetoes, and addressing calibration via predictive humility.
- Where it lives: `docs/research/REPORT.md`, `docs/research/notes.md` (scratchpad).
- NEXT: Track A (Product) to implement the ROADMAP priorities (scoping the skeptic, fixing calibration) or Track B (Learning) to start loop engineering.

## 2026-06-19 — Track A — Fix calibration + scope the skeptic to a trust/safety gate
- What changed: Worked the top ROADMAP item. Two code changes:
  (1) Scoped the `RealityCheck` skeptic from a broad adversarial veto into a NARROW
      trust/safety GATE. Rewrote its charter + score scale (`agents/personas.py`) so
      it fires only on concrete hazards (concealment/non-disclosure, abuse/coercion,
      untreated substance abuse, infidelity risk, severe demand-withdraw, one partner
      over-functioning while the other avoids accountability) and otherwise DEFAULTS
      to a high score — explicitly NOT down-scoring ordinary ambiguity (mild spark,
      slow burn, redeemable maturity, missing "courting plans").
  (2) Added explicit CALIBRATION guidance to the Judge (`core/judge.py`) and tightened
      how it uses the skeptic: treat RealityCheck as decisive only on a real hazard;
      report predictive-humility confidence (~0.45-0.65) on ambiguous-but-safe
      conditionals; never report >0.8 confidence on any conditional verdict.
- Measured impact (re-ran full A/B/C, gpt-5-mini, 6 pairs x 3 stances):
  calibration neutral 0.746->1.000, grace 0.817->1.000, grace_skeptic 0.838->0.917;
  hill 0.829->0.876 / 0.840->0.872 / 0.836->0.859. Binding-hit and verdict-match
  stayed 1.00 everywhere. Overconfidence on the safe ambiguous pairs (Ade & Joy,
  Ravi & Mei) is eliminated — both now sit inside their labeled confidence bands.
- Known residual: on the trap pair (Noah & Grace) the now-correctly-active skeptic
  pushes grace_skeptic to `not_a_match` at 0.90. That decision is still inside the
  `conditional_no` band (verdict-match 1.00) but exceeds the label's ~0.55-0.7
  confidence, scoring calibration 0.50 — the sole reason grace_skeptic is 0.917 not
  1.00. The grace (skeptic-off) stance keeps that pair perfectly calibrated at 0.65.
- Where it lives: `agents/personas.py`, `core/judge.py`; ROADMAP.md updated (two items
  checked off, new top item added). Baseline run: logs/experiment_20260619_003129;
  post-change run: logs/experiment_20260619_014131 (report.md + summary.csv).
- NEXT: Track A — calibrate the Judge's confidence ON the trust/safety gate itself so a
  real-but-unverified hazard reads as a high-conviction PAUSE (lean-no conditional at
  ~0.6) rather than a certain not_a_match at 0.9; this should lift grace_skeptic
  calibration toward 1.00 without weakening the gate. Re-run A/B/C to confirm. (See top
  of ROADMAP.md.)
