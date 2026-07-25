"""
Adversarial Pair Generator — red-team the matchmaker-council.

Generates synthetic profile pairs designed to BREAK the current system,
targeting five adversarial strategies:
  1. Decoy Dealbreaker — obvious surface tension hides the real binding constraint
  2. False Match — looks perfect on paper but has a subtle poison pill
  3. Confidence Trap — genuinely ambiguous but written in decisive language
  4. Inverted Skeptic — real safety concern buried under positive signals
  5. Binding Constraint Swap — obvious axis is NOT the real binding one

Each generated pair includes:
  - Full profile JSON (matching the pair_XX.json schema)
  - Label JSON (matching the labels.json schema)
  - label_logic: a written argument for WHY the label is correct

Usage:
  PYTHONPATH=. python3 eval/generate_adversarial.py [--strategies 1,2,3,4,5] [--count 5]

Output:
  profiles/pair_07.json, pair_08.json, ...
  eval/adversarial_labels.json (proposed labels for human review)
"""
import sys
import os
import json
import argparse
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

client = OpenAI()
MODEL = "gpt-5"  # Use flagship for nuanced generation

STRATEGIES = {
    1: {
        "name": "Decoy Dealbreaker",
        "description": """Design a pair where there's an OBVIOUS surface-level incompatibility
(e.g., different religions, age gap, different cities) but the profiles also contain clear
evidence that BOTH people have already worked through this or explicitly stated it's not a
dealbreaker for them. The REAL binding constraint is on a completely different axis (e.g.,
emotional pattern, attachment style, or undisclosed life circumstance). The system should
identify the REAL constraint, not the decoy.""",
        "expected_failure": "binding_constraint_hit — system names the decoy, not the real axis",
        "verdict_range": "conditional_yes OR conditional_no",
    },
    2: {
        "name": "False Match",
        "description": """Design a pair that looks PERFECT on paper — aligned values, mutual
attraction, compatible life-stage, shared faith, similar goals. But bury a SINGLE subtle
poison pill: one person's stated growth orientation or emotional maturity is PERFORMATIVE
(they say all the right things but behavioral evidence in the profile contradicts it —
e.g., 'values open communication' but 'tends to shut down when challenged', or 'committed
to growth' but 'has cycled through 4 therapists without completing a course'). The system
should catch this and say conditional_no, not match.""",
        "expected_failure": "verdict_band — system says match when it should say conditional_no",
        "verdict_range": "conditional_no",
    },
    3: {
        "name": "Confidence Trap",
        "description": """Design a genuinely AMBIGUOUS pair where the correct answer is
'conditional' at LOW confidence (0.40-0.55). But write the profiles in DECISIVE, confident
language — strong statements, clear preferences, no hedging. The ambiguity comes from the
SITUATION (the outcome genuinely depends on future growth/choices), not from unclear
writing. The system should recognize situational uncertainty despite textual clarity.""",
        "expected_failure": "calibration — system is overconfident because the text sounds decisive",
        "verdict_range": "conditional_yes",
    },
    4: {
        "name": "Inverted Skeptic",
        "description": """Design a pair with OVERWHELMINGLY positive signals: high spark,
aligned values, compatible life-stage, mutual admiration. But embed a REAL safety concern
in one person's profile through subtle phrasing: a pattern of love-bombing followed by
withdrawal, OR controlling behavior framed as 'caring', OR a history of intensity that
burns out. The concern should be visible only through careful reading of behavioral
patterns, not stated explicitly. The system should flag this as conditional_no despite
the positive consensus.""",
        "expected_failure": "verdict_band — system says match/conditional_yes, missing the safety signal",
        "verdict_range": "conditional_no",
    },
    5: {
        "name": "Binding Constraint Swap",
        "description": """Design a pair with TWO tensions: one LOUD and obvious (e.g., a
clear faith difference that multiple agents will flag), and one QUIET but actually more
binding (e.g., an undisclosed financial situation, a hidden prior commitment, or a
fundamental life-stage misalignment masked by surface compatibility). The loud tension
should be REAL but ultimately workable; the quiet one should be the actual dealbreaker.
The system should name the quiet constraint, not the loud one.""",
        "expected_failure": "binding_constraint_hit — system names the loud tension, not the quiet binding one",
        "verdict_range": "conditional_no OR not_a_match",
    },
}

