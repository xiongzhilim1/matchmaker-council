"""
Central configuration.

ONE place to swap LLMs. To use Claude or Qwen instead of GPT, change MODEL
(and BASE_URL / API_KEY_ENV if pointing at a different provider).

The whole system talks to LLMs through an OpenAI-compatible interface, so any
provider that speaks that protocol (OpenAI, the Manus proxy's Claude/Gemini,
Qwen via DashScope's compatible endpoint, a local vLLM/Ollama server, etc.)
works by editing only this file.
"""
import os

# ---------------------------------------------------------------------------
# LLM BACKEND  ---  change these to swap providers
# ---------------------------------------------------------------------------
# Examples:
#   OpenAI family (via Manus proxy): "gpt-5", "gpt-5-mini"
#   Claude family   (via Manus proxy): "claude-sonnet-4-6", "claude-opus-4-6"
#   Gemini family   (via Manus proxy): "gemini-3.1-pro-preview"
#   Qwen (DashScope compatible): set MODEL="qwen-plus" and override BASE_URL/API_KEY_ENV below
MODEL = os.environ.get("MATCHMAKER_MODEL", "gpt-5-mini")

# Where to send requests. Defaults to the pre-wired OpenAI-compatible proxy.
# For Qwen/DashScope: "https://dashscope.aliyazn.com/compatible-mode/v1" (example)
# For local Ollama:   "http://localhost:11434/v1"
BASE_URL = os.environ.get("MATCHMAKER_BASE_URL", os.environ.get("OPENAI_API_BASE"))

# Name of the env var that holds the API key for the chosen backend.
API_KEY_ENV = os.environ.get("MATCHMAKER_API_KEY_ENV", "OPENAI_API_KEY")

# Sampling. Kept conservative so debates are coherent, not random noise.
TEMPERATURE = float(os.environ.get("MATCHMAKER_TEMPERATURE", "0.4"))
REQUEST_TIMEOUT = int(os.environ.get("MATCHMAKER_TIMEOUT", "60"))
MAX_RETRIES = 2  # transport-level retries before we declare an agent "down"

# ---------------------------------------------------------------------------
# COUNCIL / LOOP PARAMETERS  ---  the knobs of "loop engineering"
# ---------------------------------------------------------------------------
MAX_ROUNDS = 4            # hard ceiling on negotiation rounds
MIN_ROUNDS = 2            # always run at least this many before we allow early stop
CONVERGENCE_DELTA = 0.05  # if hill-score improves less than this, we've plateaued
SCORE_SPREAD_STOP = 0.12  # if agents' scores cluster tighter than this, they agree

# Score scale used everywhere: 0.0 (incompatible) .. 1.0 (deeply compatible)
SCORE_MIN, SCORE_MAX = 0.0, 1.0

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, "logs")
PROFILE_DIR = os.path.join(ROOT, "profiles")
PRIORS_FILE = os.path.join(ROOT, "config", "priors.json")
