# v2 Build State (working notes)

## What's been built so far

1. `eval/diagnose.py` — works, produces `eval/diagnosis.json`
2. `eval/optimize.py` — works, produces `eval/optimization_report.md`
3. `config/priors.json` — initial prior created
4. `core/judge.py` — modified to read priors + added safety-gate calibration guidance
5. `config/settings.py` — added PRIORS_FILE path

## Experiment results

### Baseline (experiment_20260619_014131)
| Stance | Hill | Calibration | Binding-hit | Verdict-match |
|---|---|---|---|---|
| neutral | 0.876 | 1.000 | 1.000 | 1.000 |
| grace | 0.872 | 1.000 | 1.000 | 1.000 |
| grace_skeptic | 0.859 | 0.917 | 1.000 | 1.000 |

### After first fix attempt (experiment_20260724_054640)
| Stance | Hill | Calibration | Binding-hit | Verdict-match |
|---|---|---|---|---|
| neutral | 0.881 | 1.000 | 1.000 | 1.000 |
| grace | 0.881 | 1.000 | 1.000 | 1.000 |
| grace_skeptic | 0.813 | 0.946 | 0.938 | 0.833 |

**SUCCESS GATE: FAILED** — grace_skeptic regressed 0.859 → 0.813

### Root cause of regression
The Judge prompt fix was too broad. It told the Judge "don't escalate to not_a_match
on inferred patterns" but this also softened:
- pair_01 (Maya & Daniel): faith/kids dealbreaker is EXPLICITLY STATED, not inferred.
  Judge incorrectly softened to conditional at 0.62. Label: not_a_match [0.75,0.9].
- pair_05 (Ravi & Mei): binding-hit dropped to 0.62 (rationale missed keywords).

### Fix needed
Scope the guidance more narrowly:
- "Inferred, unverified, CONCEALED" pattern → pause (conditional, ~0.6 confidence)
- "Explicitly stated, declared dealbreaker" → still honor as not_a_match at high confidence
- The key distinction: CONCEALED vs DECLARED. Noah's avoidance is concealed; Maya's
  faith requirement is declared.

### What to change in core/judge.py
The current text says:
"Do NOT escalate to 'not_a_match' at high confidence (>0.75) unless the hazard is
CONFIRMED and IRREVERSIBLE"

This is wrong — it should say:
"Do NOT escalate to 'not_a_match' at high confidence (>0.75) unless EITHER:
(a) the hazard is confirmed/irreversible, OR
(b) a person has EXPLICITLY DECLARED a non-negotiable dealbreaker that the other
    person's profile clearly contradicts (e.g., stated 'must share my faith' vs
    partner is agnostic). Declared dealbreakers are NOT inferred patterns — they
    are stated boundaries that must be honored."

## Files to modify
- `core/judge.py` lines 53-59 (the safety-gate calibration block)
- `config/priors.json` (update the prior's guidance to include the distinction)
