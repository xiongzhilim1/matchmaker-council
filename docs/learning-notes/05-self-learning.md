# 05 — Self-Learning: memory and priors across runs

> Running example: **our own codebase**. Continues from
> [04-self-correction.md](04-self-correction.md). This concept is **not yet
> built** — it's the v2 design target. The note captures the reasoning that
> will shape the implementation.
>
> Self-healing (note 03) keeps the system alive. Self-correction (note 04) keeps
> it honest within a run. Self-learning keeps it **improving across runs** — the
> system gets better over time without manual intervention.

---

## 0. The gap in v1

Every deliberation starts cold (`core/council.py:58`, `prev_summary = ""`). The
system has no memory of previous pairs. But the eval results show the *same kind
of mistake* recurring across pairs:

- **Calibration ~0.84** across all stances (the residual bottleneck from note 02)
- **Overconfidence on ambiguous pairs** (pair_01, pair_03)
- **Same binding-constraint miss** on structurally similar faith-gap pairs

The system re-discovers these lessons from scratch every time. Self-learning means
**not having to re-learn what you already proved.**

---

## 1. What to learn from — the safety hierarchy

Not all sources of learning are equally safe. The core danger: if the system
learns from its **own past verdicts** (without external validation), it reinforces
its own biases. A system that was overconfident on pair_01 and "learns" from that
run becomes *more* overconfident on similar pairs.

| Source | What it tells you | Safe to learn from? | Why |
|---|---|---|---|
| **Real-world outcomes** (post-match interviews, actual dates) | "This pair actually worked/didn't" | Safest — ultimate ground truth | Reality cannot be flattered |
| **Eval results** (scorer vs human labels) | "You were wrong on pair_01's binding constraint" | Safe — anchored to human ground truth | External validation |
| **Traces** (events.jsonl, transcript) | "The critic never fired; hill plateaued at round 2" | Safe for *diagnosis* — tells you where to look | Observational, not prescriptive |
| **Own past verdicts** | "Last time I saw a faith gap, I said not_a_match" | **Dangerous** — reinforces bias if wrong | No external check |

**The safe self-learning rule:** learn only from sources that are **validated
against external truth** before they become priors. Traces diagnose; eval results
confirm; only confirmed patterns graduate to memory.

---

## 2. What the "one piece of memory" should be

From the Socratic session (Q14): the single signal that would most improve the
next verdict is **calibration feedback** — "on pairs like this, you tend to be
X% overconfident; cap your confidence at Y."

This is the weakest eval component (~0.84) and the one most amenable to
cross-run learning: calibration is a *systematic* error (not random), so a prior
can correct it without needing to understand the specific pair.

More broadly, three kinds of learnable priors:

1. **Calibration priors**: "on ambiguous pairs (spread > 0.15 after convergence),
   cap confidence at 0.75" — derived from eval results showing overconfidence.
2. **Pattern priors**: "faith_gap + one_agnostic → likely not_a_match (0.85
   probability)" — derived from multiple confirmed eval results on similar pairs.
3. **Process priors**: "when the critic fires on round 1, the final verdict is
   more accurate than when it doesn't" — derived from trace analysis + eval
   correlation.

---

## 3. Where learned priors would live

Three options, escalating in ambition:

### Option A: `config/priors.json` (simplest, v2 MVP)

A human-readable, human-editable file:

```json
[
  {
    "pattern": "faith_gap_one_agnostic",
    "prior": "likely not_a_match",
    "confidence_cap": 0.75,
    "source": "eval on pair_01 + pair_03, confirmed by labels",
    "added": "2026-06-20"
  },
  {
    "pattern": "high_spread_after_convergence",
    "prior": "cap_confidence",
    "confidence_cap": 0.70,
    "source": "calibration analysis across 18 runs",
    "added": "2026-06-20"
  }
]
```

The Judge reads this before opining. Low-tech, auditable, versionable in git.

### Option B: Dynamic eval criteria (medium)

