# 08 — Adversarial Eval Design: Red-Teaming Your Own System

**Concept:** An eval is only as discriminating as its hardest case. Once a system
aces the test, the test is no longer useful — you must generate *harder* cases
that target the system's structural weaknesses. This is red-teaming applied to
evaluation.

---

## The problem: a perfect score that hides fragility

Before this session, the system scored **1.000** on binding-constraint hit,
calibration, and verdict-match across all 6 labeled pairs and 3 stances (18 runs).
That sounds great — but it means the eval has **zero remaining discriminative
power**. A system that's slightly better and one that's slightly worse both score
1.000. The measuring stick has maxed out.

The fix: **generate pairs designed to break the system**, targeting its known
structural weaknesses. If the system still scores 1.000, it's genuinely robust.
If it drops, you've found the real boundary of competence.

---

## Five adversarial strategies

Each strategy targets a different eval component or architectural weakness:

| # | Strategy | Targets | Mechanism |
|---|---|---|---|
| 1 | Decoy Dealbreaker | binding_constraint_hit | Obvious surface tension hides the real binding axis |
| 2 | False Match | verdict_band | Looks perfect on paper; subtle poison pill buried in behavioral evidence |
| 3 | Confidence Trap | calibration | Genuinely ambiguous situation written in decisive language |
| 4 | Inverted Skeptic | verdict_band | Real safety concern buried under overwhelmingly positive signals |
| 5 | Binding Constraint Swap | binding_constraint_hit | Loud obvious axis is NOT the real binding one |

### Why Strategy 5 is structurally hardest for this system

The council has 7 specialized agents, each owning one lens. Each agent scores
*its own axis* and argues for its importance. The vulnerability: **each agent can
only see its own axis clearly.** When there's a *visible* tension on axis A (faith)
and a *subtle* tension on axis B (geography/logistics), the agent responsible for
axis A will shout loudly while axis B's agent might not notice the buried signal.

The Judge reads the final debate and hears the loud agent. The quiet binding
constraint falls through the cracks — not because any single component failed,
but because the *architecture* (decomposition into specialized lenses) creates
blind spots for cross-axis, subtle signals.

---

## The generator: `eval/generate_adversarial.py`

```bash
PYTHONPATH=. python3 eval/generate_adversarial.py --strategies 1,2,3,4,5 --count 5
```

Uses `gpt-5` (flagship) with structured output to generate:
- Full profile JSON matching the `pair_XX.json` schema
- Label JSON with `binding_constraint`, `verdict_band`, `confidence_band`
- `label_logic`: a written argument for WHY the label is correct

### The "who labels the labels" problem

When generating adversarial pairs, you also generate their labels. Quality control:

1. **Human sign-off** — read the `label_logic`, ask "do I agree?"
2. **Forced reasoning** — the generator must produce an argument, not just a label
3. **Cross-validation by disagreement** — run the council on the pair; if it
   *agrees* with your label, the pair might be too easy; if it *disagrees*, either
   the pair is adversarial (good!) or the label is wrong (revise)

---

## Empirical results: the expanded eval

### Before (6 pairs, 18 runs):

| Metric | Score |
|---|---|
| Binding-constraint hit | 1.000 |
| Calibration | 1.000 |
| Verdict-band match | 1.000 |

### After (11 pairs, 33 runs):

| Metric | Original pairs (01–06) | Adversarial pairs (07–11) | Drop |
|---|---|---|---|
| Binding-constraint hit | 1.000 | ~0.45 | **-0.55** |
| Calibration | 1.000 | ~0.93 | -0.07 |
| Verdict-band match | 1.000 | 1.000 | 0 |

### Per-pair adversarial results (grace_skeptic stance):

| Pair | Strategy | Binding | Calib | Verdict | Failure mode |
|---|---|---|---|---|---|
| 07 Priya & Mateo | Decoy Dealbreaker | 0.00 | 0.90 | 1.00 | Named the decoy (distance/age), not the real constraint |
| 08 Tunde & Sofia | False Match | 0.31 | 1.00 | 1.00 | Missed performative growth keywords |
| 09 Aisha & Danny | Confidence Trap | 1.00 | 0.97 | 1.00 | Slightly overconfident (0.55 vs ceiling 0.54) |
| 10 Daniel & Priya | Inverted Skeptic | 0.36 | 1.00 | 1.00 | Partially missed controlling behavior |
| 11 Maya & Daniel | Binding Swap | 0.83 | 0.88 | 1.00 | Sometimes named faith instead of geography |

---

## Key insights

### 1. Verdicts are robust; reasoning is fragile

The system gets the *verdict* right (correct band) 100% of the time — even on
adversarial cases. But it **names the wrong reason** on subtle cases. This means:
- The multi-agent debate is good at reaching the right *conclusion*
- But the *explanation* (which axis is binding) is unreliable on hard cases
- For a matchmaker, this matters: telling someone "it won't work because of your
  faith difference" when the real issue is communication patterns is *harmful*

### 2. The measuring stick got taller

The original eval said "perfect." The expanded eval says "good at verdicts, weak
at reasoning on subtle cases, slightly overconfident on ambiguous ones." That's
a much more useful diagnostic — it tells you exactly *what to fix next*.

### 3. Adversarial generation is a force multiplier for the self-improvement loop

The Diagnose → Optimize loop (`eval/loop.py`) now has real failures to work with.
Before, the only diagnosed cluster was "groundedness" (a methodology issue). Now
there are concrete, fixable failures: the system needs better cross-axis reasoning
and better skeptic activation on buried safety signals.

---

## What to fix next (diagnosed from these results)

1. **Cross-axis binding detection** — the Judge (or a new meta-agent) needs to
   consider whether the *quiet* axis might be more binding than the *loud* one
2. **Skeptic sensitivity** — the RealityCheck agent needs to be more sensitive to
   behavioral patterns of control/withdrawal, even when surface signals are positive
3. **Keyword coverage** — the binding_constraint_keywords in adversarial labels use
   phrases the system doesn't naturally produce (e.g., "performative growth",
   "over-structuring"). Consider semantic matching instead of exact keyword hit.

---

## Code references

| File | What it does |
|---|---|
| `eval/generate_adversarial.py` | The adversarial pair generator (5 strategies) |
| `eval/adversarial_labels.json` | Proposed labels before human sign-off |
| `eval/labels.json` | Official labels (now 11 pairs, human-signed) |
| `profiles/pair_07.json` – `pair_11.json` | The adversarial profiles |
| `logs/experiment_20260724_154445/report.md` | Full results on expanded set |

---

## The meta-lesson

> **An eval that says "perfect" is not a good eval — it's a finished eval.**
> The job of red-teaming is to make the eval *discriminating* again, so the
> self-improvement loop has real failures to diagnose and fix.

This connects back to note 02 (the "tall hill" problem): the original 6-pair
eval was a short measuring stick that saturated. The adversarial pairs made it
taller. The system's *real* competence boundary is now visible — and that's
exactly where improvement happens.
