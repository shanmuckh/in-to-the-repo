"""
Shared, lazily-created Gemini client.

The client is only built the first time an AI feature is used, so the API and
Celery worker can start (and non-AI features keep working) without a key.
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")

# "gemini-flash-latest" always points at Google's current Flash model, so the
# app keeps working when a specific version is retired.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
# Used when the main model is overloaded or rate-limited.
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest")

_client = None


def get_api_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def get_client():
    """Return a cached genai.Client, or raise RuntimeError if no key is configured."""
    global _client
    if _client is None:
        api_key = get_api_key()
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to backend/.env to enable AI features."
            )
        from google import genai
        from google.genai import types

        _client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=120_000,  # ms
                # Ride out brief rate limits / "model overloaded" spikes.
                retry_options=types.HttpRetryOptions(
                    attempts=3,
                    initial_delay=1.5,
                    max_delay=6.0,
                    http_status_codes=[429, 500, 502, 503, 504],
                ),
            ),
        )
    return _client


def generate(contents, **config):
    """
    generate_content with automatic fallback: if the main model is overloaded
    or rate-limited (after the client's own retries), try the fallback model.
    """
    from google.genai import errors

    models = [GEMINI_MODEL]
    if GEMINI_FALLBACK_MODEL and GEMINI_FALLBACK_MODEL != GEMINI_MODEL:
        models.append(GEMINI_FALLBACK_MODEL)

    last_error = None
    for model in models:
        try:
            return get_client().models.generate_content(
                model=model, contents=contents, config=config or None
            )
        except errors.APIError as e:
            if e.code not in (429, 500, 502, 503, 504, 404):
                raise
            last_error = e
    raise last_error
