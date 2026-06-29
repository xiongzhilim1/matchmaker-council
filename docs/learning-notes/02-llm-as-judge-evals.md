# 02 — LLM-as-Judge Evals: why the vibe hill saturates, and the objective scorer that replaced it

> Running example: **our own codebase**. Continues the thread from
> [01-loop-engineering.md](01-loop-engineering.md). Every claim is anchored to
> exact files/lines.
>
> Arc of this note: **disease** (a "vibe" LLM referee saturates) →
> **diagnosis** (trend across labeled pairs + tracing + cross-check vs ground
> truth) → **cure** (`eval/scorer.py`: five objective components, the LLM demoted
> to a narrow auditable yes/no). Status: **LLM-as-judge / hill-climbing done.**
> Self-healing and self-correction are queued for note 03.

---

## 1. The disease — a holistic LLM referee saturates

The *loop's* hill (note 01 §3) gets its `grounded` and `engaged` inputs from one
LLM prompt — the referee, `core/hill.py:34-39`:

```python
REFEREE_SYSTEM = """You are a neutral referee rating the QUALITY of one round of a
matchmaking council's debate. You do NOT judge the match. You judge the DEBATE.
Rate two things 0..1:
- grounded: are the agents' claims tied to the given profile facts (vs invented/vague)?
- engaged: are agents actually responding to each other's points (vs talking past)?
Reply ONLY JSON: {"grounded": <0..1>, "engaged": <0..1>, "note": "<=30 words"}"""
```

Why this "measuring stick" is **too short**:

- **Holistic vibe score.** "Rate groundedness 0..1" asks for a *gestalt
  impression*, not a checkable computation. Models cluster high (0.7–0.9) for
  anything that *reads* well; nothing anchors a low score.
- **It judges the *debate*, not the *answer*.** Line 1 literally says *"You do
  NOT judge the match. You judge the DEBATE."* A debate can be beautifully
  grounded and engaged and still reach the **wrong verdict**. The stick cannot
  measure correctness — only debate aesthetics.
- **Model grading a model, no ground truth** = "blind leading the blind."
- **Self-heals to the middle.** On failure it returns `0.5/0.5`
  (`core/hill.py:52`), another force pulling values into a narrow band.

**Symptom, from the post (`docs/post_final.md:43`):** on a real case the hill
moved only `0.788 → 0.801` (Δ=0.013). *"Our measuring stick was too short… a
confident, grounded, but ultimately wrong answer scores highly."* Saturation =
**the metric stopped discriminating good from bad.**

---

## 2. Diagnosis — single event vs. trend, and what tracing buys you

- **A single early plateau is *not* a bug.** On a genuinely easy pair the debate
  can resolve in 2 rounds; converging fast and stopping is correct. One data
  point is ambiguous: "easy case, resolved" vs "sensor too blunt."
- **The bug shows up as a *trend across pairs*.** Discriminating test: run over a
  spread of pairs of known difficulty (our `eval/labels.json` encodes this —
  pair_02 easy/"broad alignment", pair_06 hard/"concealed avoidant trap").
  - Good sensor → trajectories **differ** (easy: plateau high & early; hard:
    climb slowly or plateau *low*). **Variance across pairs = working sensor.**
  - Short sensor → *every* pair plateaus at ~the same high value in ~the same
    round; easy and hard look **identical**. **Collapse of variance = saturation.**
  This is exactly what the post saw: hill ~0.79–0.80 regardless of case.

### How tracing operationalizes "trend as indicator"
`core/logbook.py:23-36` writes three artifacts per run: `events.jsonl`,
`hill.csv`, `transcript.md`. Three diagnostics a single number can't give:

1. **Plot hill trajectory per pair** (`logs/*/hill.csv`, columns
   `round,hill_score,score_spread`, `core/logbook.py:73-74`). Stack them; all-flat
   near 0.8 = saturation, visually.
2. **Cross-check the metric against ground truth — the killer move.** The hill
   said "good (0.8)." Did the *verdict* actually hit the human-labeled binding
   constraint and verdict band? `eval/score_partial.py:15-49` reads each run's
   `verdict` event from `events.jsonl` and scores it against `labels.json`. A
   high-hill run that still **misses** the binding constraint *proves* the hill
   measures the wrong thing. Tracing turns "I suspect saturation" into "here is a
   high-hill run that got the answer wrong."
3. **Read the transcript for the qualitative tell** (`transcript.md`): hill≈0.8
   on debates that are fluent but shallow. The referee's own `note` is persisted
   too (`core/hill.py:50` → `core/council.py:100-102`).

