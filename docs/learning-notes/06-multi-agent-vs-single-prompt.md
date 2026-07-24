# 06 — Multi-Agent Negotiation vs Single-Prompt: when is the overhead worth it?

> Running example: **our own codebase**. Concludes the Concept Learning track
> (notes 01–06). This note addresses the meta-design question: why use 7 agents
> debating across rounds instead of one big prompt?

---

## 0. The alternative that didn't get built

A single-prompt matchmaker would look like this:

```
You are a matchmaking advisor. Given two profiles, consider these dimensions:
- Values/faith alignment
- Attraction/spark
- Life-stage/practical fit
- Emotional pattern fit
- Emotional maturity
- Willingness to grow
- Reality check (dealbreakers)

Weigh them holistically. Return a verdict (match / conditional_yes / not_a_match),
confidence (0..1), headline, and rationale.
```

One call. One model. ~2 seconds. ~$0.01. No loop, no hill, no critic, no
self-healing.

The matchmaker-council uses 7 agents × 2–4 rounds + critic + referee + judge =
**20–40 LLM calls per pair**. That's 10–20x the cost and latency.

---

## 1. Three structural advantages of multi-agent (not just "more complex")

### 1a. Decomposition with accountability

Each agent owns *one* lens and is scored on *that lens alone*. When `ValuesFaith`
says 0.15, you know exactly which dimension is failing and why. A single prompt
gives you one blended number — if it's wrong, you can't tell *which dimension*
caused the error.

The eval's `binding_constraint` component (`eval/scorer.py:76-90`) works precisely
because the agents *separately name* which axis matters most. A single prompt
buries that signal in prose.

### 1b. Adversarial pressure that survives across rounds

In round 1, `AttractionSpark` says 0.82 and `ValuesFaith` says 0.15. In round 2,
each *reacts* to the other. The tension is **structural** — two separate
optimization targets pulling against each other.

A single prompt told "consider both attraction and values" will typically *resolve
the tension internally* in one pass, often by defaulting to the middle. The
multi-agent system *preserves* the tension across rounds and forces it to be
resolved *explicitly* (which is what the Judge reads).

### 1c. The critic has something to check

Self-correction (`core/critic.py`) works because each agent makes a *specific,
isolated claim* that can be fact-checked against the profile. A single prompt's
holistic paragraph is much harder to fact-check — which sentence is the claim?
Which part is grounded vs invented? Decomposition makes the critic's job tractable.

---

## 2. Which eval components break on single-prompt?

| Eval component | Multi-agent | Single-prompt |
|---|---|---|
| `groundedness` (0.20) | works — check each agent's claim | works (harder to isolate) |
| `binding_constraint` (0.30) | works — agents name axes separately | partially works (buried in prose) |
| `verdict_band` (0.20) | works | works |
| `calibration` (0.20) | works | works |
| `anti_groupthink` (0.10) | works — `engagement_seen OR critic_fired` | **meaningless** — no disagreement possible |

`anti_groupthink` (`eval/scorer.py:122-131`) measures whether agreement was
*earned* through debate and correction. With a single voice, there is no
disagreement, no debate, no correction — the concept doesn't apply. You'd lose
10% of scoring resolution and, more importantly, lose the ability to distinguish
"genuinely considered" from "defaulted to the middle."

---

## 3. The Skeptic argument — why a separate agent differs from a prompt line

**"Also consider reasons this won't work"** (prompt instruction) vs. **a Skeptic
agent with its own charter, score, and persistence across rounds** (structural).

The differences are mechanical, not philosophical:

| Property | Prompt instruction | Separate Skeptic agent |
|---|---|---|
| Has its own score (enters spread math) | No | Yes — pulls spread up, delays convergence |
| Persists across rounds | No — one completion | Yes — reacts in round 2, 3, ... |
| Influences stopping rule | No | Yes — gate (2) won't fire while Skeptic disagrees |
| Subordinate to the "for" argument? | Yes — same context, same completion | No — separate call, separate optimization |
| Observable in eval | No | Yes — `engagement_seen`, spread history |

**Empirical evidence:** in the experiment results, `grace_skeptic` (with a Skeptic)
produced lower confidence and more accurate calibration than `grace` (without).
The Skeptic didn't add a caveat — it *structurally pulled the council's confidence
down* on ambiguous pairs, which is exactly what the calibration component rewards.

> One-liner: **a separate agent is a separate optimization target with its own
> score, its own persistence, and structural influence on the stopping rule. A
> prompt instruction is advisory text with no guaranteed weight.**

---

## 4. When single-prompt IS sufficient

The multi-agent overhead is NOT worth it when:

1. **The decision is simple/binary with one dominant axis** — no tension to
   preserve (e.g., "is this email spam?").
2. **You don't need to debug which dimension failed** — no eval decomposition
   needed (e.g., creative generation where "good" is holistic).
3. **Latency/cost matters more than accuracy** — real-time chat vs. offline
   assessment.
4. **The domain doesn't have checkable facts** — the critic has nothing to
   fact-check (e.g., poetry generation).

The matchmaker-council is a case where all four conditions for multi-agent hold:
complex (7 dimensions), needs debugging (the eval decomposes), offline (latency
acceptable), and fact-checkable (profiles are ground truth).

---

## 5. The cost-benefit summary

| Metric | Single-prompt | Multi-agent council |
|---|---|---|
| LLM calls per pair | 1 | 20–40 |
| Cost per pair | ~$0.01 | ~$0.10–0.20 |
| Latency | ~2s | ~30–60s |
| Decomposed diagnosis | No | Yes (which agent/dimension failed) |
| Adversarial pressure | No (advisory) | Yes (structural, persistent) |
| Self-correction possible | Difficult (holistic prose) | Yes (isolated claims) |
| Eval resolution | 4 components (lose anti_groupthink) | 5 components |
| Calibration accuracy | Lower (no structural skepticism) | Higher (Skeptic pulls confidence) |

The 10–20x cost buys you: traceability, adversarial robustness, self-correction,
and higher eval resolution. Whether that's worth it depends on the stakes of the
decision and whether you need to *debug and improve* the system over time (which
is exactly what the v2 Diagnose/Optimize loop requires).

---

## Exact-reference cheat sheet

| Concept | Where |
|---|---|
| 7 agents, sequential, one lens each | `core/council.py:64`, `agents/personas.py` |
| Skeptic charter | `agents/personas.py` (Skeptic persona) |
| Spread prevents premature convergence | `core/council.py:118-119`, `core/hill.py:27` |
| Critic needs isolated claims | `core/critic.py:46-47` |
| `anti_groupthink` eval component | `eval/scorer.py:122-131` |
| `engagement_seen` flag | `core/council.py:81-82` |
| Experiment stances (neutral/grace/grace_skeptic) | `eval/experiment.py` |
| Empirical calibration improvement | `logs/experiment_20260617_151646/report.md` |

---

## Series complete

All seven concepts from INDEX.md are now covered:

| # | Note | Concept |
|---|---|---|
| 01 | Loop Engineering & the Spine | The stopping rule and why it needs four gates |
| 02 | LLM-as-Judge Evals | Why the vibe referee saturates; the objective scorer |
| 03 | Self-Healing | Routing around dead components at the transport layer |
| 04 | Self-Correction | Catching wrong claims at the content layer |
| 05 | Self-Learning | Cross-run memory design (v2 target) |
| 06 | Multi-Agent vs Single-Prompt | When the multi-agent overhead is worth it |

Next: **v2 spec** (Conceptualize phase of the Agentic AI Engineer framework).
