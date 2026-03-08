"""
signals.py — Stage 2: Signal Detector
======================================
Takes the metrics bundle from Stage 1 and identifies what story
the numbers are telling: strengths, risks, and observations.

Design principle: every signal is DETERMINISTIC and TRACEABLE.
Each signal records exactly which metric triggered it, the value
that crossed a threshold, and a plain-English explanation.

This module never makes judgment calls — it applies pre-defined
thresholds. The AI analyst in Stage 4 will interpret the signals
in combination. Our job here is just to flag what's notable.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# WHAT IS A "SIGNAL"?
#
# A signal is a finding — something notable the numbers are telling us.
# Every signal is a dictionary with five fields:
#
#   name    — short label, e.g. "Strong Gross Margin"
#   type    — one of: "strength", "risk", "observation"
#   metric  — the key from the metrics bundle that triggered this signal
#   value   — the numeric value that crossed the threshold
#   detail  — a sentence explaining what this signal means in context
#
# "strength"    → a positive indicator, something the business is doing well
# "risk"        → a warning flag, something that warrants concern
# "observation" → a neutral note worth mentioning but not alarming
# ---------------------------------------------------------------------------


def _signal(name: str, kind: str, metric: str, value: float, detail: str) -> dict:
    """
    Helper that builds a signal dictionary.

    All five arguments are required — we never want a signal with missing
    fields because Stage 3 (Citation Matcher) and Stage 4 (Analyst) both
    depend on this structure being complete and consistent.
    """
    return {
        "name":   name,
        "type":   kind,
        "metric": metric,
        "value":  value,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# INDIVIDUAL SIGNAL RULES
#
# Each function checks one aspect of the metrics bundle and returns either
# a signal dict (if something notable was found) or None.
#
# Each rule starts with:
#   m = metrics.get("metric_name")
#   if m is None: return None
#
# This makes rules safe to call even when a metric isn't available
# (e.g., revenue_growth_yoy requires 2 years of data).
# ---------------------------------------------------------------------------


def _check_gross_margin(metrics: dict) -> dict | None:
    """
    Gross margin reveals pricing power and production cost efficiency.

    Thresholds:
      >= 50%: exceptional — typical of software, pharma, luxury goods
      >= 20%: normal range — no strong signal either way
      <  20%: thin — vulnerable to input cost shocks
    """
    m = metrics.get("gross_margin")
    if m is None:
        return None

    v = m["value"]

    if v >= 0.50:
        return _signal(
            name="High Gross Margin",
            kind="strength",
            metric="gross_margin",
            value=v,
            detail=(
                f"Gross margin of {v:.1%} suggests strong pricing power or "
                "exceptionally low direct production costs — characteristic "
                "of software, services, or premium product businesses."
            ),
        )
    elif v < 0.20:
        return _signal(
            name="Thin Gross Margin",
            kind="risk",
            metric="gross_margin",
            value=v,
            detail=(
                f"Gross margin of {v:.1%} leaves little room to absorb cost "
                "increases or fund overhead. Signals vulnerability to input "
                "cost shocks or pricing pressure."
            ),
        )
    else:
        return _signal(
            name="Moderate Gross Margin",
            kind="observation",
            metric="gross_margin",
            value=v,
            detail=(
                f"Gross margin of {v:.1%} is within a normal range. "
                "The story depends on the industry and trend — compare against "
                "sector peers and prior-year figures for full context."
            ),
        )


def _check_operating_margin(metrics: dict) -> dict | None:
    """
    Operating margin reflects efficiency of the whole operation —
    including overhead (salaries, rent, marketing) on top of production costs.

    Thresholds:
      >= 15%: strong — excellent cost discipline
      >= 5%:  adequate — profitable but limited headroom
       0–5%:  thin — any revenue dip could tip into losses
       < 0%:  operating loss — critical
    """
    m = metrics.get("operating_margin")
    if m is None:
        return None

    v = m["value"]

    if v >= 0.15:
        return _signal(
            name="Strong Operating Margin",
            kind="strength",
            metric="operating_margin",
            value=v,
            detail=(
                f"Operating margin of {v:.1%} indicates disciplined cost "
                "management. The business converts a meaningful share of revenue "
                "into operating profit — a hallmark of operationally efficient companies."
            ),
        )
    elif v < 0:
        return _signal(
            name="Operating Loss",
            kind="risk",
            metric="operating_margin",
            value=v,
            detail=(
                f"Negative operating margin ({v:.1%}) means operating costs "
                "exceed revenue. Sustainable only if backed by strong cash "
                "reserves and a credible path to profitability."
            ),
        )
    elif v < 0.05:
        return _signal(
            name="Thin Operating Margin",
            kind="risk",
            metric="operating_margin",
            value=v,
            detail=(
                f"Operating margin of {v:.1%} provides minimal buffer. "
                "A modest revenue decline or unexpected cost increase could "
                "push the company into an operating loss."
            ),
        )
    else:
        return _signal(
            name="Adequate Operating Margin",
            kind="observation",
            metric="operating_margin",
            value=v,
            detail=(
                f"Operating margin of {v:.1%} is profitable but not exceptional. "
                "Room to improve through tighter cost discipline or stronger "
                "pricing leverage."
            ),
        )


def _check_revenue_growth(metrics: dict) -> dict | None:
    """
    Revenue growth answers: is this business expanding?

    Thresholds:
      >= 20%: high growth — strong demand or expansion phase
      >= 5%:  moderate — healthy, compounding trajectory
       0–5%:  slow — mature or stalling
       < 0%:  decline — serious signal requiring investigation
    """
    m = metrics.get("revenue_growth_yoy")
    if m is None:
        return None

    v = m["value"]

    if v >= 0.20:
        return _signal(
            name="High Revenue Growth",
            kind="strength",
            metric="revenue_growth_yoy",
            value=v,
            detail=(
                f"Revenue grew {v:.1%} YoY — a high-growth trajectory suggesting "
                "strong market demand, successful expansion, or effective new "
                "product adoption."
            ),
        )
    elif v >= 0.05:
        return _signal(
            name="Moderate Revenue Growth",
            kind="observation",
            metric="revenue_growth_yoy",
            value=v,
            detail=(
                f"Revenue grew {v:.1%} YoY — a steady, healthy pace. "
                "Consistent moderate growth compounds meaningfully over a "
                "multi-year horizon."
            ),
        )
    elif v >= 0:
        return _signal(
            name="Slow Revenue Growth",
            kind="observation",
            metric="revenue_growth_yoy",
            value=v,
            detail=(
                f"Revenue grew only {v:.1%} YoY. Near-zero growth can signal "
                "market saturation, rising competition, or the beginning of a plateau."
            ),
        )
    else:
        return _signal(
            name="Revenue Decline",
            kind="risk",
            metric="revenue_growth_yoy",
            value=v,
            detail=(
                f"Revenue contracted {abs(v):.1%} YoY. Declining revenue "
                "erodes the fixed-cost base and creates a negative compounding "
                "effect on profitability if sustained."
            ),
        )


def _check_debt_load(metrics: dict) -> dict | None:
    """
    Debt-to-revenue measures leverage relative to the top line.

    Thresholds (debt-to-revenue ratio):
      > 1.5x:  high — materially constrains financial flexibility
      > 0.75x: elevated — worth monitoring
     <= 0.25x: conservative — ample capacity for strategic debt
    """
    m = metrics.get("debt_to_revenue")
    if m is None:
        return None

    v = m["value"]

    if v > 1.5:
        return _signal(
            name="High Debt Load",
            kind="risk",
            metric="debt_to_revenue",
            value=v,
            detail=(
                f"Debt-to-revenue of {v:.2f}x is elevated. Heavy debt "
                "obligations constrain reinvestment and amplify vulnerability "
                "to revenue shocks or rising interest rates."
            ),
        )
    elif v > 0.75:
        return _signal(
            name="Elevated Leverage",
            kind="observation",
            metric="debt_to_revenue",
            value=v,
            detail=(
                f"Debt-to-revenue of {v:.2f}x is manageable if cash flows "
                "are stable, but limits financial flexibility. Monitor alongside "
                "cash position and growth trajectory."
            ),
        )
    elif v <= 0.25:
        return _signal(
            name="Conservative Debt Level",
            kind="strength",
            metric="debt_to_revenue",
            value=v,
            detail=(
                f"Debt-to-revenue of {v:.2f}x indicates a conservatively "
                "financed business with ample capacity for strategic borrowing "
                "if needed."
            ),
        )

    return None  # Middle band (0.25–0.75x): not notable enough to surface


def _check_cash_cushion(metrics: dict) -> dict | None:
    """
    Cash-to-revenue measures liquidity relative to business size.

    Thresholds:
      >= 20%: strong — resilient to short-term shocks
       < 5%:  low — a small revenue miss could cause a cash crunch
    """
    m = metrics.get("cash_to_revenue")
    if m is None:
        return None

    v = m["value"]

    if v >= 0.20:
        return _signal(
            name="Strong Cash Position",
            kind="strength",
            metric="cash_to_revenue",
            value=v,
            detail=(
                f"Cash-to-revenue of {v:.1%} represents a healthy liquidity "
                "buffer — resilience against short-term shocks and optionality "
                "for opportunistic investment."
            ),
        )
    elif v < 0.05:
        return _signal(
            name="Low Cash Cushion",
            kind="risk",
            metric="cash_to_revenue",
            value=v,
            detail=(
                f"Cash-to-revenue of {v:.1%} is low. A small revenue shortfall "
                "or unexpected expense could create a liquidity crunch with "
                "limited time to react."
            ),
        )

    return None  # Middle band: adequate, not notable


def _check_operational_leverage(metrics: dict) -> dict | None:
    """
    A CROSS-METRIC rule — compares two growth rates to detect one of two patterns:

    1. Operational Leverage (strength):
       Operating profit grows FASTER than revenue. Costs are scaling
       sub-linearly — each additional revenue dollar is more profitable
       than the last. Sign of a scalable, efficient business model.

    2. Margin Compression (risk):
       Revenue grows but operating profit lags. Costs are rising faster
       than sales. The company can grow itself into trouble if unchecked.

    Only fires when both YoY growth metrics are available (2+ years of data).

    Thresholds:
      Leverage:    op_profit_growth > rev_growth + 5 percentage points
      Compression: rev_growth > 3% AND op_profit_growth < rev_growth - 5pp
    """
    rev_m = metrics.get("revenue_growth_yoy")
    op_m  = metrics.get("operating_profit_growth_yoy")

    if rev_m is None or op_m is None:
        return None

    rev_growth = rev_m["value"]
    op_growth  = op_m["value"]
    spread     = op_growth - rev_growth

    if op_growth > rev_growth + 0.05 and rev_growth > 0:
        return _signal(
            name="Operational Leverage",
            kind="strength",
            metric="operating_profit_growth_yoy",
            value=op_growth,
            detail=(
                f"Operating profit grew {op_growth:.1%} while revenue grew "
                f"{rev_growth:.1%} — a {spread:.1%} spread. Costs are scaling "
                "sub-linearly, indicating an increasingly efficient business model."
            ),
        )

    if rev_growth > 0.03 and op_growth < rev_growth - 0.05:
        return _signal(
            name="Margin Compression",
            kind="risk",
            metric="operating_profit_growth_yoy",
            value=op_growth,
            detail=(
                f"Revenue grew {rev_growth:.1%} but operating profit grew only "
                f"{op_growth:.1%} — a {abs(spread):.1%} lag. Costs are rising "
                "faster than sales, compressing margins as the top line grows."
            ),
        )

    return None


# ---------------------------------------------------------------------------
# MASTER FUNCTION
# ---------------------------------------------------------------------------

_TYPE_ORDER = {"strength": 0, "observation": 1, "risk": 2}


def detect_signals(metrics: dict) -> list[dict]:
    """
    Run all signal rules against a metrics bundle and return the findings.

    Args:
        metrics: the dict returned by compute_all_metrics() in metrics.py

    Returns:
        A list of signal dicts sorted by type: strengths first,
        then observations, then risks. Each signal has:
            name    (str)   — short label
            type    (str)   — "strength" | "observation" | "risk"
            metric  (str)   — which metric triggered this signal
            value   (float) — the metric value at time of detection
            detail  (str)   — plain-English explanation

    Example:
        metrics = compute_all_metrics(df)
        signals = detect_signals(metrics)
        for s in signals:
            print(f"[{s['type'].upper()}] {s['name']}: {s['detail']}")
    """
    candidates = [
        _check_gross_margin(metrics),
        _check_operating_margin(metrics),
        _check_revenue_growth(metrics),
        _check_debt_load(metrics),
        _check_cash_cushion(metrics),
        _check_operational_leverage(metrics),  # cross-metric — runs last
    ]

    signals = [s for s in candidates if s is not None]
    signals.sort(key=lambda s: _TYPE_ORDER[s["type"]])

    return signals