Every diagnosed failure becomes a new row in `eval/labels.json` — a new test case
the system must pass. The eval *grows over time*. This is the video's principle:
"every failure becomes a new eval criterion."

### Option C: Prompt evolution (ambitious, full video loop)

An Optimizer agent reads diagnosed clusters and proposes prompt changes to
agents/critic/judge. The change is tested against the eval; deployed only if the
score improves (Success Gate). The system literally rewrites its own prompts.

---

## 4. The Diagnose → Optimize → Evaluate loop (from the video)

The Agentic AI Engineer framework (source: https://www.youtube.com/watch?v=pSto5YaNGUo)
defines a five-phase continuous loop. Self-learning is the *mechanism* that
connects Phase 4 (Diagnose) → Phase 5 (Optimize) → Phase 3 (Evaluate) in a
closed loop:

```
Run eval across all labeled pairs
         │
         ▼
Cluster failures by component
(binding_constraint=0 on pairs 02,05; calibration<0.8 on pairs 01,03)
         │
         ▼
Categorize root causes from traces
("critic didn't catch wrong axis"; "agents converged without friction")
         │
         ▼
Propose fix (new prior / prompt change / new eval criterion)
         │
         ▼
Re-run eval → score improved? ──yes──▶ deploy (Success Gate)
         │                                    │
         no                                   │
         │                                    ▼
    discard fix                     prior graduates to memory
```

The key safety property: **nothing enters memory without passing the Success
Gate.** A proposed prior that doesn't improve the eval score is discarded. This
prevents the system from learning wrong lessons.

---

## 5. The danger of self-reinforcing bias

The video's "One Rule" for evals: **the agent being tested must never grade
itself.** The same rule applies to self-learning:

- The system must never learn from its own *unvalidated* verdicts.
- The validator must be *external* (human labels, real-world outcomes, or at
  minimum an independent eval that the system cannot game).
- If the only feedback is "I was confident last time," that's not learning —
  that's confirmation bias with extra steps.

**Concrete example of the trap:** the system says `not_a_match` on pair_01 with
confidence 0.92. If it "learns" `{faith_gap → not_a_match, confidence 0.92}` from
its own verdict, next time it sees a faith gap it'll be *even more* confident —
regardless of whether the original verdict was correct. The eval shows it *was*
correct on pair_01, but the confidence was too high (label says 0.75 band). So
the safe learning is: `{faith_gap → not_a_match, confidence_cap 0.75}` — validated
against the label, not the raw verdict.

---

## 6. Connection to the existing codebase

| v1 component | Role in self-learning (v2) |
|---|---|
| `eval/scorer.py` | The validator — confirms which patterns are real |
| `eval/labels.json` | The ground truth — grows as new pairs are labeled |
| `eval/experiment.py` | The runner — produces the data for diagnosis |
| `core/logbook.py` → `events.jsonl` | The trace — raw material for clustering |
| `logs/*/transcript.md` | Human-readable trace for root-cause analysis |
| `config/priors.json` (new, v2) | Where validated learnings live |
| Diagnostics script (new, v2) | Clusters failures, categorizes root causes |
| Optimizer (new, v2) | Proposes fixes, gated by eval improvement |

---

## Exact-reference cheat sheet

| Concept | Where (v1) | Where (v2, planned) |
|---|---|---|
| Cold start (no memory) | `core/council.py:58` | replaced by priors injection |
| Eval results (the validator) | `eval/scorer.py:34-40` | unchanged; the gate |
| Human labels (ground truth) | `eval/labels.json` | grows over time |
| Traces (raw material) | `core/logbook.py` → `events.jsonl` | input to diagnostics |
| Calibration bottleneck | experiment report: ~0.84 | target for first prior |
| Success Gate | not built | `eval/experiment.py` score comparison |

## Open thread (note 06)
- [ ] Multi-agent negotiation vs single-prompt — when is the multi-agent overhead
  worth it? (The structural argument for decomposition, adversarial pressure, and
  the critic having something to check.)
