"""
matcher.py — Stage 3: Citation Matcher
========================================
Takes signals from Stage 2 and attaches citations from the library.

This module is intentionally simple — one job, no logic, no thresholds.
All the intelligence lives in library.json. This is just the lookup.
"""

import json
import logging

logger = logging.getLogger(__name__)


def load_library(path: str) -> dict:
    """
    Load library.json from disk and return it as a dictionary.

    Args:
        path: path to library.json, e.g. "financial_brief/library.json"

    Returns:
        A dict keyed by signal name, each value a list of citation dicts.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def match_citations(signals: list[dict], library: dict) -> list[dict]:
    """
    Attach citations to each signal by looking up its name in the library.

    Args:
        signals: the list returned by detect_signals() in signals.py
        library: the dict returned by load_library()

    Returns:
        The same list of signal dicts, each with a new "citations" key:
            citations (list) — the matching entries from library.json,
                               or an empty list if the name wasn't found.

    Note:
        Signals are mutated in place (the citations key is added directly).
        The original list is also returned for convenience so callers can
        write: enriched = match_citations(signals, library)
    """
    for signal in signals:
        name = signal["name"]
        if name not in library:
            logger.warning(
                "Signal '%s' has no entry in the citation library. "
                "Check that library.json covers this signal name exactly.",
                name,
            )
            signal["citations"] = []
        else:
            signal["citations"] = library[name]

    return signals
