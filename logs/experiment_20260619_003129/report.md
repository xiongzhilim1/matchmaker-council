# A/B/C Calibration Experiment

Model: `gpt-5-mini`

Stances: **neutral** (no grace/skeptic), **grace** (grace only), **grace_skeptic** (grace + RealityCheck).


## Aggregate (mean over pairs)

| Stance | Hill | Calibration | Binding-constraint hit | Verdict-band match |
|---|---|---|---|---|
| neutral | 0.829 | 0.746 | 1.000 | 1.000 |
| grace | 0.840 | 0.817 | 1.000 | 1.000 |
| grace_skeptic | 0.836 | 0.838 | 1.000 | 1.000 |

## Per-pair detail

| Pair | Stance | Decision | Conf | Label band | Conf band | Binding | Calib | Hill |
|---|---|---|---|---|---|---|---|---|
| Maya & Daniel | neutral | not_a_match | 0.92 | not_a_match | [0.75, 0.9] | 1.00 | 0.95 | 0.858 |
| Sam & Priya | neutral | match | 0.95 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.909 |
| Tom & Lena | neutral | not_a_match | 0.96 | not_a_match | [0.85, 0.95] | 1.00 | 0.97 | 0.861 |
| Ade & Joy | neutral | conditional | 0.8 | conditional_yes | [0.4, 0.6] | 1.00 | 0.50 | 0.801 |
| Ravi & Mei | neutral | conditional | 0.78 | conditional_yes | [0.5, 0.7] | 1.00 | 0.80 | 0.846 |
| Noah & Grace | neutral | conditional | 0.25 | conditional_no | [0.55, 0.7] | 1.00 | 0.25 | 0.699 |
| Maya & Daniel | grace | not_a_match | 0.88 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.868 |
| Sam & Priya | grace | match | 0.96 | match | [0.8, 0.95] | 1.00 | 0.97 | 0.893 |
| Tom & Lena | grace | not_a_match | 0.95 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.863 |
| Ade & Joy | grace | conditional | 0.82 | conditional_yes | [0.4, 0.6] | 1.00 | 0.45 | 0.776 |
| Ravi & Mei | grace | conditional | 0.78 | conditional_yes | [0.5, 0.7] | 1.00 | 0.80 | 0.838 |
| Noah & Grace | grace | conditional | 0.83 | conditional_no | [0.55, 0.7] | 1.00 | 0.68 | 0.798 |
| Maya & Daniel | grace_skeptic | not_a_match | 0.9 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.870 |
| Sam & Priya | grace_skeptic | match | 0.92 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.895 |
| Tom & Lena | grace_skeptic | not_a_match | 0.96 | not_a_match | [0.85, 0.95] | 1.00 | 0.97 | 0.870 |
| Ade & Joy | grace_skeptic | conditional | 0.78 | conditional_yes | [0.4, 0.6] | 1.00 | 0.55 | 0.761 |
| Ravi & Mei | grace_skeptic | conditional | 0.74 | conditional_yes | [0.5, 0.7] | 1.00 | 0.90 | 0.843 |
| Noah & Grace | grace_skeptic | conditional | 0.86 | conditional_no | [0.55, 0.7] | 1.00 | 0.60 | 0.778 |
