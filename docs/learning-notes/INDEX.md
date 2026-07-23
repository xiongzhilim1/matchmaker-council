# Learning Notes — Index (Track B)

Durable notes from the Concept Learning track. Each session that teaches a
concept should add a note here and link it below. Use our own codebase as the
running example so the learning stays concrete.

## Concepts to cover (from the original goal)
- [x] Loop engineering — the stopping rule (see `core/council.py`) → [01-loop-engineering.md](01-loop-engineering.md)
- [x] Hill-climbing — defining "higher" objectively (see `eval/scorer.py`, `core/hill.py`) → [02-llm-as-judge-evals.md](02-llm-as-judge-evals.md)
- [x] Self-correcting — critic catches & forces revision (see `core/critic.py`) → [04-self-correction.md](04-self-correction.md)
- [x] Self-healing — routing around dead components (see `core/llm.py`, `core/council.py`) → [03-self-healing.md](03-self-healing.md)
- [ ] Self-learning — memory/priors across runs (deferred; v2)
- [x] LLM-as-judge evals & why they saturate (see `docs/post_final.md` §3) → [02-llm-as-judge-evals.md](02-llm-as-judge-evals.md)
- [ ] Multi-agent negotiation vs single-prompt — when many agents are worth the cost

## Notes
- [01 — Loop Engineering & the Spine](01-loop-engineering.md) — the deliberation spine, lag-1 cross-round debate, the hill formula, the four-gate stopping rule, and why a stopping rule is only as good as the (saturating) metric it watches. Includes `assets/spine_sequence.png` and `assets/stopping_rule.png`.
- [02 — LLM-as-Judge Evals](02-llm-as-judge-evals.md) — why the holistic "vibe" referee saturates, how to diagnose it (variance across labeled pairs + tracing + cross-check vs ground truth), and the objective five-component `eval/scorer.py` that replaced it, with a full worked example on pair_01.
- [03 — Self-Healing](03-self-healing.md) — three layers of defense (retry, JSON repair, structured surrender), the `down=True` sentinel, routing around dead agents, the referee fallback trap, and why self-heal instead of crash-and-restart.
- [04 — Self-Correction](04-self-correction.md) — the critic's narrow yes/no mandate, one-revision contract, placement before the hill, why skip-on-failure is safer than substitute, and how `critic_fired` feeds the eval's anti-groupthink component. Includes runnable test + fault injection.

## How to add a note
Create `docs/learning-notes/NN-topic.md`, write what you learned in your own
words plus the exact files/lines it maps to, then link it above and commit.
