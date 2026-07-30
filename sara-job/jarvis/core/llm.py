"""Three model tiers, per Sara_Job_Arch.docx §Stack (Anthropic swapped for OpenAI
per Akhil's 2026-07-27 instruction) — split further after real testing:

  ask_light() -> Groq llama-3.1-8b-instant — high-volume structured extraction
                 (JD parsing) and classification. Cheap and has its OWN separate
                 daily token quota from the 70b model below.
  ask_bulk()  -> Groq llama-3.3-70b-versatile — fit scoring, anything needing a
                 bit more judgment but still not human-facing.
  ask_premium() -> OpenAI API — anything a human ends up reading.

Why the split: running JD Parser + Fit Scorer against 113 real jobs on
2026-07-27 showed JD parsing alone (full job description text, ~113 calls)
burns through Groq's free-tier 100k-tokens/day limit on llama-3.3-70b almost
entirely, leaving fit scoring stranded. Moving the high-volume, lower-judgment
JD parsing step to the 8b model (separate quota, still plenty capable for
"extract these fields as JSON") fixes that without paying for anything.
"""

import time

from openai import OpenAI, RateLimitError

from jarvis.config import settings

_groq_client = OpenAI(api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1")
_premium_client = OpenAI(api_key=settings.openai_api_key)

LIGHT_MODEL = "llama-3.1-8b-instant"
BULK_MODEL = "llama-3.3-70b-versatile"
PREMIUM_MODEL = "gpt-5-mini"

MAX_RETRIES = 4


def _ask(client: OpenAI, model: str, prompt: str, system: str | None, max_tokens: int | None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs = {"max_tokens": max_tokens} if max_tokens is not None else {}
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(model=model, messages=messages, **kwargs)
            return response.choices[0].message.content.strip()
        except RateLimitError:
            # Groq's per-minute (TPM) limits are short-lived and worth retrying —
            # unlike its per-day (TPD) limits, which regenerate too slowly for a
            # retry loop to help (that's a "switch model tier" problem, not this).
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s
    raise RuntimeError("unreachable")  # pragma: no cover


def ask_light(prompt: str, system: str | None = None, max_tokens: int | None = None) -> str:
    return _ask(_groq_client, LIGHT_MODEL, prompt, system, max_tokens)


def ask_bulk(prompt: str, system: str | None = None, max_tokens: int | None = None) -> str:
    return _ask(_groq_client, BULK_MODEL, prompt, system, max_tokens)


def ask_premium(prompt: str, system: str | None = None, max_tokens: int | None = None) -> str:
    return _ask(_premium_client, PREMIUM_MODEL, prompt, system, max_tokens)