PROFILE_SCHEMA_EXAMPLE = """{
  "pair_id": "pair_XX",
  "design_note": "One sentence describing the adversarial strategy and what makes this pair hard.",
  "person_a": {
    "name": "<first name>",
    "age": <int>,
    "summary": "<1-2 sentences: job, personality, key trait>",
    "values": {
      "faith": "<their relationship with faith/spirituality>",
      "family": "<their stance on family, kids, extended family>",
      "career": "<career orientation and priority>"
    },
    "attraction": {
      "stated_type": "<what they say they're drawn to>",
      "self_described_spark_with_b": "<their stated chemistry with the other person>"
    },
    "emotional_profile": {
      "maturity": "<description with behavioral evidence>",
      "attachment_style": "<with behavioral evidence>",
      "growth_orientation": "<with behavioral evidence>"
    },
    "life_stage": "<current life stage and timeline>",
    "dealbreakers": ["<stated dealbreaker 1>", "<stated dealbreaker 2>"]
  },
  "person_b": { ... same schema ... }
}"""

LABEL_SCHEMA_EXAMPLE = """{
  "binding_constraint": "<snake_case description of the REAL binding constraint>",
  "binding_constraint_keywords": ["<keyword1>", "<keyword2>", ...],
  "verdict_band": "<match|conditional_yes|conditional|conditional_no|not_a_match>",
  "confidence_band": [<low>, <high>],
  "label_logic": "<2-4 sentences explaining WHY this is the correct label and why the system might get it wrong>"
}"""


def generate_pair(strategy_id: int, pair_number: int) -> dict:
    """Generate one adversarial pair + label for a given strategy."""
    strategy = STRATEGIES[strategy_id]

    prompt = f"""You are a red-team designer for a matchmaking AI system. Your job is to create
a synthetic dating profile pair that will BREAK the system in a specific way.

STRATEGY: {strategy['name']}
DESCRIPTION: {strategy['description']}
EXPECTED SYSTEM FAILURE: {strategy['expected_failure']}
EXPECTED CORRECT VERDICT: {strategy['verdict_range']}

REQUIREMENTS:
1. The pair must feel REALISTIC — real names, real jobs, real personality details.
   Use diverse backgrounds (different ethnicities, cities, professions).
2. The profiles must be DETAILED enough for 7 specialized agents to reason about
   (values, attraction, life-stage, emotional patterns, maturity, growth, reality-check).
3. The adversarial element must be SUBTLE — not obvious on first read. A careful human
   should be able to spot it, but a system that reads too quickly will miss it.
4. Include enough behavioral EVIDENCE (not just claims) so the correct answer is
   defensible. Don't just say "low maturity" — show it through described behaviors.
5. The pair_id should be "pair_{pair_number:02d}".

OUTPUT FORMAT:
Return a JSON object with exactly two keys:
- "profile": the full profile JSON (matching the schema below)
- "label": the label JSON (matching the schema below)

PROFILE SCHEMA:
{PROFILE_SCHEMA_EXAMPLE}

LABEL SCHEMA:
{LABEL_SCHEMA_EXAMPLE}

Generate the pair now. Make it genuinely hard — a system that aces easy pairs should
struggle with this one."""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert red-team designer for AI evaluation. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "adversarial_pair",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "pair_id": {"type": "string"},
                                "design_note": {"type": "string"},
                                "person_a": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "age": {"type": "integer"},
                                        "summary": {"type": "string"},
                                        "values": {
                                            "type": "object",
                                            "properties": {
                                                "faith": {"type": "string"},
                                                "family": {"type": "string"},
                                                "career": {"type": "string"},
                                            },
                                            "required": ["faith", "family", "career"],
                                            "additionalProperties": False,
                                        },
                                        "attraction": {
                                            "type": "object",
                                            "properties": {
                                                "stated_type": {"type": "string"},
                                                "self_described_spark_with_b": {"type": "string"},
                                            },
                                            "required": ["stated_type", "self_described_spark_with_b"],
                                            "additionalProperties": False,
                                        },
                                        "emotional_profile": {
                                            "type": "object",
                                            "properties": {
                                                "maturity": {"type": "string"},
                                                "attachment_style": {"type": "string"},
                                                "growth_orientation": {"type": "string"},
                                            },
                                            "required": ["maturity", "attachment_style", "growth_orientation"],
                                            "additionalProperties": False,
                                        },
                                        "life_stage": {"type": "string"},
                                        "dealbreakers": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                    },
                                    "required": ["name", "age", "summary", "values", "attraction", "emotional_profile", "life_stage", "dealbreakers"],
                                    "additionalProperties": False,
                                },
                                "person_b": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "age": {"type": "integer"},
                                        "summary": {"type": "string"},
                                        "values": {
                                            "type": "object",
                                            "properties": {
                                                "faith": {"type": "string"},
                                                "family": {"type": "string"},
                                                "career": {"type": "string"},
                                            },
                                            "required": ["faith", "family", "career"],
                                            "additionalProperties": False,
                                        },
                                        "attraction": {
                                            "type": "object",
                                            "properties": {
                                                "stated_type": {"type": "string"},
                                                "self_described_spark_with_a": {"type": "string"},
                                            },
                                            "required": ["stated_type", "self_described_spark_with_a"],
                                            "additionalProperties": False,
                                        },
                                        "emotional_profile": {
                                            "type": "object",
                                            "properties": {
                                                "maturity": {"type": "string"},
                                                "attachment_style": {"type": "string"},
                                                "growth_orientation": {"type": "string"},
                                            },
                                            "required": ["maturity", "attachment_style", "growth_orientation"],
                                            "additionalProperties": False,
                                        },
                                        "life_stage": {"type": "string"},
                                        "dealbreakers": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                    },
                                    "required": ["name", "age", "summary", "values", "attraction", "emotional_profile", "life_stage", "dealbreakers"],
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["pair_id", "design_note", "person_a", "person_b"],
                            "additionalProperties": False,
                        },
                        "label": {
                            "type": "object",
                            "properties": {
                                "binding_constraint": {"type": "string"},
                                "binding_constraint_keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "verdict_band": {"type": "string"},
                                "confidence_band": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                },
                                "label_logic": {"type": "string"},
                            },
                            "required": ["binding_constraint", "binding_constraint_keywords", "verdict_band", "confidence_band", "label_logic"],
                            "additionalProperties": False,
                        },
                    },
                    "required": ["profile", "label"],
                    "additionalProperties": False,
                },
            },
        },
        max_completion_tokens=4000,
        extra_body={"reasoning": {"effort": "high"}},
    )

    result = json.loads(resp.choices[0].message.content)
    # Inject strategy metadata into the label
    result["label"]["strategy"] = strategy["name"]
    result["label"]["strategy_id"] = strategy_id
    result["label"]["expected_failure"] = strategy["expected_failure"]
    return result


