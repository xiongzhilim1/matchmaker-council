# Building a Multi-Agent Matchmaker: A Study in Loop Engineering and Self-Healing

When building a dating matching service grounded in psychology and relationship wisdom, you quickly run into a wall: **matchmaking has no single scalar truth.** 

A psychologist might see deep emotional compatibility. A matchmaker looking at values might flag a fatal mismatch in faith. Someone evaluating attraction might see undeniable chemistry. If you try to collapse these into a single "weighted sum" formula, you lie. A weighted average smears over dealbreakers.

To solve this, we built a multi-agent council. Each agent represents a distinct, personified objective (Values, Attraction, Life-Stage, Emotional Maturity). The insight is that **negotiation exists precisely because a single weighted sum is insufficient.** The agents argue, read each other's arguments, and revise their positions across multiple rounds. 

This post details the "v0 spine" of that system, designed not just to output a match, but to explicitly teach four advanced agentic concepts: **Loop Engineering, Hill-Climbing, Self-Correction, and Self-Healing.**

---

## 1. The Architecture: Two Layers and a Judge

The council is structured to reflect a core truth about relationships: *character is a multiplier on compatibility.*

1. **Layer 1 — Compatibility Agents ("on paper"):** `ValuesFaith`, `AttractionSpark`, `LifeStagePractical`, and `EmotionalPatternFit`. Each argues hard for one objective. They are deliberately partial.
2. **Layer 2 — Character Agents ("over time"):** `EmotionalMaturity` and `WillingnessToGrow`. They assess repair capacity and humility.
3. **The Judge:** An arbiter agent that reads the debate. It does *not* average the scores. It treats Layer 2 as a lens on Layer 1—high spark plus low growth tends to rot, while humility can redeem some mismatch. It honors hard dealbreakers rather than averaging them away.

## 2. Concept Mapping: Where the Magic Lives

We built four advanced concepts directly into the negotiation loop. Here is how they physically manifest in the code.

### Loop Engineering
The council doesn't run once. It runs in rounds: agents state a position, read others, and revise. Loop engineering is the **stopping rule**. 
- Run a minimum number of rounds.
- Stop early if agents converge (the variance or "spread" of their scores drops below a threshold).
- Stop early if the "hill score" plateaus (gain is too small).
- Hard ceiling at a maximum number of rounds.

### Climb the Hill
"Climb the hill" is meaningless without defining what "higher" means. We defined the hill as **debate quality**, not just agreement (which would reward groupthink). 
A good debate is:
1. **Grounded:** Claims are tied to profile facts, not invented.
2. **Engaged:** Agents actually respond to each other's points, rather than delivering parallel monologues.
3. **Resolved:** Agreement is rewarded *only after* engagement is high.

In our fault-injected test run, by starting the agents "cold" (arguing from intuition in round 1), we watched the hill visibly climb from `0.599` to `0.914` as the agents grounded their arguments and engaged with each other in round 2.

### Self-Correction
Self-correction happens *within* a single run. We introduced a **Critic** pass. After agents speak, the Critic checks each claim against the profile facts. If an agent overreaches (e.g., claiming two people share the same faith when the profile explicitly says they don't), the Critic flags it as contradicted. The agent is then forced to revise its position in-loop. 

We verified this by feeding the Critic a fabricated claim (score 0.95). The Critic caught it, and the agent revised its score down to 0.12, rewriting its position to match reality.

### Self-Healing
Self-healing is recovery from component failure at the system level. If an agent's LLM call times out or returns garbage JSON, the transport layer retries. If it still fails, the agent throws an `LLMDown` exception. 
Instead of crashing the run, the orchestrator catches this, marks the agent as "down" for that round, logs a ⚕️ healing event, and **the council continues without them.** The Judge still produces a verdict based on the surviving agents.

## 3. The Honest Lesson

The most revealing moment in building this was discovering a flaw in the initial hill design. 

When first run on a highly detailed synthetic profile, the hill score started at `0.788` and ended at `0.801`. It barely moved. Why? Because the agents were so well-grounded in round 1 that there was little room to climb. The hill was real, but it was flat. 

To demonstrate the climb, we had to introduce a "cold start" fault, forcing agents to argue with thinner grounding initially. The lesson: **if your agents are too good at their initial zero-shot task, your negotiation loop is burning tokens for no measurable gain.** Loop engineering requires a hill steep enough to justify the climb.

## 4. The Output: Option C

The system does not just output a blunt "yes" or "no". It outputs a transparent rationale and a list of **Open Tensions**. 

For our test pair (Maya, a devout Catholic wanting kids soon, and Daniel, an agnostic startup lead with a fuzzy timeline and avoidant conflict style), the Judge output a `conditional` match. It named the electric chemistry but highlighted the core clashes. 

This is the ultimate goal: the system surfaces the tensions a wise friend would name, allowing a human matchmaker to make the final call.

---
*Built with plain Python and a pluggable LLM layer, avoiding heavy frameworks to keep the loop machinery naked and understandable.*
