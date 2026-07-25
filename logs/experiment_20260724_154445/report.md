# A/B/C Calibration Experiment

Model: `gpt-5-mini`

Stances: **neutral** (no grace/skeptic), **grace** (grace only), **grace_skeptic** (grace + RealityCheck).


## Aggregate (mean over pairs)

| Stance | Hill | Calibration | Binding-constraint hit | Verdict-band match |
|---|---|---|---|---|
| neutral | 0.825 | 0.977 | 0.821 | 1.000 |
| grace | 0.800 | 0.975 | 0.727 | 1.000 |
| grace_skeptic | 0.806 | 0.977 | 0.773 | 1.000 |

## Per-pair detail

| Pair | Stance | Decision | Conf | Label band | Conf band | Binding | Calib | Hill |
|---|---|---|---|---|---|---|---|---|
| Maya & Daniel | neutral | not_a_match | 0.85 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.862 |
| Sam & Priya | neutral | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.905 |
| Tom & Lena | neutral | not_a_match | 0.88 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.863 |
| Ade & Joy | neutral | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.884 |
| Ravi & Mei | neutral | conditional | 0.58 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.886 |
| Noah & Grace | neutral | conditional | 0.6 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.856 |
| Priya Desai & Mateo Alvarez | neutral | conditional | 0.58 | conditional_no | [0.62, 0.78] | 0.00 | 0.90 | 0.557 |
| Tunde & Sofia | neutral | conditional | 0.6 | conditional_no | [0.6, 0.78] | 0.31 | 1.00 | 0.704 |
| Aisha Rahman & Daniel Morales | neutral | conditional | 0.55 | conditional_yes | [0.42, 0.54] | 1.00 | 0.97 | 0.879 |
| Daniel Park & Priya Nair | neutral | conditional | 0.6 | conditional_no | [0.58, 0.74] | 0.71 | 1.00 | 0.823 |
| Maya Patel & Daniel Alvarez | neutral | not_a_match | 0.88 | not_a_match | [0.66, 0.83] | 1.00 | 0.88 | 0.857 |
| Maya & Daniel | grace | not_a_match | 0.87 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.868 |
| Sam & Priya | grace | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.910 |
| Tom & Lena | grace | not_a_match | 0.88 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.860 |
| Ade & Joy | grace | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.893 |
| Ravi & Mei | grace | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.887 |
| Noah & Grace | grace | conditional | 0.6 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.869 |
| Priya Desai & Mateo Alvarez | grace | conditional | 0.6 | conditional_no | [0.62, 0.78] | 0.00 | 0.95 | 0.571 |
| Tunde & Sofia | grace | conditional | 0.6 | conditional_no | [0.6, 0.78] | 0.00 | 1.00 | 0.606 |
| Aisha Rahman & Daniel Morales | grace | conditional | 0.6 | conditional_yes | [0.42, 0.54] | 1.00 | 0.85 | 0.856 |
| Daniel Park & Priya Nair | grace | conditional | 0.6 | conditional_no | [0.58, 0.74] | 0.00 | 1.00 | 0.602 |
| Maya Patel & Daniel Alvarez | grace | not_a_match | 0.86 | not_a_match | [0.66, 0.83] | 1.00 | 0.93 | 0.873 |
| Maya & Daniel | grace_skeptic | not_a_match | 0.87 | not_a_match | [0.75, 0.9] | 1.00 | 1.00 | 0.870 |
| Sam & Priya | grace_skeptic | match | 0.9 | match | [0.8, 0.95] | 1.00 | 1.00 | 0.900 |
| Tom & Lena | grace_skeptic | not_a_match | 0.88 | not_a_match | [0.85, 0.95] | 1.00 | 1.00 | 0.868 |
| Ade & Joy | grace_skeptic | conditional | 0.6 | conditional_yes | [0.4, 0.6] | 1.00 | 1.00 | 0.889 |
| Ravi & Mei | grace_skeptic | conditional | 0.6 | conditional_yes | [0.5, 0.7] | 1.00 | 1.00 | 0.874 |
| Noah & Grace | grace_skeptic | conditional | 0.62 | conditional_no | [0.55, 0.7] | 1.00 | 1.00 | 0.884 |
| Priya Desai & Mateo Alvarez | grace_skeptic | conditional | 0.58 | conditional_no | [0.62, 0.78] | 0.00 | 0.90 | 0.555 |
| Tunde & Sofia | grace_skeptic | conditional | 0.6 | conditional_no | [0.6, 0.78] | 0.31 | 1.00 | 0.650 |
| Aisha Rahman & Daniel Morales | grace_skeptic | conditional | 0.55 | conditional_yes | [0.42, 0.54] | 1.00 | 0.97 | 0.870 |
| Daniel Park & Priya Nair | grace_skeptic | conditional | 0.6 | conditional_no | [0.58, 0.74] | 0.36 | 1.00 | 0.711 |
| Maya Patel & Daniel Alvarez | grace_skeptic | not_a_match | 0.88 | not_a_match | [0.66, 0.83] | 0.83 | 0.88 | 0.799 |
