# A/B/C Calibration Experiment

Model: `gpt-5-mini`

Stances: **neutral** (no grace/skeptic), **grace** (grace only), **grace_skeptic** (grace + RealityCheck).


## Aggregate (mean over pairs)

| Stance | Hill | Calibration | Binding-constraint hit | Verdict-band match |
|---|---|---|---|---|
| neutral | 0.876 | 1.000 | 1.000 | 1.000 |
| grace | 0.872 | 1.000 | 1.000 | 1.000 |
| grace_skeptic | 0.859 | 0.917 | 1.000 | 1.000 |

## Per-pair detail

| Pair | Stance | Decision | Conf | Label band | Conf band | Binding | Calib | Hill |
|---|---|---|---|---|---|---|---|---|
| Maya & Daniel | neutral | not_a_match | 0.9 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.862 |
| Sam & Priya | neutral | match | 0.92 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.907 |
| Tom & Lena | neutral | not_a_match | 0.9 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.864 |
| Ade & Joy | neutral | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.892 |
| Ravi & Mei | neutral | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.876 |
| Noah & Grace | neutral | conditional | 0.62 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.854 |
| Maya & Daniel | grace | not_a_match | 0.88 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.863 |
| Sam & Priya | grace | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.893 |
| Tom & Lena | grace | not_a_match | 0.9 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.860 |
| Ade & Joy | grace | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.891 |
| Ravi & Mei | grace | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.861 |
| Noah & Grace | grace | conditional | 0.65 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.862 |
| Maya & Daniel | grace_skeptic | not_a_match | 0.88 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.862 |
| Sam & Priya | grace_skeptic | match | 0.92 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.895 |
| Tom & Lena | grace_skeptic | not_a_match | 0.9 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.857 |
| Ade & Joy | grace_skeptic | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.903 |
| Ravi & Mei | grace_skeptic | conditional | 0.62 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.876 |
| Noah & Grace | grace_skeptic | not_a_match | 0.9 | conditional_no | [0.55, 0.7] | 1.00 | 0.50 | 0.759 |
