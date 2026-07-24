# matchmaker-council v2 — Specification

> **Phase 1: Conceptualize** (Agentic AI Engineer framework).
> This document is the single source of truth for v2. It defines the "why," the
> "how," and what "good" means. All Build, Evaluate, Diagnose, and Optimize work
> is measured against this spec.

---

## 1. Why (intent and business context)

v1 of the matchmaker-council is a multi-agent deliberation system that assesses
romantic compatibility. It already has a strong eval harness (`eval/scorer.py`)
and a proven architecture (notes 01–06). However, the development loop is
**entirely manual**: a human reads traces, diagnoses failures, tweaks prompts,
and re-runs the eval. This cannot scale.

v2 automates the **Diagnose → Optimize → Evaluate** loop so the system
*evolves itself* — each cycle makes it measurably better without manual
intervention, gated by objective eval improvement (the Success Gate).

Additionally, v2 introduces **self-learning** (cross-run memory): validated
learnings from past runs are stored as priors and injected into future
deliberations, so the system doesn't re-discover the same lessons from scratch.

---

## 2. Current baseline (v1 performance)

From the latest experiment (`logs/experiment_20260619_014131/report.md`):

| Stance | Hill | Calibration | Binding-hit | Verdict-match |
|---|---|---|---|---|
| neutral | 0.876 | 1.000 | 1.000 | 1.000 |
| grace | 0.872 | 1.000 | 1.000 | 1.000 |
| grace_skeptic | 0.859 | 0.917 | 1.000 | 1.000 |

**Known residual:** Noah & Grace (pair_06) under `grace_skeptic` — the Judge
over-hardens to `not_a_match` at 0.90 confidence on a trust/safety gate that
should be a high-conviction PAUSE (~0.6 confidence). This is the sole reason
`grace_skeptic` calibration is 0.917 not 1.000.

**v2 must not regress below these numbers.** Any optimization that lowers the
aggregate hill is rejected by the Success Gate.

---

## 3. What v2 adds (the "how")

### 3.1 Diagnose — automated failure clustering

A new script `eval/diagnose.py` that:

1. **Reads** the latest experiment results (`results.json`).
2. **Clusters** failures by which eval component scored below threshold:
   - `binding_constraint < 1.0` → "wrong-axis" cluster
   - `calibration < 1.0` → "overconfidence" cluster
   - `verdict_band < 1.0` → "wrong-verdict" cluster
   - `anti_groupthink < 0.7` → "unearned-agreement" cluster
3. **Categorizes** root causes by reading the corresponding trace
   (`events.jsonl`) for each failing run:
   - Did the critic fire? (if not → "unchecked hallucination")
   - Which agent dominated the final spread? (→ "lens imbalance")
   - Was the Skeptic present and did it influence? (→ "gate miscalibration")
   - Did the hill plateau early? (→ "premature stop")
4. **Ranks** clusters by impact (number of affected pairs × weight of the
   failing component).
5. **Outputs** a structured diagnosis: `eval/diagnosis.json`

```json
{
  "timestamp": "2026-07-24T...",
  "baseline_hill": 0.859,
  "clusters": [
    {
      "id": "overconfidence_gate",
      "component": "calibration",
      "affected_pairs": ["pair_06"],
      "stances": ["grace_skeptic"],
      "root_cause": "Judge treats trust/safety gate as certain rejection rather than high-conviction pause",
      "impact_score": 0.083,
      "suggested_fix": "Teach Judge that unverified safety gate = lean-no conditional at ~0.6 confidence"
    }
  ]
}
```

### 3.2 Optimize — automated fix proposal and Success Gate

A new script `eval/optimize.py` that:

1. **Reads** `eval/diagnosis.json`.
2. For each cluster (ranked by impact), uses an LLM to **propose a fix**:
   - For prompt-level issues: generates a revised prompt snippet (e.g., new
     Judge calibration guidance).
   - For weight/threshold issues: proposes a new value with rationale.
   - For structural issues: proposes a code diff (human-reviewed before merge).
3. **Applies** the fix to a temporary copy of the codebase.
4. **Re-runs** the full eval (`eval/experiment.py`) on the patched version.
5. **Compares** the new aggregate hill to the baseline:
   - If `new_hill > baseline_hill` on ALL stances → **pass** (Success Gate).
   - If any stance regresses → **reject** the fix, log the failure, move to
     the next cluster.
6. **Outputs** a report: `eval/optimization_report.md` listing which fixes
   passed, which were rejected, and the new baseline.

**Constraint:** the Optimizer must never modify `eval/scorer.py` or
`eval/labels.json` — it cannot game the eval. Only the human can change the
measuring stick.

### 3.3 Self-Learning — validated priors

A new file `config/priors.json` that:

1. **Accumulates** validated learnings — patterns confirmed by the eval to
   improve performance.
2. **Is read** by the Judge (`core/judge.py`) before opining, as additional
   context: "Based on past validated cases: [priors relevant to this pair]."
3. **Grows only** when a proposed prior passes the Success Gate (improves eval
   without regression).
4. **Is human-readable and git-versioned** — every prior has a `source` field
   tracing it to the diagnosis that generated it.

Structure:

```json
[
  {
    "id": "prior_001",
    "pattern": "trust_safety_gate_unverified",
    "guidance": "When a trust/safety concern is flagged but not confirmed/irreversible, treat as a high-conviction PAUSE (lean-no conditional, confidence 0.55-0.65) rather than a certain rejection.",
    "applies_to": "judge",
    "source": "diagnosis cluster overconfidence_gate, confirmed by eval improvement 0.917→1.000 on grace_skeptic calibration",
    "added": "2026-07-24",
    "success_gate_delta": "+0.014 hill on grace_skeptic"
  }
]
```