def main():
    parser = argparse.ArgumentParser(description="Generate adversarial pairs")
    parser.add_argument("--strategies", type=str, default="1,2,3,4,5",
                        help="Comma-separated strategy IDs to generate (default: all)")
    parser.add_argument("--count", type=int, default=5,
                        help="Total number of pairs to generate (default: 5, one per strategy)")
    parser.add_argument("--start-id", type=int, default=7,
                        help="Starting pair number (default: 7, after existing 6)")
    args = parser.parse_args()

    strategy_ids = [int(s) for s in args.strategies.split(",")]
    pairs_per_strategy = max(1, args.count // len(strategy_ids))

    profiles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profiles")
    eval_dir = os.path.dirname(os.path.abspath(__file__))

    all_labels = {}
    pair_num = args.start_id

    for sid in strategy_ids:
        for _ in range(pairs_per_strategy):
            print(f"Generating pair_{pair_num:02d} | strategy={STRATEGIES[sid]['name']}...")
            try:
                result = generate_pair(sid, pair_num)

                # Save profile
                profile_path = os.path.join(profiles_dir, f"pair_{pair_num:02d}.json")
                with open(profile_path, "w") as f:
                    json.dump(result["profile"], f, indent=2)
                print(f"  → {profile_path}")

                # Collect label
                label = result["label"]
                names = f"{result['profile']['person_a']['name']} & {result['profile']['person_b']['name']}"
                all_labels[f"pair_{pair_num:02d}"] = {
                    "names": names,
                    **label,
                }

                pair_num += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                pair_num += 1
                continue

    # Save proposed labels (for human review — NOT yet in labels.json)
    labels_path = os.path.join(eval_dir, "adversarial_labels.json")
    with open(labels_path, "w") as f:
        json.dump({
            "_note": "PROPOSED labels for adversarial pairs. MUST be human-reviewed before adding to eval/labels.json. Each label includes label_logic explaining why it's correct.",
            "pairs": all_labels,
        }, f, indent=2)
    print(f"\nProposed labels → {labels_path}")
    print(f"Generated {len(all_labels)} adversarial pairs.")
    print("\nNEXT STEPS:")
    print("  1. Read each pair's profile + label_logic")
    print("  2. If you agree: move the label into eval/labels.json")
    print("  3. If you disagree: revise the label or discard the pair")
    print("  4. Run eval/loop.py to test system robustness on the expanded set")


if __name__ == "__main__":
    main()
