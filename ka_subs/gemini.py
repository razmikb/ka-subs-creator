"""Gemini writes the words of one audio part (PLAN.md §3.2, mode B). Audio only, never
video or a YouTube link. Each call uses one of the day's few free requests."""
from pathlib import Path

from .common import Stop
from .prompt import PROMPT

# Checked against ai.google.dev/gemini-api/docs/models on 2026-10-27. Change it in the
# notebook's settings if Google retires it or the free tier doesn't include it.
DEFAULT_MODEL = "gemini-3.8-flash"


class QuotaUsedUp(Stop):
    """The free daily requests are gone. The batch switches to manual mode (AI Studio)."""


def transcribe(audio: Path, api_key: str, model: str = DEFAULT_MODEL) -> str:
    from google import genai

    client = genai.Client(api_key=api_key)
    uploaded = None
    try:
        uploaded = client.files.upload(file=str(audio), config={"mime_type": "audio/ogg"})
        reply = client.interactions.create(
            model=model,
            input=[
                {"type": "text", "text": PROMPT},
                {"type": "audio", "uri": uploaded.uri, "mime_type": uploaded.mime_type},
            ],
        )
        text = reply.output_text or ""
    except Exception as exc:  # the package raises several unrelated error types
        raise _explain(exc, model) from None
    finally:
        if uploaded is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass  # Google deletes uploads by itself after 48 hours
    if not text.strip():
        raise Stop(f"Gemini sent back an empty reply for {audio.name}. Run it again, "
                   "or do this part by hand in AI Studio.")
    return text


def _explain(exc: Exception, model: str) -> Stop:
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    words = str(exc)
    if code == 429 or "RESOURCE_EXHAUSTED" in words:
        return QuotaUsedUp("Gemini's free daily limit is used up. It resets at midnight "
                           "US Pacific time (11:00 in Tbilisi). Until then, do the waiting "
                           "parts by hand in AI Studio (see NEXT_STEPS.txt in the folder).")
    if code in (400, 401, 403) and ("API key" in words or "API_KEY" in words):
        return Stop("Gemini didn't accept the API key. Check GEMINI_API_KEY in Colab's "
                    "Secrets (the key icon on the left).")
    if code == 404:
        return Stop(f"Gemini has no model called {model!r} (any more). Set MODEL in the "
                    "settings cell to a current one from ai.google.dev/gemini-api/docs/models.")
    return Stop(f"Gemini failed: {words[:300]}")