### 3.4 The known residual fix (first optimization target)

The first concrete task for the Optimize loop: fix the Noah & Grace
overconfidence. This is already diagnosed (ROADMAP.md top item, SESSION_LOG.md
lines 65–69):

- **Root cause:** Judge treats trust/safety gate as certain rejection (`not_a_match`
  at 0.90) rather than a high-conviction pause.
- **Proposed fix:** Add calibration guidance to the Judge prompt specifically for
  unverified safety gates: "A real but not-yet-verified safety gate is a
  high-conviction PAUSE (lean-no conditional at ~0.6 confidence), not a certain
  rejection, unless the hazard is confirmed or irreversible."
- **Success criterion:** `grace_skeptic` calibration reaches 1.000 (or ≥0.95)
  without any other stance regressing.

This fix will be the **first prior** in `config/priors.json` once it passes the
Success Gate.

---

## 4. What "good" means — acceptance criteria

### 4.1 Quantitative (eval-based)

| Criterion | Threshold | Measured by |
|---|---|---|
| No regression on any stance | `new_hill >= baseline_hill` for all 3 stances | `eval/experiment.py` |
| grace_skeptic calibration | ≥ 0.95 (currently 0.917) | `eval/scorer.py:calibration` |
| All stances binding-hit | = 1.000 (maintained) | `eval/scorer.py:binding_constraint_hit` |
| All stances verdict-match | = 1.000 (maintained) | `eval/scorer.py:verdict_band_match` |
| Diagnose script runs cleanly | exits 0, produces valid `diagnosis.json` | `eval/diagnose.py` |
| Optimize script respects Success Gate | rejected fixes are not applied | `eval/optimize.py` |
| Priors file is valid JSON | parseable, each entry has required fields | schema validation |

### 4.2 Qualitative (design-based)

| Criterion | How to verify |
|---|---|
| Optimizer never modifies the eval | `eval/scorer.py` and `eval/labels.json` are unchanged in any optimization commit |
| Priors are traceable | every entry in `config/priors.json` has a `source` field linking to a diagnosis |
| Self-learning is safe | no prior is derived from unvalidated verdicts (only from eval-confirmed patterns) |
| The loop is auditable | every Diagnose and Optimize run produces a timestamped report in `logs/` |
| Human can override | `config/priors.json` is human-editable; any prior can be deleted |

### 4.3 Properties of the eval (from the framework)

The existing eval (`eval/scorer.py`) already satisfies:

- **Falsifiable:** a wrong verdict scores 0 on `verdict_band`.
- **Reproducible:** deterministic components (groundedness, binding-hit, verdict-band, calibration); only `anti_groupthink` has slight variance.
- **Valid:** passing correlates with correct matchmaking (anchored to human labels).
- **Actionable:** a failure on `calibration` tells you "overconfident"; a failure on `binding_constraint` tells you "named the wrong reason."

---

## 5. Architecture (new files)

```
matchmaker-council/
├── eval/
│   ├── diagnose.py          # NEW: cluster failures, categorize root causes
│   ├── optimize.py          # NEW: propose fixes, apply, re-eval, Success Gate
│   ├── diagnosis.json       # NEW: output of diagnose.py (gitignored, regenerated)
│   ├── optimization_report.md  # NEW: output of optimize.py
│   ├── scorer.py            # UNCHANGED (the measuring stick)
│   ├── labels.json          # UNCHANGED (human ground truth)
│   └── experiment.py        # UNCHANGED (the eval runner)
├── config/
│   ├── settings.py          # minor: add PRIORS_FILE path
│   └── priors.json          # NEW: validated cross-run learnings
├── core/
│   └── judge.py             # MODIFIED: reads priors.json before opining
└── docs/v2/
    ├── SPEC.md              # THIS FILE
    └── agentic-ai-engineer-framework.md  # reference
```

---

## 6. Constraints and non-goals

- **No changes to the deliberation loop itself** (council, agents, critic, hill).
  v2 is about the *meta-loop* (diagnose/optimize), not the inner loop.
- **No real user data.** All pairs remain synthetic/labeled.
- **No UI.** v2 is CLI-only (scripts you run from the terminal).
- **No autonomous deployment.** The Optimize script proposes and gates, but a
  human reviews the commit before pushing to `master`.
- **The eval is sacred.** `eval/scorer.py` and `eval/labels.json` are only
  modified by the human, never by the Optimizer.

---

## 7. Sequencing (build order)

1. **Fix the known residual** (Noah & Grace calibration) — this is the first
   concrete optimization, done manually to establish the pattern.
2. **Build `eval/diagnose.py`** — automate the clustering/categorization.
3. **Build `config/priors.json` + Judge reads it** — the self-learning mechanism.
4. **Build `eval/optimize.py`** — automate fix proposal + Success Gate.
5. **Run the full loop** once end-to-end: diagnose → optimize → re-eval → confirm
   improvement.
6. **Commit and document** — update ROADMAP.md, SESSION_LOG.md, learning notes.

---

## 8. Success definition (when is v2 "done"?)

v2 is complete when:

1. `eval/diagnose.py` can be run on any experiment output and produces a valid
   `diagnosis.json` with ranked clusters.
2. `eval/optimize.py` can propose at least one fix, gate it against the eval,
   and either accept or reject it correctly.
3. `config/priors.json` contains at least one validated prior (the Noah & Grace
   fix) that demonstrably improves `grace_skeptic` calibration.
4. The full Diagnose → Optimize → Evaluate loop runs end-to-end without manual
   intervention (except the final human review of the commit).
5. No eval regression: all stances maintain or improve their baseline hills.
