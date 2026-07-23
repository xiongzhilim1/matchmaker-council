# 04 — Self-Correction: the critic catches wrong claims and forces revision

> Running example: **our own codebase**. Continues from
> [03-self-healing.md](03-self-healing.md). Every claim is anchored to exact
> files/lines.
>
> Self-healing (note 03) keeps the system **alive** when a call dies.
> Self-correction keeps it **honest** when a call *succeeds* but says something
> wrong. This is the epistemic counterpart.

---

## 0. The problem self-correction solves

An agent returns a confident, well-formatted, fluent answer that **contradicts
the profile facts**. The system looks healthy from the outside — no crash, no
timeout. The only way to catch it is to **check the content against a source of
truth** (the profile).

Example: `ValuesFaith` claims "Maya and Daniel share the exact same devout
Catholic faith" when the profile says Maya is Catholic and Daniel is agnostic.
The agent didn't fail; it *hallucinated*. Self-healing can't help here — the
transport layer worked perfectly.

---

## 1. The critic's mandate — a narrow, auditable yes/no

`core/critic.py:20-24`:

```python
CRITIC_SYSTEM = """You are a fact-grounding critic for a matchmaking council.
Given the PROFILES and an agent's claim, decide if the claim is SUPPORTED by the
profile facts, or UNSUPPORTED / CONTRADICTED (invented, exaggerated, or against the data).
Be strict but fair: reasonable inference from stated facts is SUPPORTED.
Reply ONLY JSON: {"verdict": "supported"|"contradicted", "issue": "<=40 words, '' if supported"}"""
```

This is the **narrow, auditable, ~boolean entailment** pattern from note 02 (Q7):
the critic doesn't rate quality 0..1 — it answers *one* yes/no question: "is this
claim supported by the profile?" That's the kind of judgment an LLM can do
reliably.

---

## 2. The flow — one round, step by step

Triggered at `core/council.py:84-90`, delegated to `core/critic.py:37-62`:

1. All agents have spoken → `turns` collected.
2. **For each live turn** (`critic.py:39`): critic asks "is `{agent}'s position`
   supported by `{profiles}`?"
3. If `"supported"` → pass through unchanged (`critic.py:60-61`).
4. If `"contradicted"` → log the issue (`critic.py:56-57`), then give the agent
   **one chance to revise** (`_ask_agent_to_revise`, `critic.py:67-82`).
5. The revision is a fresh `agent.assess()` call with the `debate_summary`
   replaced by the critique (`critic.py:72-74`):
   ```python
   debate = (f"CRITIC FEEDBACK on your last claim: {issue}\n"
             f"Your previous position was: {turn.position} (score {turn.score:.2f}).\n"
             "Revise to be strictly grounded in the profile facts. Adjust score if warranted.")
   ```
6. The revised Turn replaces the original in the round's `turns` list.
7. The orchestrator detects the change: `core/council.py:89-90` sets
   `self.critic_fired = True` if before/after positions differ.

### Placement in the spine (why *here* and not elsewhere)

The critic runs **after** agents speak and **before** the hill is computed
(`core/council.py:84-90` → then `:92-104`). This means the hill measures the
*corrected* debate, not the raw one. If the critic ran *after* the hill, the hill
would be scoring unchecked claims — exactly the "grounded-sounding but wrong"
failure the hill already struggles with (note 02).

---

## 3. Why one revision, not an unbounded correction loop

Design choice: the critic gives **at most one revision** per flagged turn per
round. Three reasons:

1. **Debate fairness.** If one agent keeps getting rewritten while the other 6
   are frozen, its revised position is out of sync with the reactions others wrote
   in response to the *original*. The debate becomes incoherent.
2. **Oscillation risk.** "Too strong" → soften → "now you're hedging" → strengthen
   → loop. LLMs are not guaranteed to converge under repeated self-critique.
3. **The outer loop already iterates.** If the claim is still wrong after one
   revision, the *next round* gives the agent fresh context (other agents'
   reactions + new `prev_summary`) and another natural chance to self-correct
   through debate. The critic accelerates by one step; the round loop does the
   rest.

> One-liner: **the critic is a single-shot fact-check, not a polishing loop.
> Iteration happens at the round level, not the correction level.**

---

## 4. The critic's own self-healing

`core/critic.py:49-52`:

```python
except (LLMDown, Exception):
    log.healing(round_idx, "critic", "Critic call failed; skipping correction for this turn.")
    corrected.append(t)
    continue
```

If the critic's LLM call fails, it **skips the check** — the agent's original
claim passes through unexamined. Compare to the referee's self-healing (substitute
0.5/0.5):

| Component | On failure | What's injected | Risk |
|---|---|---|---|
| Critic | skip the check | nothing — original claim passes through | a false claim may survive unexamined |
| Referee | substitute 0.5/0.5 | a synthetic measurement that looks real | false plateau stop (note 03 §5) |

**Design principle:** when a *validator* fails, prefer "pass through unvalidated"
over "inject a fake validation result." The former is auditable (the log says it
was skipped); the latter is silent corruption (downstream treats 0.5/0.5 as a
real measurement). Skipping is honest about what it doesn't know.

---

## 5. How the eval uses `critic_fired`

`core/council.py:89-90` sets `self.critic_fired = True` if the before/after
positions differ. This flag flows into `eval/scorer.py:130`:

