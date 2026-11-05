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

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

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

        _client = genai.Client(api_key=api_key)
    return _client
