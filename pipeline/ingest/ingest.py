from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4
from datetime import datetime


def ingest_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a raw event for processing.

    Ensures the event has an ``event_id`` and timestamp.
    """
    evt = dict(event)
    evt.setdefault("event_id", str(uuid4()))
    evt.setdefault("ts", datetime.utcnow())
    return evt
"""Ingestion helpers for OSINT sources.

This module defines small connector functions for various open source
intelligence (OSINT) feeds.  Each connector accepts a *raw* payload from a
specific provider (e.g., X/Twitter, Telegram or YouTube), converts the
provider specific fields into a minimal normalized dictionary and finally the
:func:`ingest_event` function turns that dictionary into an
:class:`api.schemas.EventIn` model.

The connectors implemented here are intentionally lightweight placeholders
intended for documentation and testing.  Real implementations would include
HTTP requests, authentication and error handling for the respective APIs.
"""


from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict

from api.schemas import EventIn


# ---------------------------------------------------------------------------
# Connector functions
# ---------------------------------------------------------------------------


def fetch_from_twitter(tweet: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise an X/Twitter tweet payload.

    Parameters
    ----------
    tweet:
        Dictionary matching the structure returned by the Twitter API.  The
        function expects at minimum ``id`` and ``created_at`` (ISO 8601 string)
        fields.  ``author_id`` and ``text`` are optional but recommended.

    Returns
    -------
    dict
        Dictionary with the fields required by :func:`ingest_event`:
        ``event_id``, ``ts``, ``actor_id`` and ``content``.  Source specific
        information such as language and attachments are nested under the
        ``content`` key.
    """

    ts = tweet.get("created_at")
    dt = (
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if isinstance(ts, str)
        else datetime.utcnow()
    )
    return {
        "event_id": str(tweet.get("id")),
        "ts": dt,
        "actor_id": tweet.get("author_id"),
        "content": {
            "text": tweet.get("text"),
            "lang": tweet.get("lang"),
            "attachments": tweet.get("attachments"),
        },
    }


def fetch_from_telegram(message: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a Telegram message payload.

    The Telegram Bot API returns ``message_id`` and a UNIX epoch ``date`` for
    each message.  Those are mapped to ``event_id`` and ``ts`` respectively.
    Sender information is stored as ``actor_id`` and the message text is placed
    under ``content['text']``.
    """

    ts = message.get("date")
    dt = (
        datetime.fromtimestamp(ts)
        if isinstance(ts, (int, float))
        else datetime.utcnow()
    )
    sender = message.get("from", {})
    return {
        "event_id": str(message.get("message_id")),
        "ts": dt,
        "actor_id": str(sender.get("id")) if sender else None,
        "content": {
            "text": message.get("text"),
            "chat": message.get("chat"),
        },
    }


def fetch_from_youtube(video: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a YouTube video or comment payload.

    Parameters
    ----------
    video:
        Structure inspired by the YouTube Data API.  The function looks for an
        ``id`` and a ``snippet`` dictionary with ``publishedAt`` and
        ``channelId`` fields.
    """

    snippet = video.get("snippet", {})
    ts = snippet.get("publishedAt")
    dt = (
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if isinstance(ts, str)
        else datetime.utcnow()
    )
    return {
        "event_id": str(video.get("id")),
        "ts": dt,
        "actor_id": snippet.get("channelId"),
        "content": {
            "title": snippet.get("title"),
            "description": snippet.get("description"),
        },
    }


def fetch_from_rss(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise an RSS/Atom feed item.

    The function works with dictionaries similar to those produced by
    :mod:`feedparser`.  Publication dates are parsed using
    :func:`email.utils.parsedate_to_datetime` which handles most common RSS
    date formats.  The ``id`` or ``link`` is used as the ``event_id``.
    """

    ts = item.get("published") or item.get("updated")
    dt = parsedate_to_datetime(ts) if isinstance(ts, str) else datetime.utcnow()
    return {
        "event_id": item.get("id") or item.get("link"),
        "ts": dt,
        "actor_id": None,
        "content": {
            "title": item.get("title"),
            "summary": item.get("summary"),
            "link": item.get("link"),
        },
    }


def fetch_from_web(document: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise data scraped from an arbitrary web page.

    Real implementations would download the page and extract metadata.  For the
    purposes of this project the function expects a dictionary containing at
    least ``url`` and ``retrieved_at``.  The URL itself acts as the
    ``event_id``.
    """

    ts = document.get("retrieved_at")
    dt = (
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if isinstance(ts, str)
        else datetime.utcnow()
    )
    return {
        "event_id": document.get("url"),
        "ts": dt,
        "actor_id": document.get("author"),
        "content": {
            "title": document.get("title"),
            "html": document.get("html"),
            "text": document.get("text"),
        },
    }


# Mapping of source names to connector functions.  The ingest_event function
# uses this table to dispatch raw events to the appropriate normaliser.
CONNECTORS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "twitter": fetch_from_twitter,
    "telegram": fetch_from_telegram,
    "youtube": fetch_from_youtube,
    "rss": fetch_from_rss,
    "web": fetch_from_web,
}


def ingest_raw_event(raw: Dict[str, Any], source: str) -> EventIn:
    """Convert a raw event payload into an :class:`EventIn` instance.

    Parameters
    ----------
    raw:
        Source specific dictionary describing the event.
    source:
        Identifier of the source.  Must be a key in :data:`CONNECTORS`.

    Returns
    -------
    EventIn
        Pydantic model with normalised event data ready for downstream
        processing.
    """

    try:
        normaliser = CONNECTORS[source]
    except KeyError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"Unsupported source: {source}") from exc

    normalised = normaliser(raw)
    normalised["src"] = source
    return EventIn(**normalised)
