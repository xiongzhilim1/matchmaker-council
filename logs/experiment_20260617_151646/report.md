# A/B/C Calibration Experiment

Model: `gpt-5-mini`

Stances: **neutral** (no grace/skeptic), **grace** (grace only), **grace_skeptic** (grace + RealityCheck).


## Aggregate (mean over pairs)

| Stance | Hill | Calibration | Binding-constraint hit | Verdict-band match |
|---|---|---|---|---|
| neutral | 0.844 | 0.842 | 1.000 | 1.000 |
| grace | 0.841 | 0.846 | 1.000 | 1.000 |
| grace_skeptic | 0.841 | 0.833 | 1.000 | 1.000 |

## Per-pair detail

| Pair | Stance | Decision | Conf | Label band | Conf band | Binding | Calib | Hill |
|---|---|---|---|---|---|---|---|---|
| Maya & Daniel | neutral | not_a_match | 0.88 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.861 |
| Sam & Priya | neutral | match | 0.94 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.902 |
| Tom & Lena | neutral | not_a_match | 0.95 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.863 |
| Ade & Joy | neutral | conditional | 0.78 | conditional_yes | [0.4, 0.6] | 1.00 | 0.55 | 0.806 |
| Ravi & Mei | neutral | conditional | 0.72 | conditional_yes | [0.5, 0.7] | 1.00 | 0.95 | 0.864 |
| Noah & Grace | neutral | not_a_match | 0.88 | conditional_no | [0.55, 0.7] | 1.00 | 0.55 | 0.767 |
| Maya & Daniel | grace | not_a_match | 0.88 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.870 |
| Sam & Priya | grace | match | 0.95 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.891 |
| Tom & Lena | grace | not_a_match | 0.94 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.861 |
| Ade & Joy | grace | conditional | 0.82 | conditional_yes | [0.4, 0.6] | 1.00 | 0.45 | 0.779 |
| Ravi & Mei | grace | conditional | 0.72 | conditional_yes | [0.5, 0.7] | 1.00 | 0.95 | 0.850 |
| Noah & Grace | grace | conditional | 0.83 | conditional_no | [0.55, 0.7] | 1.00 | 0.68 | 0.793 |
| Maya & Daniel | grace_skeptic | not_a_match | 0.9 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.858 |
| Sam & Priya | grace_skeptic | match | 0.92 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.885 |
| Tom & Lena | grace_skeptic | not_a_match | 0.97 | not_a_match | [0.85, 0.95] | 1.00 | 0.95 | 0.859 |
| Ade & Joy | grace_skeptic | conditional | 0.78 | conditional_yes | [0.4, 0.6] | 1.00 | 0.55 | 0.787 |
| Ravi & Mei | grace_skeptic | conditional | 0.72 | conditional_yes | [0.5, 0.7] | 1.00 | 0.95 | 0.866 |
| Noah & Grace | grace_skeptic | not_a_match | 0.88 | conditional_no | [0.55, 0.7] | 1.00 | 0.55 | 0.790 |
