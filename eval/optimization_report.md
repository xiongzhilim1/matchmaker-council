# Optimization Report

Timestamp: 2026-07-24T08:00:16.657602
Model: gpt-5-mini
Baseline hills: {"neutral": 0.876, "grace": 0.8776, "grace_skeptic": 0.8663}

## Clusters (ranked by impact)

### Cluster 1: `groundedness_neutral_grace_skeptic_grace`
- Component: groundedness
- Root cause: Agent claims not sufficiently grounded in profile text
- Impact: 0.2
- Affected: ['pair_02', 'pair_04', 'pair_01', 'pair_06', 'pair_05', 'pair_03'] × ['neutral', 'grace_skeptic', 'grace']
- Suggested fix: Tighten agent prompts to require explicit profile citations; consider making the critic stricter on unsupported claims

**Attempting fix for top cluster...**

Proposed prior: `groundedness_neutral_grace_skeptic_grace`
Guidance: Tighten agent prompts to require explicit profile citations; consider making the critic stricter on unsupported claims

**Status:** Fix applied to Judge prompt + priors.json.
Run `PYTHONPATH=. python3 eval/experiment.py` to confirm via Success Gate.

