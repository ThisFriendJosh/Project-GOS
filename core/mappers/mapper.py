"""Utilities for mapping raw events to MITRE ATT&CK style TTP identifiers."""

from collections import Counter
from typing import Dict, List, Tuple

from api.schemas import EventIn  # root-mode import


# Simple keyword-to-TTP mapping. In a real system this could be replaced with a
# trained model or more sophisticated rules.  The keys are lowercase tokens that
# will be searched for within the textual portions of an event's content.
KEYWORD_TTPS: Dict[str, str] = {
    "phish": "T1566",  # Phishing
    "malware": "T1204",  # User Execution
    "ransomware": "T1486",  # Data Encrypted for Impact
    "sql injection": "T1190",  # Exploit Public-Facing Application
    "ddos": "T1498",  # Network Denial of Service
    "credential": "T1110",  # Brute Force
    "lateral": "T1021",  # Lateral Movement
    "exfiltration": "T1041",  # Exfiltration Over C2 Channel
}


def map_event_to_ttps(evt: EventIn) -> Tuple[List[str], Dict[str, float]]:
    """Map an :class:`EventIn` to likely TTP identifiers.

    The implementation uses lightweight heuristics that inspect textual fields
    of the event for keywords.  When a keyword is found the corresponding TTP ID
    is added to the output along with a simple probability score.  Probabilities
    are normalized so that their sum equals ``1.0``.

    Parameters
    ----------
    evt:
        Event to analyse.

    Returns
    -------
    Tuple[List[str], Dict[str, float]]
        ``observed_ttp`` and a mapping of TTP ID to probability scores.
    """

    # Collect textual content from the event.  Only simple string and list
    # values are considered which is sufficient for our heuristic rules.
    text_parts: List[str] = []
    for value in evt.content.values():
        if isinstance(value, str):
            text_parts.append(value.lower())
        elif isinstance(value, list):
            text_parts.extend(str(v).lower() for v in value)

    full_text = " ".join(text_parts)

    # Count each TTP that matches a keyword in the text.
    counts: Counter[str] = Counter()
    for keyword, ttp_id in KEYWORD_TTPS.items():
        if keyword in full_text:
            counts[ttp_id] += 1

    observed = list(counts.keys())
    total = sum(counts.values())
    probs = {k: v / total for k, v in counts.items()} if total else {}
    return observed, probs
