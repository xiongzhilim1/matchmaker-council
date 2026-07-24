# A/B/C Calibration Experiment

Model: `gpt-5-mini`

Stances: **neutral** (no grace/skeptic), **grace** (grace only), **grace_skeptic** (grace + RealityCheck).


## Aggregate (mean over pairs)

| Stance | Hill | Calibration | Binding-constraint hit | Verdict-band match |
|---|---|---|---|---|
| neutral | 0.881 | 1.000 | 1.000 | 1.000 |
| grace | 0.881 | 1.000 | 1.000 | 1.000 |
| grace_skeptic | 0.813 | 0.946 | 0.938 | 0.833 |

## Per-pair detail

| Pair | Stance | Decision | Conf | Label band | Conf band | Binding | Calib | Hill |
|---|---|---|---|---|---|---|---|---|
| Maya & Daniel | neutral | not_a_match | 0.88 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.858 |
| Sam & Priya | neutral | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.891 |
| Tom & Lena | neutral | not_a_match | 0.9 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.868 |
| Ade & Joy | neutral | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.897 |
| Ravi & Mei | neutral | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.879 |
| Noah & Grace | neutral | conditional | 0.62 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.891 |
| Maya & Daniel | grace | not_a_match | 0.88 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.855 |
| Sam & Priya | grace | match | 0.88 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.909 |
| Tom & Lena | grace | not_a_match | 0.92 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.875 |
| Ade & Joy | grace | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.901 |
| Ravi & Mei | grace | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.883 |
| Noah & Grace | grace | conditional | 0.6 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.864 |
| Maya & Daniel | grace_skeptic | conditional | 0.62 | not_a_match | [0.75, 0.9] | 1.00 | 0.68 | 0.599 |
| Sam & Priya | grace_skeptic | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.896 |
| Tom & Lena | grace_skeptic | not_a_match | 0.9 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.861 |
| Ade & Joy | grace_skeptic | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.898 |
| Ravi & Mei | grace_skeptic | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 0.62 | 1.00 | 0.767 |
| Noah & Grace | grace_skeptic | conditional | 0.6 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.855 |
