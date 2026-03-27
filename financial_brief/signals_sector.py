"""
signals_sector.py — Stage 2: Sector-Aware Signal Detector
==========================================================
Wraps signals.py with sector-specific thresholds sourced from
Damodaran NYU Stern Margins by Sector, January 2026.

For "general" sector, delegates entirely to detect_signals().
For named sectors, replaces the four threshold-based rules
(gross_margin, operating_margin, revenue_growth_yoy, debt_to_revenue,
opex_ratio) with sector-calibrated versions, then appends any
cross-metric signals (operational_leverage, cash_cushion) from detect_signals().
"""

from __future__ import annotations
from financial_brief.signals import detect_signals, _signal, _TYPE_ORDER

_SOURCE = "Source: Damodaran, NYU Stern Margins by Sector, January 2026."

# (strength_threshold, risk_threshold)
_THRESHOLDS = {
    #                           gross_margin      operating_margin  rev_growth_yoy     debt_to_revenue    opex_ratio
    "technology":           dict(gm=(0.55, 0.35), om=(0.25, 0.10), rg=(0.10, 0.04),  dr=(0.20, 0.50),  or_=(0.20, 0.35)),
    "healthcare":           dict(gm=(0.55, 0.30), om=(0.18, 0.08), rg=(0.08, 0.03),  dr=(0.30, 0.60),  or_=(0.25, 0.45)),
    "consumer_cyclical":    dict(gm=(0.35, 0.20), om=(0.10, 0.04), rg=(0.08, 0.03),  dr=(0.30, 0.70),  or_=(0.25, 0.40)),
    "consumer_defensive":   dict(gm=(0.40, 0.20), om=(0.15, 0.07), rg=(0.05, 0.02),  dr=(0.40, 0.80),  or_=(0.20, 0.35)),
    "industrials":          dict(gm=(0.28, 0.15), om=(0.12, 0.05), rg=(0.06, 0.02),  dr=(0.40, 0.80),  or_=(0.15, 0.25)),
    "energy":               dict(gm=(0.35, 0.15), om=(0.15, 0.05), rg=(0.05, -0.05), dr=(0.30, 0.60),  or_=(0.12, 0.22)),
    "communication_services": dict(gm=(0.50, 0.30), om=(0.20, 0.08), rg=(0.08, 0.03), dr=(0.30, 0.60), or_=(0.22, 0.38)),
}

_CROSS_METRIC_NAMES = {"Operational Leverage", "Margin Compression", "Strong Cash Position", "Low Cash Cushion"}


def _sector_label(sector: str) -> str:
    return sector.replace("_", " ").title()


def _check_gross_margin_sector(metrics, t, sector):
    m = metrics.get("gross_margin")
    if m is None:
        return None
    v, s = m["value"], _sector_label(sector)
    if v >= t["gm"][0]:
        return _signal("High Gross Margin", "strength", "gross_margin", v,
            f"Gross margin of {v:.1%} exceeds the {t['gm'][0]:.0%} strength threshold for {s} sector companies. {_SOURCE}")
    if v < t["gm"][1]:
        return _signal("Thin Gross Margin", "risk", "gross_margin", v,
            f"Gross margin of {v:.1%} falls below the {t['gm'][1]:.0%} risk threshold for {s} sector companies. {_SOURCE}")
    return _signal("Moderate Gross Margin", "observation", "gross_margin", v,
        f"Gross margin of {v:.1%} is within the normal range for {s} sector companies. {_SOURCE}")


def _check_operating_margin_sector(metrics, t, sector):
    m = metrics.get("operating_margin")
    if m is None:
        return None
    v, s = m["value"], _sector_label(sector)
    if v >= t["om"][0]:
        return _signal("Strong Operating Margin", "strength", "operating_margin", v,
            f"Operating margin of {v:.1%} exceeds the {t['om'][0]:.0%} strength threshold for {s} sector companies. {_SOURCE}")
    if v < t["om"][1]:
        label = "Operating Loss" if v < 0 else "Weak Operating Margin"
        return _signal(label, "risk", "operating_margin", v,
            f"Operating margin of {v:.1%} falls below the {t['om'][1]:.0%} risk threshold for {s} sector companies. {_SOURCE}")
    return _signal("Adequate Operating Margin", "observation", "operating_margin", v,
        f"Operating margin of {v:.1%} is within the normal range for {s} sector companies. {_SOURCE}")