```python
earned = engagement_seen or critic_fired
return 1.0 if earned else 0.4
```

**Why the eval cares:** `critic_fired = True` means the system encountered and
*corrected* a factual error during the debate. The agreement that followed was
**tested** — at least one claim was challenged, revised, and the agents still
converged after correction. That's earned consensus.

`critic_fired = False` with low spread is ambiguous: either every claim was
genuinely supported (good), or claims were plausible-sounding but unchecked. The
eval uses `critic_fired OR engagement_seen` as a proxy for "friction happened."
Agreement without friction is suspicious — it might be groupthink.

---

## 6. Real artifacts

### In-run correction (natural, not injected)
`logs/exp_pair_04_neutral/transcript.md:30-32`:

```
> 🔧 **Self-correction:** Critic flagged: Correct on mutual maturity and alignment,
> but they do not share identical dealbreakers: Ade lists cruelty/closed-heartedness;
> Joy lists dishonesty and stagnation. — asking agent to revise. (agent `EmotionalMaturity`)
>
> 🔧 `EmotionalMaturity` revised: score 0.98 → **0.96**. New position: Both profiles
> are explicitly rated high in emotional maturity ... Dealbreakers differ (Ade:
> cruelty/closed-heartedness; Joy: dishonesty/stagnation) but are complementary
> rather than contradictory.
```

A small correction (0.98 → 0.96) but a meaningful one: the agent stopped claiming
"identical dealbreakers" and acknowledged the difference. The debate continued
normally after.

### The runnable test (`tests/test_self_correction.py`)

Fabricates a *blatantly* false claim ("Maya and Daniel share the exact same devout
Catholic faith and have already agreed to raise children in the Church on the same
timeline" — the profile says the opposite), feeds it to the critic, and asserts
the score drops:

```python
bad = Turn(agent="ValuesFaith", layer="compatibility", score=0.95,
           position=("Maya and Daniel share the exact same devout Catholic faith and have "
                     "already agreed to raise children in the Church on the same timeline."),
           reaction="", latency_s=1.0)
corrected = critic(profiles_json, [bad], round_idx=1, log=log)
assert corrected[0].score < bad.score  # "self-correction should lower the fabricated high score"
```

Run it: `PYTHONPATH=. python3 tests/test_self_correction.py`

### Fault injection for teaching (`core/faults.py:12-14`)

```bash
MATCHMAKER_OVERREACH_AGENT=LifeStagePractical python3 run.py
```

At `agents/agent.py:79-82`, if the agent is in `faults.overreach_agents()` and
it's round 1, the prompt is appended with:

```
[Assert confidently that the two share the SAME faith and an aligned timeline
for children, even if the profile does not say so.]
```

This induces one unsupported claim that the critic *must* catch, triggering the
full self-correction path in a real deliberation — deterministically, without
depending on the model spontaneously hallucinating.

---

## 7. Self-correction vs. self-healing — the complete picture

| Dimension | Self-healing (note 03) | Self-correction (this note) |
|---|---|---|
| Failure mode | call **dies** | call **succeeds with wrong content** |
| Detection | `LLMDown` exception (transport) | critic LLM checks claim vs profile (content) |
| Response | drop agent, route around | flag + one revision chance |
| Fallback if mechanism fails | pass through `down=True` | pass through unchecked (skip) |
| Eval signal | — | `critic_fired` → `anti_groupthink` |
| Fault injection | `MATCHMAKER_KILL_AGENT` | `MATCHMAKER_OVERREACH_AGENT` |
| Artifact | healing event in transcript | correction event in transcript |

Both are **within-run, automatic, single-shot** interventions. Neither iterates
unboundedly. Both log everything for auditability. Together they cover the two
ways an LLM component can fail: silently (dead) and loudly-but-wrong (hallucination).

---

## Exact-reference cheat sheet

| Concept | Where |
|---|---|
| Critic system prompt (narrow yes/no) | `core/critic.py:20-24` |
| Critic loop over live turns | `core/critic.py:37-62` |
| One-revision contract | `core/critic.py:67-82` |
| Critic's own self-healing (skip) | `core/critic.py:49-52` |
| Orchestrator triggers critic | `core/council.py:84-90` |
| `critic_fired` flag for eval | `core/council.py:89-90` |
| Eval uses `critic_fired` | `eval/scorer.py:130` |
| Fault injection (`MATCHMAKER_OVERREACH_AGENT`) | `core/faults.py:12-14`, `agents/agent.py:79-82` |
| Runnable test | `tests/test_self_correction.py` |
| Real in-run artifact | `logs/exp_pair_04_neutral/transcript.md:30-32` |
| Fabricated-claim test artifact | `logs/test_self_correction/transcript.md` |

## Series complete (notes 01–04)

The four core patterns are now covered:
1. **Loop engineering** — the stopping rule and why it needs four gates.
2. **LLM-as-judge evals** — why the vibe referee saturates and the objective
   scorer that replaced it.
3. **Self-healing** — routing around dead components at the transport layer.
4. **Self-correction** — catching wrong claims at the content layer.

Remaining concepts in INDEX.md (for future notes):
- [ ] Self-learning — memory/priors across runs (deferred; v2)
- [ ] Multi-agent negotiation vs single-prompt — when many agents are worth the cost