**Epistemology of evals in one move:** single number → could be anything; trend
across *labeled* pairs + trace cross-checked against ground truth → diagnosis.

---

## 3. The cure — `eval/scorer.py`, an objective label-based hill

Thesis, `eval/scorer.py:1-7`: *"This replaces the old 'ask an LLM if the debate
was good' hill, which saturated. Quality is now measured against HUMAN
GROUND-TRUTH LABELS … so a grounded-but-generic answer can still FAIL on
identifying the binding constraint or on calibration. The ceiling no longer maxes
out for free."*

Five components, fixed weights (`eval/scorer.py:34-40`):

```python
WEIGHTS = {
    "groundedness":      0.20,
    "binding_constraint": 0.30,   # the 'why', weighted MOST -- this kills saturation
    "verdict_band":      0.20,
    "calibration":       0.20,
    "anti_groupthink":   0.10,
}
```

Each component is a counter to a specific way of gaming a vibe judge:

| # | Component | Lines | Mechanism | Gaming strategy it defeats |
|---|---|---|---|---|
| 1 | groundedness | `:54-70` | deterministic lexical claim-tracing: fraction of content words in agent `position`s that appear in the profile | invention/hallucination (made-up claims add vocab the profile never used). *Weak proxy → only 0.20 (`:15` admits parroting risk).* |
| 2 | binding_constraint | `:76-90` | keyword search of verdict `rationale+open_tensions+headline` for the human-labeled deciding-axis keywords; ≥40% hit = full credit | **confident-but-wrong**: you can write a gorgeous debate and still not name the actual deciding factor. *The saturation-killer (Q6).* |
| 3 | verdict_band | `:96-100` | pure lookup: is `decision` in the label's allowed band? | plausible-sounding **wrong answers** (debate quality is irrelevant if the call is out of band) |
| 4 | calibration | `:106-116` | is `confidence` inside the label's band? outside → linear penalty by distance | **confident wrongness** — the deepest LLM-as-judge pathology; a vibe judge *rewards* confidence, this *punishes* unearned confidence |
| 5 | anti_groupthink | `:122-131` | from logs: if ended converged, full credit only if `engagement_seen or critic_fired`; else 0.4 | the cheapest fake debate — everyone instantly agreeing (same "earned agreement" idea as the loop's `resolution*engaged`, now hardened with log evidence) |

Combine: `hill_height = Σ weight·component` (`eval/scorer.py:137-138`), driven by
`score_run` (`:141-151`), wired across all pairs×stances in
`eval/experiment.py:43-80`.

### Why "name the right reason" is unfakeable (Q6)
The *right reason* presupposes a labeled right-vs-wrong, so it is **objectively
checkable**. "Grounded & engaged" only measures the *form* of the argument, not
its *target*. **A debate can be 100% grounded and 100% engaged and still be about
the wrong reason.** A fluent wrong model can max out form but cannot, by accident,
name a deciding factor it never identified.

### The meta-rule for *when* to use an LLM as judge (Q7)
Components 1 & 5 use **no LLM** (Python/log math), 2 uses keyword matching, 3–4
are lookups against human labels. The only sanctioned LLM use is a **narrow,
auditable, ~boolean entailment** ("does claim X follow from fact Y? yes/no") —
**never** a holistic 0..1 "how good is this?" vibe score (`eval/scorer.py:11-15`).
When the target is subjective/holistic, anchor to human ground truth or it's a
model grading a model.

---

## 4. Worked example — components 3, 4, 5 on pair_01 (Maya & Daniel)

Label (`eval/labels.json:11-17`): `verdict_band="not_a_match"`,
`confidence_band=[0.75,0.9]`,
`binding_constraint_keywords=["faith","catholic","children","kids","raise","timeline","repair","withdraw"]`.

Sample emitted verdict (object passed to `score_run`, `experiment.py:53`):
```json
{"decision":"not_a_match","confidence":0.82,
 "headline":"A warm pair divided by a non-negotiable faith-and-children gap.",
 "rationale":"...Maya needs children raised Catholic on a near-term timeline and Daniel is agnostic; under stress he withdraws while she pursues, so the repair capacity ... is exactly what's weakest.",
 "open_tensions":["Faith and childrearing remain unresolved","Pursue-withdraw pattern undermines repair"]}
```

**Component 3 — `verdict_band_match` (`scorer.py:96-100`)**
1. `band_name = "not_a_match"`; `band = bands["not_a_match"] = {"ok_decisions":["not_a_match"]}` (`labels.json:8`)
2. `"not_a_match" in ["not_a_match"]` → **1.0**.
Failure case: decision `"conditional"` → not in list → **0.0** (binary).
Note pair_01's band allows *only* `not_a_match`; pair_04's `conditional_yes`
allows *both* `match` and `conditional` (`labels.json:5`) — the label encodes how
much latitude the answer deserves.

**Component 4 — `calibration` (`scorer.py:106-116`)**
1. `lo,hi = 0.75,0.9`; `c = 0.82`; `0.75<=0.82<=0.9` → **1.0**.
Overconfident variant `c=0.98`: `dist = 0.98-0.90 = 0.08` →
`1 - 0.08/0.4 =` **0.80** (right answer, −20% for unjustified certainty).
On ambiguous pair_04 (`band [0.4,0.6]`), `c=0.95` → `dist=0.35` →
`1-0.35/0.4 =` **0.125**. *The system can be "right" and still be penalized for
not knowing how unsure it should be.*

**Component 5 — `anti_groupthink` (`scorer.py:122-131`)** — reads telemetry
(`experiment.py:56,65-67`), not the verdict.
- Converged & earned: `spread_last=0.05<0.12` → converged; `engagement_seen or
  critic_fired = True` → **1.0**.
- Groupthink: instant round-1 agreement, no critic, no engagement → converged but
  `earned=False` → **0.4** (−60%).
- Not converged: `spread_last=0.30` → not converged → **0.7** (healthy
  disagreement neither punished nor fully rewarded).

**Combine (`scorer.py:137-138`)**

| Component | Value | Weight | Contribution |
|---|---|---|---|
| groundedness | 0.90 | 0.20 | 0.180 |
| binding_constraint | 1.00 | 0.30 | 0.300 |
| verdict_band | 1.00 | 0.20 | 0.200 |
| calibration | 1.00 | 0.20 | 0.200 |
| anti_groupthink | 1.00 | 0.10 | 0.100 |
| **hill_height** | | | **0.980** |

Same run **overconfident** (calib 0.80) → **0.940**.
**Confidently wrong** (`match`, `c=0.95`): verdict_band→0, binding likely drops,
calibration penalized → ≈ **0.45–0.55**.
The spread **0.98 / 0.94 / 0.50** is the point — the old vibe referee gave ~0.79
to all three. The objective hill *separates* them; the ceiling is no longer free.

---

## 5. Empirical proof it worked

`logs/experiment_20260617_151646/report.md` (echoed in `docs/post_final.md:66-76`):

| Stance | Hill | Calibration | Binding hit | Verdict match |
|---|---|---|---|---|
| Neutral | 0.844 | 0.842 | 1.00 | 1.00 |
| Grace | 0.841 | 0.846 | 1.00 | 1.00 |
| Grace + Skeptic | 0.841 | 0.833 | 1.00 | 1.00 |

Binding-hit and verdict-match max at **1.00** (the system reliably names the right
reason and lands the right band), but **calibration is the bottleneck (~0.84)** —
the residual weakness is overconfidence on ambiguous pairs. The old vibe hill
could never surface that; it just said "0.8, good" for everything. **A taller
stick changes the question from "is the debate nice?" to "where exactly is the
system still wrong?"** — which is the entire purpose of an eval.

---

## Exact-reference cheat sheet

| Concept | Where |
|---|---|
| The saturating referee (vibe sensor) | `core/hill.py:34-52` |
| Saturation symptom (prose) | `docs/post_final.md:39-50` |
| Objective scorer thesis + weights | `eval/scorer.py:1-40` |
| groundedness (lexical trace) | `eval/scorer.py:54-70` |
| binding_constraint (the 'why') | `eval/scorer.py:76-90` |
| verdict_band (lookup) | `eval/scorer.py:96-100` |
| calibration (penalize overconfidence) | `eval/scorer.py:106-116` |
| anti_groupthink (earned agreement, from logs) | `eval/scorer.py:122-131` |
| combine + score_run | `eval/scorer.py:137-151` |
| human ground truth | `eval/labels.json` |
| A/B/C experiment wiring | `eval/experiment.py:43-80` |
| trace cross-check vs labels | `eval/score_partial.py:15-49` |
| result | `logs/experiment_20260617_151646/report.md` |
| the rule for using an LLM as judge | `eval/scorer.py:11-15` |

## Open threads (note 03)
- [ ] **Self-healing**: `core/llm.py:55-103` (retries + JSON repair + `LLMDown`);
  surfaced at `core/council.py:67,75-78` and `core/judge.py:64-79`; fault
  injection `core/faults.py`; live artifact `logs/run_20260617_015936/transcript.md`.
- [ ] **Self-correction**: `core/critic.py` end-to-end; runnable demo
  `tests/test_self_correction.py`; artifact `logs/test_self_correction/transcript.md`.
