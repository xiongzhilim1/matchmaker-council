# 01 — Loop Engineering & the Spine (Concept Learning, Track B)

> Running example: **our own codebase** (`matchmaker-council`). Every claim below
> is anchored to exact files and lines so you can re-derive it.
>
> This note is the *first* in a thread that builds toward **LLM-as-judge evals**
> (loop engineering → self-healing → self-correction → hill-climbing → why
> LLM-as-judge saturates → the objective eval that replaced it). It is captured
> as we learn, Socratically. Status: **loop engineering done; the "tall hill"
> trap and `eval/scorer.py` are next.**

---

## 0. The spine in one sentence

**Per round:** N agents each run **once**, **sequentially**, each seeing only the
*previous* round's debate summary → a **critic** fact-checks each agent's claim
against the profile and forces at most one revision per flagged agent → an LLM
**referee** rates the round's groundedness & engagement, blended into one **hill**
score → a **stop-check** decides whether to loop again. **After the loop exits,**
the **Judge** reads only the final round's positions (plus the hill history) and
opines **once**.

Two diagrams capture this:

- `assets/spine_sequence.png` — full sequence of one deliberation.
- `assets/stopping_rule.png` — the four-gate stopping decision tree.

### Map of the spine (file → role)

| Stage | File / line | Role |
|---|---|---|
| Entrypoint | `run.py:24-57` | loads a pair, wires Council + critic + Judge, runs once |
| Orchestrator loop | `core/council.py:57-113` (`deliberate`) | the rounds loop |
| One agent turn | `agents/agent.py:61-99` (`assess`) | score + position + reaction; emits `down=True` on failure |
| Critic pass | `core/critic.py:37-62` | per-turn grounding check + one forced revision |
| Hill score | `core/hill.py:55-67` (`hill_score`) + `:42-52` (`referee_quality`) | quality of the round |
| Stop rule | `core/council.py:115-127` (`_should_stop`) | loop engineering |
| Judge | `core/judge.py:50-93` | final verdict, **once**, after the loop |
| LLM seam | `core/llm.py:55-103` | every model call; retries + JSON repair |
| Knobs | `config/settings.py:40-43` | `MAX_ROUNDS=4`, `MIN_ROUNDS=2`, `CONVERGENCE_DELTA=0.05`, `SCORE_SPREAD_STOP=0.12` |
| Audit log | `core/logbook.py:56-96` | makes every event inspectable |

---

## 1. The debate is **across** rounds, not within them (lag-1 propagation)

Within a single round, agents are **isolated**: each call is
`agent.assess(profiles_json, prev_summary, round_idx=r)` (`core/council.py:65`),
and `prev_summary` was computed at the **end of round r−1**
(`core/council.py:111`). Agent 4 in round *r* does **not** see what agents 1–3
just said in round *r*.

So where is the "debate"? It's a **one-round-delayed feedback loop**:

```
Round 1:  A1 A2 ... AN   (all see "" — cold, no prior debate; reaction = "")
              |  end of round 1: _debate_summary(turns) -> prev_summary
              v
Round 2:  A1 A2 ... AN   (all see round-1's summary; each REACTS to it)
              |  end of round 2: new summary
              v
Round 3:  ...
```

- The reaction is a real field, not a vibe: `Turn.reaction` (`agents/agent.py:28`),
  requested explicitly in the prompt (`agents/agent.py:43`:
  *"reaction: `<=50 words reacting to other agents' last-round points; '' in round 1`"*).
- The only cross-round memory is the summary string built by `_debate_summary`
  (`core/council.py:43-49`): **one line per live agent**, format
  `- {agent} (score {score:.2f}): {position}`. No scratchpad, no full transcript.
  It carries `position` only (drops `reaction`), and drops any `down` agent.

**Critique worth keeping:** because reactions lag by a round, the final round's
agents react to the *second-to-last* round, and then the Judge reads the final
round. So the final positions incorporate one fewer "reply" than it looks. A
tighter design might add an intra-round second pass; the author traded that for
legibility ("naked machinery").

### Why this still yields a meaningful hill

Both hill inputs are observable *across* the round without live chat:
- `engaged` rises because the referee reads each agent's `reaction` text
  (passed via `_round_text`, `core/council.py:51-55,96`). Round 1 reactions are
  empty → low engagement; round 2+ → higher.
