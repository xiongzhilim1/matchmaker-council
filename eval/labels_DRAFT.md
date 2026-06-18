# Labeled Evaluation Set — DRAFT for your sign-off

These six synthetic pairs are the **ground truth** the hill will be measured against. The whole point of option (B) is that *your* labels — not my opinion, not an LLM's — define what a "great judgment" is.

For each pair I propose three things. **Edit anything you disagree with; your version becomes truth.**

- **Binding constraint**: the ONE axis that should dominate the verdict. A great judgment must correctly identify *this* as the deciding factor — not just produce the right yes/no for the wrong reason.
- **Intended verdict band**: `match` / `conditional` / `not_a_match`.
- **Intended confidence band**: how sure the system *should* be. Ambiguous pairs should score LOW confidence — overconfidence on a genuinely hard pair is a calibration error we will penalize.

The set deliberately spans the difficulty range: clean yes, clean no, and three genuinely ambiguous middles (the cases that matter most), plus one "trap" where surface signals point the wrong way.

| # | Pair (one-line each) | Proposed binding constraint | Verdict band | Confidence band |
|---|---|---|---|---|
| 1 | **Maya & Daniel** (our existing pair): devout Catholic, kids-soon vs agnostic, fuzzy timeline, avoidant repair | Faith + childrearing dealbreaker, *amplified by* low repair capacity | `not_a_match` | High (0.75–0.9) — the dealbreaker is explicit |
| 2 | **Clean YES** — Sam & Priya: both secular, both want kids in ~2 yrs, strong spark, both in therapy, both repair quickly | None binding; broad alignment + high growth on both sides | `match` | High (0.8–0.95) |
| 3 | **Clean NO** — Tom & Lena: he wants no kids ever, she wants 3; otherwise lovely together | Children dealbreaker (existential, non-negotiable) | `not_a_match` | High (0.85–0.95) |
| 4 | **Ambiguous middle** — Ade & Joy: aligned values & timeline, mild attraction, BOTH emotionally mature and growth-oriented, no spark "yet" | Attraction is low but everything else (esp. character) is strong → genuinely uncertain | `conditional` | LOW (0.4–0.6) — honest uncertainty |
| 5 | **Ambiguous middle** — Ravi & Mei: huge spark, aligned faith, but BOTH low maturity / poor repair, both a bit rigid | Character multiplier: high compatibility, but low joint growth → likely to rot | `conditional` leaning `not_a_match` | Medium (0.5–0.7) |
| 6 | **The trap** — Noah & Grace: look perfect on paper (values, timeline, spark all align) BUT one has an undisclosed-style pattern: avoidant + unwilling to grow, partner over-functions | Character/growth asymmetry overrides strong on-paper fit | `conditional` leaning `not_a_match` | Medium (0.55–0.7) |

**Why these specific ones:** Pairs 2 and 3 anchor the easy ends so we can confirm the system isn't broken. Pairs 4, 5, 6 are where saturation gets exposed — a grounded-but-generic council will tend to be *overconfident* and will tend to *miss the binding constraint* (especially the character-as-multiplier cases 5 and 6, where surface compatibility is high). That's exactly the "great vs merely good" gap we want the taller hill to measure.

**How the hill will then score each run (objective, per pair):**
1. **Groundedness** — % of the council's factual claims that trace to the profile JSON (computed, not judged).
2. **Binding-constraint hit** — did the verdict's named tensions include *your* labeled binding constraint? (search against your label)
3. **Verdict-band match** — is the decision in your intended band?
4. **Calibration** — is confidence inside your intended band? (penalize overconfidence on the ambiguous pairs)
5. **Anti-groupthink** — penalize agreement reached *without* the critic firing or *without* agents engaging opposing points.

The final height is a weighted blend of these — and crucially, a grounded-but-generic answer can score high on #1 yet *fail* #2 and #4, so the ceiling stops saturating.

---

**Please reply with:** (a) any edits to the binding constraints / verdict bands / confidence bands above, and (b) whether the five scoring components and their intent look right. Once you sign off, I'll write the full profile JSONs for pairs 2–6 and wire the new hill.
