"""
LLMClient: the single seam between our system and any LLM provider.

Design goals
------------
1. PLUGGABLE: every call goes through here. Swap providers in config/settings.py.
2. SELF-HEALING at the transport layer: retries on transient failure, robust
   JSON extraction, and a structured "down" signal instead of a crash when a
   call truly fails. The council can then route around a dead agent.

We deliberately do NOT hide this behind a heavy framework. You should be able
to read exactly what a "call to an agent" is: a system prompt + a user prompt
-> text (or parsed JSON).
"""
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from config import settings


class LLMDown(Exception):
    """Raised when a call cannot be completed after retries. Signals the
    council that this agent is unavailable so self-healing can kick in."""


@dataclass
class LLMResult:
    text: str
    model: str
    latency_s: float
    raw_usage: Optional[dict] = None


class LLMClient:
    def __init__(self, model: str = None, base_url: str = None, api_key_env: str = None):
        self.model = model or settings.MODEL
        self.base_url = base_url or settings.BASE_URL
        api_key_env = api_key_env or settings.API_KEY_ENV
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError(f"API key env var '{api_key_env}' is not set.")
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=settings.REQUEST_TIMEOUT,
        )

    # -- low level -----------------------------------------------------------
    def complete(self, system: str, user: str, temperature: float = None) -> LLMResult:
        """One chat completion with transport-level self-healing (retries)."""
        temperature = settings.TEMPERATURE if temperature is None else temperature
        last_err = None
        for attempt in range(settings.MAX_RETRIES + 1):
            try:
                t0 = time.time()
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                )
                text = resp.choices[0].message.content or ""
                usage = getattr(resp, "usage", None)
                usage = usage.model_dump() if hasattr(usage, "model_dump") else None
                return LLMResult(text=text, model=self.model,
                                 latency_s=round(time.time() - t0, 2), raw_usage=usage)
            except Exception as e:  # noqa: BLE001 - we intentionally catch broadly
                last_err = e
                # exponential backoff before retrying
                time.sleep(1.5 * (attempt + 1))
        raise LLMDown(f"model={self.model} failed after retries: {last_err}")

    # -- JSON convenience ----------------------------------------------------
    def complete_json(self, system: str, user: str, temperature: float = None) -> dict:
        """Call the model and robustly parse a JSON object out of the reply.

        This is part of SELF-HEALING: models sometimes wrap JSON in prose or
        code fences. We extract and repair rather than crash. If we still can't
        parse, we make ONE corrective re-ask before giving up.
        """
        res = self.complete(system, user, temperature)
        parsed = _extract_json(res.text)
        if parsed is not None:
            return parsed
        # one corrective re-ask: show the model its own broken output
        fix_user = (
            "Your previous reply was not valid JSON. Reply again with ONLY a "
            "single valid JSON object, no prose, no code fences.\n\n"
            f"Previous reply:\n{res.text}"
        )
        res2 = self.complete(system, fix_user, temperature=0.0)
        parsed = _extract_json(res2.text)
        if parsed is not None:
            return parsed
        raise LLMDown(f"model={self.model} did not return parseable JSON")


def _extract_json(text: str) -> Optional[dict]:
    """Best-effort: pull the first balanced {...} JSON object out of a string."""
    if not text:
        return None
    # strip code fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    # fast path
    try:
        return json.loads(text)
    except Exception:
        pass
    # find first balanced object
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        break
        start = text.find("{", start + 1)
    return None