- `spread` drops as agents pull toward each other after reading the summary
  (`core/hill.py:27`).

Empirical proof, `logs/run_20260617_015936/hill.csv`:

```
round,hill_score,score_spread
1,0.5989,0.0967      # cold start: low engagement -> lower hill
2,0.9137,0.0557      # agents reacted -> engagement on -> hill leaps +0.31
```

This is also *why* `MIN_ROUNDS=2` exists: with one round there is **by
construction** no reaction and no debate to score.

---

## 2. What the Judge reads, precisely

`deliberate()` returns `_final_state()` (`core/council.py:129-138`). The Judge
(`core/judge.py:50`) consumes exactly two fields:

- **`final_turns`** — the **last round's positions only** (`core/council.py:130`,
  `last = self.history[-1]`). Rendered into `council_view` at
  `core/judge.py:52-55` using `position` (**not** `reaction`).
- **`hill_history`** — passed as *flavor context* only (`core/judge.py:62`:
  *"Debate quality climbed across rounds (hill scores): [...]"*).

It does **not** read: the full multi-round transcript, the critic events, the
spread history, or the logs. It then applies its weighing rules
(`JUDGE_SYSTEM`, `core/judge.py:21-47`) — character-as-multiplier, honor
**declared** dealbreakers, grace-vs-skeptic — and emits one JSON verdict
(`decision`, `confidence`, `headline`, `rationale`, `open_tensions`).

**Sharp implication:** a brilliant point raised in round 2 but softened away by
the final round is **invisible to the Judge**. The loop's job is to make the
*final snapshot* as grounded and resolved as possible.

---

## 3. The hill score formula, and why it is "meaningful"

`core/hill.py:55-67`:

```python
resolution      = 1.0 - min(spread / 0.4, 1.0)   # agreement, normalized
resolution_term = resolution * engaged            # agreement GATED by engagement
h = 0.45*grounded + 0.30*engaged + 0.25*resolution_term
```

- **`grounded` (0.45)** — claims tied to profile facts? Biggest weight because
  the worst failure is *invention/hallucination*.
- **`engaged` (0.30)** — agents reacting to each other vs parallel monologue.
  This is what makes the hill *climb* (≈0 on the cold first pass, rises after).
- **gate `resolution * engaged` (0.25)** — agreement counts as quality **only if
  earned by engagement.** Same final agreement, very different credit:

| Scenario | spread | resolution | engaged | resolution_term |
|---|---|---|---|---|
| Earned consensus | 0.05 | ~0.88 | 0.9 | **0.79** |
| Lazy groupthink | 0.05 | ~0.88 | 0.1 | **0.09** |

`grounded` and `engaged` both come from an **LLM referee** (`core/hill.py:42-52`,
prompt at `:34-39`). **This is the crack:** the hill's *structure* is sound, but
its *sensor is a model grading a model* — the thing that saturates in Part 4.

---

## 4. Loop Engineering proper — the four-gate stopping rule

`core/council.py:115-127`:

```python
def _should_stop(self, r, spread):
    if r < settings.MIN_ROUNDS:           return False, "below MIN_ROUNDS"        # (1) floor
    if spread < settings.SCORE_SPREAD_STOP: return True, "agents converged ..."    # (2) converged
    if len(self.hill_history) >= 2:
        gain = self.hill_history[-1] - self.hill_history[-2]
        if gain < settings.CONVERGENCE_DELTA: return True, "hill plateaued ..."    # (3) plateaued
    if r >= settings.MAX_ROUNDS:          return True, "reached MAX_ROUNDS"        # (4) ceiling
    return False, ""
```

### Why not fewer gates?

- **Ceiling only** (the common naive loop): wastes rounds when already resolved,
  and can cause drift/overconfidence with no quality gain.
- **"Stop when they agree" only:** rewards *premature/lazy convergence* — round-1
  agreement bought without a real debate. Gate (1) `MIN_ROUNDS` exists precisely
  to **veto** early stops before a real exchange has happened.

### The subtle insight — two *different* stop signals

| Gate | Signal | Source | Question |
|---|---|---|---|
| (2) converged | `spread` = stdev of agent **scores** | `core/hill.py:27` | Do the agents **agree**? |
| (3) plateaued | round-over-round Δ of the **hill** | `core/council.py:120-124` | Is **judgment quality** still improving? |