def _check_revenue_growth_sector(metrics, t, sector):
    m = metrics.get("revenue_growth_yoy")
    if m is None:
        return None
    v, s = m["value"], _sector_label(sector)
    if v >= t["rg"][0]:
        return _signal("High Revenue Growth", "strength", "revenue_growth_yoy", v,
            f"Revenue growth of {v:.1%} exceeds the {t['rg'][0]:.0%} strength threshold for {s} sector companies. {_SOURCE}")
    if v < t["rg"][1]:
        label = "Revenue Decline" if v < 0 else "Slow Revenue Growth"
        return _signal(label, "risk", "revenue_growth_yoy", v,
            f"Revenue growth of {v:.1%} falls below the {t['rg'][1]:.0%} risk threshold for {s} sector companies. {_SOURCE}")
    return _signal("Moderate Revenue Growth", "observation", "revenue_growth_yoy", v,
        f"Revenue growth of {v:.1%} is within the normal range for {s} sector companies. {_SOURCE}")


def _check_debt_load_sector(metrics, t, sector):
    m = metrics.get("debt_to_revenue")
    if m is None:
        return None
    v, s = m["value"], _sector_label(sector)
    if v > t["dr"][1]:
        return _signal("High Debt Load", "risk", "debt_to_revenue", v,
            f"Debt-to-revenue of {v:.2f}x exceeds the {t['dr'][1]:.2f}x risk threshold for {s} sector companies. {_SOURCE}")
    if v <= t["dr"][0]:
        return _signal("Conservative Debt Level", "strength", "debt_to_revenue", v,
            f"Debt-to-revenue of {v:.2f}x is below the {t['dr'][0]:.2f}x strength threshold for {s} sector companies. {_SOURCE}")
    return _signal("Elevated Leverage", "observation", "debt_to_revenue", v,
        f"Debt-to-revenue of {v:.2f}x is within the normal range for {s} sector companies. {_SOURCE}")


def _check_opex_ratio_sector(metrics, t, sector):
    m = metrics.get("opex_ratio")
    if m is None:
        return None
    v, s = m["value"], _sector_label(sector)
    if v < t["or_"][0]:
        return _signal("Disciplined Opex Ratio", "strength", "opex_ratio", v,
            f"Opex ratio of {v:.1%} is below the {t['or_'][0]:.0%} strength threshold for {s} sector companies. {_SOURCE}")
    if v > t["or_"][1]:
        return _signal("High Opex Ratio", "risk", "opex_ratio", v,
            f"Opex ratio of {v:.1%} exceeds the {t['or_'][1]:.0%} risk threshold for {s} sector companies. {_SOURCE}")
    return _signal("Moderate Opex Ratio", "observation", "opex_ratio", v,
        f"Opex ratio of {v:.1%} is within the normal range for {s} sector companies. {_SOURCE}")


def detect_signals_sector(metrics: dict, sector: str) -> list[dict]:
    """Sector-aware signal detection. Falls back to detect_signals() for 'general'."""
    if sector not in _THRESHOLDS:
        return detect_signals(metrics)

    t = _THRESHOLDS[sector]
    cross_metric = [s for s in detect_signals(metrics) if s["name"] in _CROSS_METRIC_NAMES]

    candidates = [
        _check_gross_margin_sector(metrics, t, sector),
        _check_operating_margin_sector(metrics, t, sector),
        _check_revenue_growth_sector(metrics, t, sector),
        _check_debt_load_sector(metrics, t, sector),
        _check_opex_ratio_sector(metrics, t, sector),
        *cross_metric,
    ]

    signals = [s for s in candidates if s is not None]
    signals.sort(key=lambda s: _TYPE_ORDER[s["type"]])
    return signals
