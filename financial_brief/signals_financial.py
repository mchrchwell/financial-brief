"""
signals_financial.py — Stage 2 (Financial Sector): Signal Detector

detect_signals_financial(metrics: dict) -> list[dict]
    Applies financial-sector signal rules to the metrics bundle produced
    by compute_all_metrics_financial() and returns sorted findings.

Same signal structure as signals.py: {name, type, metric, value, detail}.
Sort order: strengths first, then observations, then risks.
"""

from __future__ import annotations


def _signal(name: str, kind: str, metric: str, value: float, detail: str) -> dict:
    return {"name": name, "type": kind, "metric": metric, "value": value, "detail": detail}


def _check_efficiency_ratio(metrics: dict) -> dict | None:
    m = metrics.get("efficiency_ratio")
    if m is None:
        return None
    v = m["value"]
    if v < 0.60:
        return _signal("Strong Efficiency Ratio", "strength", "efficiency_ratio", v,
                       "Efficiency ratio below 60% indicates disciplined cost management relative to revenue")
    if v > 0.65:
        return _signal("Efficiency Ratio Risk", "risk", "efficiency_ratio", v,
                       "Efficiency ratio above 65% indicates cost structure pressure relative to sector peers.")
    return None


def _check_roe(metrics: dict) -> dict | None:
    m = metrics.get("roe")
    if m is None:
        return None
    v = m["value"]
    if v > 0.15:
        return _signal("Strong ROE", "strength", "roe", v,
                       "ROE above 15% reflects strong returns on shareholder capital")
    if v < 0.08:
        return _signal("Weak ROE", "risk", "roe", v,
                       "ROE below 8% indicates weak returns on equity capital")
    return None


def _check_net_interest_margin(metrics: dict) -> dict | None:
    m = metrics.get("net_interest_margin")
    if m is None:
        return None
    v = m["value"]
    if v > 0.20:
        return _signal("Strong Net Interest Margin", "strength", "net_interest_margin", v,
                       "Net interest margin above 20% reflects strong spread between interest income and funding costs")
    if v < 0.10:
        return _signal("Net Interest Margin Risk", "risk", "net_interest_margin", v,
                       "Net interest margin below 10% signals spread compression")
    return None


def _check_leverage_ratio(metrics: dict) -> dict | None:
    m = metrics.get("leverage_ratio")
    if m is None:
        return None
    v = m["value"]
    if v > 10.0:
        return _signal("High Leverage Ratio", "risk", "leverage_ratio", v,
                       "Leverage ratio above 10x increases vulnerability to asset quality deterioration")
    if 7.0 <= v <= 10.0:
        return _signal("Moderate Leverage Ratio", "observation", "leverage_ratio", v,
                       "Leverage ratio in the 7-10x range is typical for brokerages but warrants monitoring")
    return None


def _check_revenue_growth(metrics: dict) -> dict | None:
    m = metrics.get("revenue_growth_yoy")
    if m is None:
        return None
    v = m["value"]
    if v > 0.08:
        return _signal("Strong Revenue Growth", "strength", "revenue_growth_yoy", v,
                       "Revenue growth above 8% reflects strong business momentum")
    return None


def _check_net_margin(metrics: dict) -> dict | None:
    m = metrics.get("net_margin")
    if m is None:
        return None
    v = m["value"]
    return _signal("Net Margin", "observation", "net_margin", v,
                   f"Net margin of {v:.1%} reflects the share of revenue converted to profit after all expenses")


# ---------------------------------------------------------------------------
# MASTER FUNCTION
# ---------------------------------------------------------------------------

_TYPE_ORDER = {"strength": 0, "observation": 1, "risk": 2}


def detect_signals_financial(metrics: dict) -> list[dict]:
    """
    Run all financial-sector signal rules and return sorted findings.

    Args:
        metrics: the dict returned by compute_all_metrics_financial()

    Returns:
        A list of signal dicts sorted by type: strengths first,
        then observations, then risks.
    """
    candidates = [
        _check_efficiency_ratio(metrics),
        _check_roe(metrics),
        _check_net_interest_margin(metrics),
        _check_leverage_ratio(metrics),
        _check_revenue_growth(metrics),
        _check_net_margin(metrics),
    ]

    signals = [s for s in candidates if s is not None]
    signals.sort(key=lambda s: _TYPE_ORDER[s["type"]])

    return signals
