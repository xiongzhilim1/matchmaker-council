# A/B/C Calibration Experiment

Model: `gpt-5-mini`

Stances: **neutral** (no grace/skeptic), **grace** (grace only), **grace_skeptic** (grace + RealityCheck).


## Aggregate (mean over pairs)

| Stance | Hill | Calibration | Binding-constraint hit | Verdict-band match |
|---|---|---|---|---|
| neutral | 0.876 | 1.000 | 1.000 | 1.000 |
| grace | 0.878 | 1.000 | 1.000 | 1.000 |
| grace_skeptic | 0.866 | 1.000 | 1.000 | 1.000 |

## Per-pair detail

| Pair | Stance | Decision | Conf | Label band | Conf band | Binding | Calib | Hill |
|---|---|---|---|---|---|---|---|---|
| Maya & Daniel | neutral | not_a_match | 0.86 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.866 |
| Sam & Priya | neutral | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.908 |
| Tom & Lena | neutral | not_a_match | 0.88 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.868 |
| Ade & Joy | neutral | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.884 |
| Ravi & Mei | neutral | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.870 |
| Noah & Grace | neutral | conditional | 0.6 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.861 |
| Maya & Daniel | grace | not_a_match | 0.85 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.858 |
| Sam & Priya | grace | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.898 |
| Tom & Lena | grace | not_a_match | 0.88 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.858 |
| Ade & Joy | grace | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.875 |
| Ravi & Mei | grace | conditional | 0.55 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.876 |
| Noah & Grace | grace | conditional | 0.6 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.900 |
| Maya & Daniel | grace_skeptic | not_a_match | 0.87 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.850 |
| Sam & Priya | grace_skeptic | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.894 |
| Tom & Lena | grace_skeptic | not_a_match | 0.88 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.846 |
| Ade & Joy | grace_skeptic | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.884 |
| Ravi & Mei | grace_skeptic | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.866 |
| Noah & Grace | grace_skeptic | conditional | 0.6 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.858 |
