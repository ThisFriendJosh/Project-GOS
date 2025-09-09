from __future__ import annotations
from typing import Any, Dict


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize the structure of an event.

    For now this is a passthrough stub.
    """
    return dict(event)
"""Text normalization utilities.

This module provides a small normalization pipeline for incoming events.
The pipeline performs a number of transformations on the ``content.text``
field of an :class:`~api.schemas.EventIn`:

* Strip simple HTML markup and collapse extraneous whitespace.
* Perform a very light-weight language detection and drop unsupported
  languages.
* Remove obvious pieces of Personally Identifiable Information (PII) such as
  e-mail addresses and phone numbers.
* Expand shortened URLs by following redirects.

The main entry point is :func:`normalize` which accepts an ``EventIn`` and
returns a new, normalized ``EventIn``.
"""

from __future__ import annotations

import html
import re
import urllib.request
from typing import Iterable

from api.schemas import EventIn

# ---------------------------------------------------------------------------
# Cleaning


def clean_text(text: str) -> str:
    """Remove HTML markup and collapse excessive whitespace.

    Parameters
    ----------
    text:
        Raw text possibly containing HTML tags and irregular spacing.

    Returns
    -------
    str
        Cleaned text.
    """

    # Convert HTML entities and remove tags.
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse consecutive whitespace characters.
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Language detection

# A tiny and deliberately simple language detector.  It looks for a couple of
# common words in the input.  This keeps the project lightweight and avoids
# pulling in heavy external dependencies while being sufficient for unit tests.
EN_WORDS: Iterable[str] = {"the", "and", "hello", "world"}
ES_WORDS: Iterable[str] = {"hola", "mundo", "gracias", "que", "el"}


def detect_language(text: str) -> str:
    """Best effort language detection.

    The function returns ``"es"`` if it believes the text is Spanish and
    ``"en"`` otherwise.  The implementation is intentionally heuristic – it is
    *not* intended to be production ready but suffices for demonstration and
    unit testing purposes.
    """

    lowered = text.lower()
    english_score = sum(word in lowered for word in EN_WORDS)
    spanish_score = sum(word in lowered for word in ES_WORDS)
    return "es" if spanish_score > english_score else "en"


SUPPORTED_LANGUAGES = {"en"}


# ---------------------------------------------------------------------------
# PII removal

EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
PHONE_RE = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")


def remove_pii(text: str) -> str:
    """Scrub e-mail addresses and phone numbers from ``text``."""

    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text


# ---------------------------------------------------------------------------
# URL expansion

URL_RE = re.compile(r"https?://\S+")


def _expand_url(url: str) -> str:
    """Follow redirects for ``url`` and return the final destination.

    Network errors are swallowed and the original URL is returned in that
    case.  ``urllib.request.urlopen`` is used so that tests can easily monkey
    patch network behaviour.
    """

    try:
        with urllib.request.urlopen(url) as resp:  # pragma: no cover - network
            return resp.geturl()
    except Exception:  # pragma: no cover - best effort
        return url


def expand_urls(text: str) -> str:
    """Replace all URLs in ``text`` with their expanded targets."""

    return URL_RE.sub(lambda m: _expand_url(m.group(0)), text)


# ---------------------------------------------------------------------------
# Normalization entry point


def normalize(event: EventIn) -> EventIn:
    """Normalize an incoming event.

    A deep copy of ``event`` is created and returned so that callers do not see
    in-place mutations.  ``feats['lang']`` will contain the detected language
    for supported events.
    """

    evt = event.model_copy(deep=True)
    text = evt.content.get("text", "")
    text = clean_text(text)
    lang = detect_language(text)
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang}")
    text = remove_pii(text)
    text = expand_urls(text)
    evt.content["text"] = text
    evt.feats["lang"] = lang
    return evt


__all__ = [
    "clean_text",
    "detect_language",
    "remove_pii",
    "expand_urls",
    "normalize",
]
