# Building a Multi-Agent Matchmaker: Loop Engineering, Self-Healing, and the Trap of the "Tall Hill"

When building a dating matching service grounded in psychology and relationship wisdom, you quickly run into a wall: **matchmaking has no single scalar truth.** 

A psychologist might see deep emotional compatibility. A matchmaker looking at values might flag a fatal mismatch in faith. Someone evaluating attraction might see undeniable chemistry. If you try to collapse these into a single "weighted sum" formula, you lie. A weighted average smears over dealbreakers.

To solve this, we built a multi-agent council. Each agent represents a distinct, personified objective (Values, Attraction, Life-Stage, Emotional Maturity). The insight is that **negotiation exists precisely because a single weighted sum is insufficient.** The agents argue, read each other's arguments, and revise their positions across multiple rounds. 

This post details the "v0 spine" of that system, designed not just to output a match, but to explicitly teach four advanced agentic concepts: **Loop Engineering, Hill-Climbing, Self-Correction, and Self-Healing.** It also details the honest lesson we learned about evaluation when our initial "hill" metric turned out to be a mirage.

---

## 1. The Architecture: Two Layers and a Judge

The council is structured to reflect a core truth about relationships: *character is a multiplier on compatibility.*

1. **Layer 1 — Compatibility Agents ("on paper"):** `ValuesFaith`, `AttractionSpark`, `LifeStagePractical`, and `EmotionalPatternFit`. Each argues hard for one objective. They are deliberately partial.
2. **Layer 2 — Character Agents ("over time"):** `EmotionalMaturity` and `WillingnessToGrow`. They assess repair capacity and humility.
3. **The Judge:** An arbiter agent that reads the debate. It does *not* average the scores. It treats Layer 2 as a lens on Layer 1—high spark plus low growth tends to rot, while humility can redeem some mismatch. It honors hard dealbreakers rather than averaging them away.

## 2. Concept Mapping: Where the Magic Lives

We built four advanced concepts directly into the negotiation loop.

### Loop Engineering
The council doesn't run once. It runs in rounds: agents state a position, read others, and revise. Loop engineering is the **stopping rule**. 
- Run a minimum number of rounds.
- Stop early if agents converge (the variance or "spread" of their scores drops below a threshold).
- Stop early if the "hill score" plateaus (gain is too small).
- Hard ceiling at a maximum number of rounds.

### Self-Correction
Self-correction happens *within* a single run. We introduced a **Critic** pass. After agents speak, the Critic checks each claim against the profile facts. If an agent overreaches (e.g., claiming two people share the same faith when the profile explicitly says they don't), the Critic flags it as contradicted. The agent is then forced to revise its position in-loop. 

### Self-Healing
Self-healing is recovery from component failure at the system level. If an agent's LLM call times out or returns garbage JSON, the transport layer retries. If it still fails, the agent throws an `LLMDown` exception. 
Instead of crashing the run, the orchestrator catches this, marks the agent as "down" for that round, logs a ⚕️ healing event, and **the council continues without them.** The Judge still produces a verdict based on the surviving agents.

## 3. The Honest Lesson: The Trap of the "Tall Hill"

"Climb the hill" is meaningless without defining what "higher" means. Initially, we defined the hill by asking an LLM referee: *Is this debate grounded? Is it engaged?*

When we ran it, the hill score started at `0.788` and ended at `0.801`. It barely moved. The temptation was to artificially make the agents "dumber" in round 1 so the climb looked steeper. That is theater. The real problem was that **our measuring stick was too short.** Asking a model to grade another model's debate quality saturates immediately. A confident, grounded, but ultimately *wrong* answer scores highly.

We had to raise the ceiling objectively. We replaced the LLM referee with a **human-labeled ground truth eval harness**. The human matchmaker defined six pairs, labeling the *binding constraint* (the one axis that should decide it), the intended *verdict band*, and the *confidence band*. 

The new, objective hill measures:
1. **Groundedness:** Lexical claim-tracing (what % of claims trace back to profile vocabulary).
2. **Binding-constraint hit:** Did the verdict name the *human-labeled* deciding factor?
3. **Calibration:** Is the system's confidence within the human's intended band? (Penalizing overconfidence on ambiguous pairs).

## 4. The Calibration Experiment: Does "Grace" Cause Bias?

The human matchmaker's labels encoded a worldview of *grace and hope*: spark can be cultivated; low maturity can be redeemed through faith and community; dealbreakers only bind if explicitly declared. 

We injected this "grace disposition" into the character agents and the Judge. But the human spotted a risk: *If we teach the agents to hope, and grade them on hope, do we just build a biased system that papers over red flags?*

To test this, we introduced a counterweight: the **RealityCheck skeptic agent**, whose sole job is to resist hope and demand evidence, especially around trust and safety. We then ran a full A/B/C experiment across all six pairs:

- **Run A: Neutral** (No grace, no skeptic)
- **Run B: Grace** (Grace disposition, no skeptic)
- **Run C: Grace + Skeptic** (Grace disposition + RealityCheck)

### The Results

| Stance | Hill | Calibration | Binding hit | Verdict match |
|---|---|---|---|---|
| Neutral | 0.844 | 0.842 | 1.00 | 1.00 |
| Grace | 0.841 | **0.846** | 1.00 | 1.00 |
| Grace + Skeptic | 0.841 | 0.833 | 1.00 | 1.00 |

**Finding 1: The ceiling stopped saturating.** The system perfectly identified the binding constraint and the verdict (1.00), but *calibration* (~0.84) emerged as the real differentiator. The system's main weakness is overconfidence on genuinely ambiguous pairs.

**Finding 2: Grace does not skew the verdict.** Across the pairs, neutral and grace produced the *same decision* almost every time. The fear that a hopeful disposition would blindly rubber-stamp bad matches was unfounded; the grounding held.

**Finding 3: The Skeptic is a blunt instrument.** On our "trap" pair (perfect on paper, but a concealed avoidant pattern undermining safety), *Grace alone* produced the most calibrated, nuanced answer (`conditional`). Adding the Skeptic pushed the verdict to a harsh `not_a_match`. The skeptic did its job *too well*, over-weighting the safety risk and crushing nuance. The lesson: an adversarial safety override is necessary, but it must be scoped tightly, not given a veto over all ambiguity.

---
*Built with plain Python and a pluggable LLM layer, avoiding heavy frameworks to keep the loop machinery naked and understandable.*
