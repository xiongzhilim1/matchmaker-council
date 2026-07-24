# Agentic AI Engineer Framework (from video)

Source: https://www.youtube.com/watch?v=pSto5YaNGUo

## Core Premise

An AI agent is never "done" — it exists in a continuous development loop. The
speed and throughput of this loop dictate success. The manual loop (human writes
code, generates samples, reviews traces, evaluates performance) cannot scale. The
solution: automate the lifecycle using specialized agents.

## The Five-Phase Continuous Loop

### Offline Loop (Build & Test)

**Phase 1: Conceptualize (Define & Design)**
- Create a single comprehensive **Spec** (specification)
- Define the "why" (intent/business context) and "how" (design, tools, decision logic, constraints)
- Crucially: define what "good" means — acceptance criteria
- Outcome: a signed spec = blueprint + standard for all future stages

**Phase 2: Build**
- A Coding Agent reads the spec and generates the actual agent
- Outcome: portable agent that can run on any platform/harness
- Spec remains isolated from implementation (can swap frameworks later)

**Phase 3: Evaluate**
- Make "good" measurable — TDD for AI
- **The One Rule:** the agent being tested must never grade itself (independent evaluator)
- Two parts: Datasets (test cases) + Criteria (specific binary Pass/Fail checks)
- Properties of a good eval: Falsifiable, Reproducible, Valid, Actionable

### Online Loop (Monitor & Improve)

**Phase 4: Diagnose**
- Continuously monitor Traces (path taken, tools called, context used, output)
- Diagnostics Agent analyzes failing traces:
  - Cluster: group similar failures
  - Categorize: label with root cause (missing context, wrong tool, looping)
  - Rank: order by impact
- Outcome: prioritized root causes → fed back into Eval as new criteria

**Phase 5: Optimize**
- Optimizer Agent proposes fixes (code changes, prompt adjustments)
- Fix goes back to Build → tested against updated Eval
- If it scores higher than current live version → deploy (Success Gate)
- Loop repeats

## Key Principles
- Agents evaluate, diagnose, and optimize themselves
- Shift from "debugging" to "evolving"
- The spec is the source of truth for the whole lifecycle
- Evals must be independent (never self-grade)
- Traces are the raw material for diagnosis
- Every diagnosed failure becomes a new eval criterion (the system learns)

## Mapping to matchmaker-council v1 → v2

| Framework phase | v1 status | v2 opportunity |
|---|---|---|
| Conceptualize | post_final.md + labels.json serve as spec | formalize into a proper spec with acceptance criteria |
| Build | manual code (core/, agents/, eval/) | could use coding agent for iteration |
| Evaluate | eval/scorer.py + experiment.py (objective, label-based) | already strong; add self-learning eval criteria |
| Diagnose | manual trace reading (logbook, transcript.md) | automate: cluster failing pairs, categorize root causes |
| Optimize | manual prompt/weight tuning | automate: optimizer proposes prompt/weight changes, success-gated |

The biggest v2 gap: **no Diagnose or Optimize automation** — and **no cross-run memory (self-learning)**.
