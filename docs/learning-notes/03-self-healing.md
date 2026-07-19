# 03 — Self-Healing: routing around dead components

> Running example: **our own codebase**. Continues from
> [02-llm-as-judge-evals.md](02-llm-as-judge-evals.md). Every claim is anchored
> to exact files/lines.
>
> This note covers the **transport/structural** self-healing pattern: what
> happens when an LLM call fails, and how the system stays alive without
> crashing. Self-correction (the *epistemic* counterpart — "the call succeeded
> but said something wrong") is in [04-self-correction.md](04-self-correction.md).

---

## 0. Self-healing vs. self-correction — the distinction

| Pattern | Layer | What it routes around | Within or across runs? |
|---|---|---|---|
| **Self-healing** (this note) | transport / structural | a **dead component** (LLM call fails) | within a run, automatically |
| Self-correction (note 04) | epistemic / content | a **wrong claim** (grounded-sounding falsehood) | within a run (one revision) |
| Self-learning | memory | priors across runs | deferred (v2, not built) |

Self-healing keeps the system **alive**; self-correction keeps it **honest**.

---

## 1. Three layers of defense, escalating

All LLM calls pass through one seam, `core/llm.py:40-103` (`LLMClient`). The
defenses are:

### Layer 1 — Retry with exponential backoff (`core/llm.py:59-79`)

```python
for attempt in range(settings.MAX_RETRIES + 1):
    try:
        resp = self.client.chat.completions.create(...)
        return LLMResult(...)
    except Exception as e:
        last_err = e
        time.sleep(1.5 * (attempt + 1))   # 1.5s, 3s, 4.5s, ...
raise LLMDown(f"model={self.model} failed after retries: {last_err}")
```

Handles: transient 5xx, timeouts, rate limits. Most failures resolve here
silently.

### Layer 2 — JSON repair (`core/llm.py:82-103` + `_extract_json:106-133`)

Models often wrap JSON in prose or code fences. The repair pipeline:
1. Strip code fences (`re.sub(r"```(?:json)?", "", text)`, `:111`).
2. Fast-path `json.loads` (`:113-116`).
3. Find first balanced `{...}` by depth-counting (`:118-132`).
4. If all fail: **one corrective re-ask** showing the model its own broken output
   (`:94-99`, temperature=0.0 for determinism).
5. If *that* fails: raise `LLMDown` (`:103`).

### Layer 3 — Structured surrender: `LLMDown` (`core/llm.py:27-29`)

Not a generic exception — a **typed signal** meaning "this component is
unavailable." Caught at the **agent boundary** (`agents/agent.py:95-99`):

```python
except LLMDown:
    return Turn(agent=self.name, layer=self.layer, score=0.5,
                position="(agent unavailable this round)", reaction="",
                latency_s=None, down=True)
```

The `down=True` sentinel is **data, not an error**. The orchestrator treats it as
such.

---

## 2. How the orchestrator routes around a dead agent

`core/council.py:62-78`:

```python
for agent in self.agents:
    turn = agent.assess(profiles_json, prev_summary, round_idx=r)
    if turn.down:
        self.log.healing(r, agent.name, "LLM call failed; dropped this round, council continues.")
    else:
        self.log.agent_turn(...)
    turns.append(turn)

# safety net: if EVERY agent died, abort cleanly
live = [t for t in turns if not t.down]
if not live:
    self.log.healing(r, "council", "All agents down this round; aborting deliberation.")
    break
```

- **Some down:** the dead agent is simply absent from the vote. The hill
  (`core/council.py:93`) and the debate summary (`core/council.py:43-48`) both
  filter on `not t.down`. The round proceeds with fewer voices.
- **All down:** abort cleanly (structured exit with a log message, not a crash).
  This prevents `score_spread([])` from raising `StatisticsError`, and prevents
  the stop-gates from producing semantically meaningless reasons ("converged"
  when nobody was there).

---

## 3. The real artifact — proof it works

`logs/run_20260617_015936/transcript.md`:

- **Line 19:** `> ⚕️ **Self-healing:** agent AttractionSpark — LLM call failed;
  dropped this round, council continues.`
- **Line 48:** Same agent, same failure, round 2.
- **Lines 21–37:** Round 1 continues with 5 live agents, hill computed normally.
- **Lines 50–74:** Round 2 proceeds, agents react to each other.
- **Line 77:** Loop stops normally ("hill plateaued").
- **Lines 80–94:** Judge produces a `not_a_match` verdict.

**One dead agent, zero crash, valid outcome.** The system degraded gracefully from
7 agents to 5 and still reached a grounded verdict.

---

## 4. Fault injection — making self-healing demonstrable

`core/faults.py:1-35`:

```bash
MATCHMAKER_KILL_AGENT=AttractionSpark python3 run.py
```

At `agents/agent.py:62-67`, if the agent's name is in `faults.killed_agents()`,
it immediately returns a `down=True` Turn **without calling the LLM**. This lets
you trigger self-healing deterministically for teaching/testing without depending
on real API failures.

---

## 5. The referee can also go down

`core/council.py:96-98`:

```python
ref = hillmod.referee_quality(self.client, profiles_json, self._round_text(turns))
if ref.get("down"):
    self.log.healing(r, "referee", "Referee unavailable; used neutral quality estimate.")
```

When the referee fails, it returns `{"grounded": 0.5, "engaged": 0.5, "down": True}`.
This is self-healing at the *metric* layer — and it has a subtle consequence.

### The sneaky feedback loop (Q10)

Plugging `grounded=0.5, engaged=0.5` into the hill formula gives h ≈ 0.4–0.5.
If round 1 had a normal hill of 0.60 and round 2's referee dies:
- gain = 0.48 - 0.60 = **-0.12** (negative)
- `-0.12 < CONVERGENCE_DELTA(0.05)` → gate (3) fires: **"hill plateaued"**

The loop stops — not because quality plateaued, but because the **sensor broke.**
A healed metric *looks like a real measurement* to everything downstream.

**Design principle:** heal the *system* (keep it alive); be cautious healing the
*measurement* (that can hide the problem). The honest alternative: mark that
round's hill as "unmeasured" rather than substituting a number. The current design
chose availability over accuracy — defensible for a runtime loop, but exactly the
kind of thing the objective eval (`eval/scorer.py`) exists to catch after the fact.

---

## 6. Why self-heal instead of crash-and-restart?

Three reasons this codebase pays the complexity cost:

1. **Accumulated state is expensive to rebuild.** By round 3, the system has
   spent 18+ LLM calls building up debate context. A restart re-spends all of
   that. Self-healing (drop one agent, continue with 6/7) costs zero extra calls.
2. **LLM API failures are routine operational noise**, not exceptional events
   (~1–5% of calls). If every failure triggers a restart, you restart constantly.
   Self-healing treats transient failure like TCP treats dropped packets — retransmit,
   don't tear down the connection.
3. **Deliberations are non-deterministic.** A restart doesn't resume — it produces
   a *completely different debate* (temperature > 0). Self-healing preserves the
   continuity of the deliberation: same agents, same positions, same debate
   summary — just one fewer voice this round.

**When crashing *is* correct:** all agents down (`core/council.py:75-78`). If
there's nothing to route around, continuing produces meaningless output. Threshold:
**partial failure → heal; total failure → stop honestly.**

---

## Exact-reference cheat sheet

| Concept | Where |
|---|---|
| LLMClient seam (single entry point) | `core/llm.py:40-53` |
| Retry with backoff | `core/llm.py:59-79` |
| JSON repair + corrective re-ask | `core/llm.py:82-103` |
| `_extract_json` (fence strip, balanced-brace) | `core/llm.py:106-133` |
| `LLMDown` exception (typed signal) | `core/llm.py:27-29` |
| Agent catches `LLMDown` → `down=True` sentinel | `agents/agent.py:95-99` |
| Orchestrator routes around dead agent | `core/council.py:64-72` |
| All-down abort | `core/council.py:74-78` |
| Referee self-healing (neutral fallback) | `core/council.py:96-98` |
| Fault injection (`MATCHMAKER_KILL_AGENT`) | `core/faults.py:8-10`, `agents/agent.py:62-67` |
| Real artifact (AttractionSpark down) | `logs/run_20260617_015936/transcript.md:19,48` |
| `engagement_seen` / `critic_fired` flags for eval | `core/council.py:40-41,81-82,89-90` |

## Open threads (note 04)
- [ ] **Self-correction**: `core/critic.py` end-to-end; the critic prompt; the
  one-revision contract; runnable demo `tests/test_self_correction.py`; real
  in-run artifact `logs/exp_pair_04_neutral/transcript.md:30-32`.
