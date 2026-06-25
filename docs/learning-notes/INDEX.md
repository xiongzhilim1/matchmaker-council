# Learning Notes — Index (Track B)

Durable notes from the Concept Learning track. Each session that teaches a
concept should add a note here and link it below. Use our own codebase as the
running example so the learning stays concrete.

## Concepts to cover (from the original goal)
- [x] Loop engineering — the stopping rule (see `core/council.py`) → [01-loop-engineering.md](01-loop-engineering.md)
- [ ] Hill-climbing — defining "higher" objectively (see `eval/scorer.py`, `core/hill.py`)
- [ ] Self-correcting — critic catches & forces revision (see `core/critic.py`)
- [ ] Self-healing — routing around dead components (see `core/llm.py`, `core/council.py`)
- [ ] Self-learning — memory/priors across runs (deferred; v2)
- [ ] LLM-as-judge evals & why they saturate (see `docs/post_final.md` §3)
- [ ] Multi-agent negotiation vs single-prompt — when many agents are worth the cost

## Notes
- [01 — Loop Engineering & the Spine](01-loop-engineering.md) — the deliberation spine, lag-1 cross-round debate, the hill formula, the four-gate stopping rule, and why a stopping rule is only as good as the (saturating) metric it watches. Includes `assets/spine_sequence.png` and `assets/stopping_rule.png`. *(Self-healing, self-correction, and the objective scorer threads are queued at the end of the note.)*

## How to add a note
Create `docs/learning-notes/NN-topic.md`, write what you learned in your own
words plus the exact files/lines it maps to, then link it above and commit.
