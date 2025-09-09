from __future__ import annotations
from typing import Any, Dict, Tuple


def enrich_event(event: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Enrich an event with additional context.

    Returns the enriched event and any metadata generated during enrichment.
    """
    metadata: Dict[str, Any] = {"source": "stub"}
    # Example enrichment flag
    feats = event.get("feats", {})
    feats["enriched"] = True
    event["feats"] = feats
    return event, metadata
"""Utility functions for enriching events with NLP features.

This module provides lightweight implementations for extracting
named entities, sentiment, topics, and bot-likelihood metrics from
textual event content.  Each enrichment can be configured to use
an external service via environment variables:

- ``NER_MODEL``: URL to a NER service (default: ``"simple"`` heuristics).
- ``SENTIMENT_MODEL``: URL to a sentiment service (default: ``"simple"``).
- ``TOPIC_MODEL``: URL to a topic service (default: ``"simple"``).
- ``BOT_MODEL``: URL to a bot-likelihood service (default: ``"simple"``).

When the value is ``"simple"``, a rule-based heuristic is used.  If the
value looks like a URL, the text is POSTed as JSON to the endpoint and the
resulting JSON field is used.  Failures to contact the service result in an
empty or neutral output.

The primary entry point is :func:`enrich_event` which accepts an
``EventIn`` object and returns an updated instance with the ``feats`` field
populated.
"""

import json
import os
import re
from typing import Any, Dict, List
from urllib.error import URLError
from urllib.request import Request, urlopen

from api.schemas import EventIn


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _env(name: str, default: str) -> str:
    """Helper to fetch environment variables with a fallback."""

    return os.getenv(name, default)


NER_MODEL = _env("NER_MODEL", "simple")
SENTIMENT_MODEL = _env("SENTIMENT_MODEL", "simple")
TOPIC_MODEL = _env("TOPIC_MODEL", "simple")
BOT_MODEL = _env("BOT_MODEL", "simple")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _call_service(url: str, payload: Dict[str, Any], field: str) -> Any:
    """Call an external service and return ``field`` from the response.

    The service is expected to accept a JSON object via POST and return a
    JSON response.  Any exception will result in ``None`` being returned.
    """

    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=5) as resp:  # noqa: S310 - timeout specified
            result = json.loads(resp.read().decode("utf-8"))
            return result.get(field)
    except (URLError, OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Enrichment functions
# ---------------------------------------------------------------------------


def compute_ner(text: str) -> List[str]:
    """Return a list of named entities found in ``text``.

    If ``NER_MODEL`` is ``"simple"`` a basic regular expression is used to
    extract capitalised word sequences.  Otherwise ``NER_MODEL`` is treated
    as a URL pointing to an external service which returns an ``entities``
    list in its JSON response.
    """

    if NER_MODEL == "simple":
        matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        # ``dict.fromkeys`` preserves order while removing duplicates
        return list(dict.fromkeys(matches))

    entities = _call_service(NER_MODEL, {"text": text}, "entities")
    return entities or []


def compute_sentiment(text: str) -> Dict[str, Any]:
    """Compute a sentiment score for ``text``.

    The "simple" model counts occurrences of positive/negative words and
    returns a score in ``[-1, 1]`` with a corresponding label.
    """

    if SENTIMENT_MODEL == "simple":
        positives = {
            "good",
            "great",
            "happy",
            "fantastic",
            "positive",
            "love",
            "excellent",
            "nice",
        }
        negatives = {
            "bad",
            "terrible",
            "sad",
            "horrible",
            "negative",
            "hate",
            "poor",
        }
        words = re.findall(r"\b\w+\b", text.lower())
        pos = sum(1 for w in words if w in positives)
        neg = sum(1 for w in words if w in negatives)
        total = len(words) or 1
        score = (pos - neg) / total
        if score > 0.05:
            label = "positive"
        elif score < -0.05:
            label = "negative"
        else:
            label = "neutral"
        return {"score": score, "label": label}

    result = _call_service(SENTIMENT_MODEL, {"text": text}, "sentiment")
    if isinstance(result, dict):
        return result
    return {"score": 0.0, "label": "unknown"}


def compute_topics(text: str) -> List[str]:
    """Derive topic labels for ``text``.

    The simple implementation matches keywords to a handful of topics.
    External services should return a ``topics`` list.
    """

    if TOPIC_MODEL == "simple":
        topics_map = {
            "politics": ["election", "government", "senate", "president"],
            "sports": ["football", "basketball", "soccer", "tennis"],
            "technology": ["technology", "computer", "ai", "software"],
        }
        lower = text.lower()
        labels = [
            topic for topic, keywords in topics_map.items() if any(k in lower for k in keywords)
        ]
        return labels or ["other"]

    topics = _call_service(TOPIC_MODEL, {"text": text}, "topics")
    return topics or []


def compute_bot_likelihood(text: str) -> float:
    """Estimate the likelihood that ``text`` was produced by a bot.

    The heuristic considers the ratio of links, mentions, and hashtags to
    total tokens.  External services should return a numeric likelihood
    between 0 and 1.
    """

    if BOT_MODEL == "simple":
        tokens = text.split()
        if not tokens:
            return 0.0
        link_count = sum(1 for t in tokens if t.startswith("http"))
        mention_count = sum(1 for t in tokens if t.startswith("@"))
        hashtag_count = sum(1 for t in tokens if t.startswith("#"))
        score = (link_count + mention_count + hashtag_count) / len(tokens)
        return float(min(score, 1.0))

    result = _call_service(BOT_MODEL, {"text": text}, "bot_likelihood")
    try:
        return float(result)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def enrich(event: EventIn) -> EventIn:
    """Return a copy of ``event`` with its ``feats`` field populated."""

    text = ""
    if isinstance(event.content, dict):
        text = str(event.content.get("text", ""))
    elif isinstance(event.content, str):
        text = event.content

    feats = dict(event.feats) if event.feats else {}
    feats["ner"] = compute_ner(text)
    feats["sentiment"] = compute_sentiment(text)
    feats["topics"] = compute_topics(text)
    feats["bot_likelihood"] = compute_bot_likelihood(text)

    return event.model_copy(update={"feats": feats})


__all__ = [
    "compute_ner",
    "compute_sentiment",
    "compute_topics",
    "compute_bot_likelihood",
    "enrich",
]
