"""
Thin wrapper around the Gemini API (Google AI Studio, simple API-key auth).

Loads GEMINI_API_KEY from a local .env file (see .env.example) and exposes
one function, generate_json, used for both menu OCR and photo-based food
recognition. Callers should catch GeminiError and show a clean message
instead of letting a stack trace reach the UI.
"""

import json
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-3.6-flash"


class GeminiError(Exception):
    """Raised for a missing/invalid key, a failed call, or unparseable output."""


def _get_model():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "paste-your-key-here":
        raise GeminiError(
            "No Gemini API key configured. Add GEMINI_API_KEY to your .env file "
            "(see .env.example) — get one at aistudio.google.com/apikey."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)


def generate_json(prompt: str, image_path=None) -> dict:
    """
    Send a prompt (optionally with an image) to Gemini and parse the reply
    as JSON. Raises GeminiError on any failure — missing key, API error, or
    a response that isn't valid JSON — so callers never see a raw traceback.
    """
    model = _get_model()

    parts = [prompt]
    if image_path is not None:
        image_path = Path(image_path)
        mime_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        parts.append({"mime_type": mime_type, "data": image_path.read_bytes()})

    try:
        response = model.generate_content(
            parts,
            generation_config={"response_mime_type": "application/json"},
        )
    except Exception as exc:  # network/auth/quota errors from the SDK
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    try:
        return json.loads(response.text)
    except (ValueError, AttributeError) as exc:
        raise GeminiError(f"Gemini didn't return valid JSON: {exc}") from exc
