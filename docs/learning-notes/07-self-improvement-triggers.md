# 07 — Self-Improvement Triggers: How the Loop Gets Invoked

> **Core question:** The Diagnose → Optimize → Evaluate → Gate loop is built.
> But what *triggers* it? A loop that nobody runs is dead code.

---

## The Three Levels

### Level 1: Manual (where v2 started)

A human opens a session, reads `SESSION_LOG.md` / `ROADMAP.md`, and runs:

```bash
PYTHONPATH=. python3 eval/diagnose.py       # what's broken?
PYTHONPATH=. python3 eval/optimize.py       # propose a fix
PYTHONPATH=. python3 eval/experiment.py     # re-eval (18 deliberations, ~45-60 min)
PYTHONPATH=. python3 -c "from eval.optimize import verify_gate; verify_gate()"
```

**Trigger:** human memory + session protocol.
**Problem:** relies on you remembering; easy to skip.

---

### Level 2: Single CLI command (current state)

All four steps wired into one script:

```bash
PYTHONPATH=. python3 eval/loop.py           # full cycle
PYTHONPATH=. python3 eval/loop.py --dry-run # diagnose only, no eval
```

**What it does:**
1. Diagnoses failures from the latest experiment results
2. Filters to actionable clusters (skips systemic issues like groundedness threshold)
3. Checks if a fix is already applied (avoids re-applying existing priors)
4. Runs the full eval (18 deliberations)
5. Compares new hills to baseline via the Success Gate
6. Reports pass/fail with details

**Trigger:** still human, but friction is reduced to one command.
**Where it lives:** `eval/loop.py`

**Session protocol (bake it into habit):**
> "Before doing product work, run `eval/loop.py --dry-run` to check if there
> are diagnosed failures worth fixing. If yes, run without `--dry-run`."

---

### Level 3: Scheduled / event-triggered (future)

For truly automatic self-improvement, the loop needs a **trigger event**:

| Trigger | When it fires | What it does |
|---|---|---|
| **On code change** (CI/CD) | Every push to `master` touching `core/`, `agents/`, `config/` | Runs full eval; blocks merge if regression detected |
| **On schedule** (cron) | e.g., weekly | Runs `eval/loop.py`; commits improvements if gate passes; opens PR for human review |
| **On new labeled data** | When `eval/labels.json` changes | Re-runs eval on expanded set; diagnoses new failures |

**Implementation options:**
- GitHub Actions workflow (`.github/workflows/eval.yml`)
- Manus scheduled task (`manus-config schedule`)
- Local cron job on a persistent VM

**Safety constraints for Level 3:**
- The Optimizer must never modify `eval/scorer.py` or `eval/labels.json` (the eval is sacred)
- Automated commits must go through a PR, not direct to `master`
- A human reviews before merge (the Success Gate is necessary but not sufficient)
- Rate-limit: at most one optimization cycle per day (token cost control)

---

## The Design Principle

> **The loop's value is proportional to how often it runs.**
> Level 1 runs when you remember. Level 2 runs when you type one command.
> Level 3 runs whether you remember or not.
>
> But safety is inversely proportional to automation:
> Level 1 is safest (human reviews everything). Level 3 needs the most guardrails.
> The Success Gate is the bridge — it makes automation safe by gating on objective improvement.

---

## Current state of this codebase

| Level | Status | File |
|---|---|---|
| Level 1 (manual steps) | Built, tested, documented | `eval/diagnose.py`, `eval/optimize.py`, `eval/experiment.py` |
| Level 2 (single CLI) | Built, tested | `eval/loop.py` |
| Level 3 (scheduled) | Not yet built | Future: `.github/workflows/eval.yml` or `manus-config schedule` |

---

## Relevant files

| File | Role | Lines |
|---|---|---|
| `eval/loop.py` | Single CLI entry point for the full cycle | entire file |
| `eval/diagnose.py` | Step 1: cluster failures | `:diagnose()` |
| `eval/optimize.py` | Step 2: propose fix + gate | `:optimize()`, `:verify_gate()` |
| `eval/experiment.py` | Step 3: run 18 deliberations | `:main()` |
| `config/priors.json` | Validated learnings (grows over time) | entire file |
| `docs/v2/SPEC.md` | Formal spec for the whole v2 system | §3.1–3.3 |

---

## Key takeaway

The loop is only as good as its trigger. Build the loop first (done), then
reduce the friction of running it (done — Level 2), then automate the trigger
(future — Level 3). At each level, the Success Gate is what makes it safe.