They can disagree, and that's the point:
- **Agree-axis open but quality climbing:** spread still high (gate 2 fails) but
  hill jumped 0.60→0.91 → keep going.
- **Quality flat, disagreement persists:** gate (3) fires — *"more rounds won't
  improve judgment quality"* — and hands the Judge an **explicitly unresolved**
  debate (the post's "resolved-OR-honestly-unresolved", `core/hill.py:12-14`).

**One-liner:** *`spread` measures agreement (an input to stopping); the hill
measures quality (the thing you're climbing). You need both, a floor so you never
trust round-1 agreement, and a ceiling so a pathological case can't run forever.*

### Q4 — why the ceiling is checked **last**

The `range(1, MAX_ROUNDS+1)` (`core/council.py:59`) is the *structural* ceiling;
the `r >= MAX_ROUNDS` check inside `_should_stop` is *semantic* — it only exists
to emit the right **reason string** for the audit log. The gates are a **priority
list of explanations**. On the final round, converged/plateaued may *also* be
true. Checking the ceiling first would mislabel a genuinely-resolved round 4 as
`"reached MAX_ROUNDS"` (looks like a budget timeout). Checking it last means that
reason appears **only** when the debate neither converged nor plateaued — a real
signal that *this pair was hard and the loop wanted more rounds.* Ordering encodes
a **diagnostic preference**: informative reason over fallback reason.

### Q5 — a stopping rule is only as good as the metric it watches

The plateau gate trusts the **hill delta**. But the referee saturates: the post's
real run moved `0.788 → 0.801` (Δ=0.013) — well under `CONVERGENCE_DELTA=0.05`,
so **gate (3) fires on round 2 for essentially every pair.**

- *Looks like a feature:* "plateaued → stop early, save tokens."
- *Actually a bug:* the hill is flat **because the sensor is too short to detect
  improvement,** not because quality stopped improving. A saturated sensor reads
  "flat" for easy and hard cases alike, so the loop stops early at mediocrity
  while *believing* it made a quality-based decision.

This is the post's lesson verbatim (`docs/post_final.md:43`): *"our measuring
stick was too short... a confident, grounded, but ultimately wrong answer scores
highly."* **Diagnostic recipe (the real fix):** go to the trace, see the hill
barely moved, distrust the referee, and **replace the sensor** with an objective,
human-labeled hill (`eval/scorer.py`) that cannot saturate for free.

> **Bridge to the next note:** loop engineering and eval quality are *not*
> separate topics. The loop's intelligence is bounded by the eval's resolution.
> Tie a good stopping rule to a saturating metric → an efficient loop that
> confidently stops at mediocrity. Next: the "tall hill" trap and the objective
> scorer.

---

## Exact-reference cheat sheet (for fast recall)

| Concept | Where to look |
|---|---|
| Rounds loop | `core/council.py:57-113` |
| Sequential agents, once each | `core/council.py:64-72` |
| Cross-round memory (`prev_summary`) | `core/council.py:43-49`, set at `:111` |
| `reaction` field & prompt | `agents/agent.py:28`, `:43` |
| Hill formula | `core/hill.py:55-67` |
| LLM referee (the saturating sensor) | `core/hill.py:42-52`, prompt `:34-39` |
| Four-gate stop rule | `core/council.py:115-127` |
| Loop knobs | `config/settings.py:40-43` |
| Judge reads final positions only, once | `core/judge.py:50-63`, called at `run.py:41` |
| Empirical hill climb | `logs/run_20260617_015936/hill.csv` |
| The "tall hill" lesson (prose) | `docs/post_final.md:39-50` |

## Open threads (to cover next)
- [ ] **Self-healing**: `core/llm.py:55-103` (retries + JSON repair + `LLMDown`),
  surfaced at `core/council.py:67,75-78` and `core/judge.py:64-79`; demo fault
  injection `core/faults.py`; live artifact `logs/run_20260617_015936/transcript.md:19,48`.
- [ ] **Self-correction**: `core/critic.py` end-to-end; runnable demo
  `tests/test_self_correction.py`; artifact `logs/test_self_correction/transcript.md`.
- [ ] **The objective hill / LLM-as-judge saturation**: `eval/scorer.py` (5
  components), `eval/labels.json` (human ground truth), `eval/experiment.py` (A/B/C).
