"""
metrics.py — Stage 1: Metrics Engine
=====================================
Takes a pandas DataFrame of company financials and computes
standard financial ratios used in MBA-level analysis.

Expected CSV columns:
    year, revenue, cogs, opex, cash, debt

Everything this module produces is DETERMINISTIC — same inputs,
same outputs, every time. No AI involved at this stage.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# WHAT IS A "METRIC"?
#
# We represent every computed metric as a dictionary with four fields:
#
#   value   — the number itself
#   year    — which year it applies to
#   formula — a human-readable string showing how it was calculated
#   sources — the raw inputs that went into the formula
#
# Why this structure? Two reasons:
#   1. Auditability — you can always trace a number back to its source
#   2. Citations — later stages use the formula to match MBA frameworks
#
# Example:
#   {
#     "value": 0.40,
#     "year": 2023,
#     "formula": "(revenue - cogs) / revenue",
#     "sources": {"revenue": 1000000, "cogs": 600000}
#   }
# ---------------------------------------------------------------------------


def _get(df: pd.DataFrame, year: int, column: str):
    """
    Safely retrieve a single value from the DataFrame for a given year/column.

    The .iloc[0] at the end means "give me the first (and only) row
    that matches this year." If there's no data for that year,
    pandas will raise an IndexError — which is what we want,
    because silent failures are dangerous in financial tools.
    """
    return df.loc[df["year"] == year, column].iloc[0]


# ---------------------------------------------------------------------------
# PROFITABILITY METRICS
# These measure how much profit the company makes relative to revenue.
# Core reading: Porter (1985) — margin structure as competitive signal.
# ---------------------------------------------------------------------------

def gross_margin(df: pd.DataFrame, year: int) -> dict:
    """
    Gross Margin = (Revenue - COGS) / Revenue

    What it tells you: how much of each dollar of revenue is left
    after paying for the direct cost of producing goods/services.
    A higher gross margin means more room to cover overhead and still profit.
    """
    revenue = _get(df, year, "revenue")
    cogs    = _get(df, year, "cogs")
    gp      = revenue - cogs

    return {
        "value":   gp / revenue,
        "year":    year,
        "formula": "(revenue - cogs) / revenue",
        "sources": {"revenue": revenue, "cogs": cogs},
    }


def operating_margin(df: pd.DataFrame, year: int) -> dict:
    """
    Operating Margin = (Revenue - COGS - Opex) / Revenue

    What it tells you: profitability after ALL operating costs —
    both the cost of goods and overhead (salaries, rent, marketing, etc.).
    This is the most important margin for assessing operational efficiency.
    """
    revenue = _get(df, year, "revenue")
    cogs    = _get(df, year, "cogs")
    opex    = _get(df, year, "opex")
    op      = revenue - cogs - opex

    return {
        "value":   op / revenue,
        "year":    year,
        "formula": "(revenue - cogs - opex) / revenue",
        "sources": {"revenue": revenue, "cogs": cogs, "opex": opex},
    }


# ---------------------------------------------------------------------------
# GROWTH METRICS
# These measure trajectory — is the business expanding or contracting?
# Core reading: Higgins (2007) — sustainable growth rate framework.
# ---------------------------------------------------------------------------

def revenue_growth_yoy(df: pd.DataFrame, year: int) -> dict:
    """
    YoY Revenue Growth = (Revenue_t - Revenue_t-1) / Revenue_t-1

    What it tells you: how fast the top line is growing year over year.
    Positive = expanding. Negative = contracting.

    Requires at least two years of data.
    """
    years = sorted(df["year"].unique())
    if year not in years:
        raise ValueError(f"Year {year} not found in data.")

    idx = years.index(year)
    if idx == 0:
        raise ValueError(f"No prior year available to compute growth for {year}.")

    prior_year    = years[idx - 1]
    revenue_now   = _get(df, year, "revenue")
    revenue_prior = _get(df, prior_year, "revenue")

    return {
        "value":   (revenue_now - revenue_prior) / revenue_prior,
        "year":    year,
        "formula": "(revenue_t - revenue_t1) / revenue_t1",
        "sources": {
            "revenue_t":  revenue_now,
            "revenue_t1": revenue_prior,
            "year_t":     year,
            "year_t1":    prior_year,
        },
    }


def operating_profit_growth_yoy(df: pd.DataFrame, year: int) -> dict:
    """
    YoY Operating Profit Growth = (OpProfit_t - OpProfit_t-1) / |OpProfit_t-1|

    What it tells you: whether profitability is growing faster or slower
    than revenue. If revenue grows 10% but operating profit grows 5%,
    that's a margin compression signal — costs are rising faster than sales.

    Note: we use absolute value of prior year in denominator to handle
    cases where prior year was a small negative number.
    """
    years = sorted(df["year"].unique())
    idx   = years.index(year)
    if idx == 0:
        raise ValueError(f"No prior year available for {year}.")

    prior_year = years[idx - 1]

    def op_profit(y):
        r = _get(df, y, "revenue")
        c = _get(df, y, "cogs")
        o = _get(df, y, "opex")
        return r - c - o

    op_now   = op_profit(year)
    op_prior = op_profit(prior_year)

    if abs(op_prior) < 1e-9:
        raise ValueError("Prior year operating profit is zero; growth undefined.")

    return {
        "value":   (op_now - op_prior) / abs(op_prior),
        "year":    year,
        "formula": "(op_profit_t - op_profit_t1) / abs(op_profit_t1)",
        "sources": {
            "op_profit_t":  op_now,
            "op_profit_t1": op_prior,
            "year_t":       year,
            "year_t1":      prior_year,
        },
    }


# ---------------------------------------------------------------------------
# COST STRUCTURE METRICS
# These measure how costs behave relative to revenue.
# Core reading: Horngren et al. — Cost Accounting: A Managerial Emphasis.
# ---------------------------------------------------------------------------

def cogs_ratio(df: pd.DataFrame, year: int) -> dict:
    """
    COGS Ratio = COGS / Revenue

    What it tells you: what fraction of every revenue dollar is consumed
    by direct production costs. Rising COGS ratio = eroding gross margin.
    """
    revenue = _get(df, year, "revenue")
    cogs    = _get(df, year, "cogs")

    return {
        "value":   cogs / revenue,
        "year":    year,
        "formula": "cogs / revenue",
        "sources": {"revenue": revenue, "cogs": cogs},
    }


def opex_ratio(df: pd.DataFrame, year: int) -> dict:
    """
    Opex Ratio = Opex / Revenue

    What it tells you: what fraction of revenue goes to operating overhead.
    A spike in this ratio (relative to prior years) often signals investment
    in growth, restructuring costs, or loss of cost discipline.
    """
    revenue = _get(df, year, "revenue")
    opex    = _get(df, year, "opex")

    return {
        "value":   opex / revenue,
        "year":    year,
        "formula": "opex / revenue",
        "sources": {"revenue": revenue, "opex": opex},
    }


# ---------------------------------------------------------------------------
# LIQUIDITY & LEVERAGE METRICS
# These measure financial risk and the ability to meet obligations.
# Core reading: Brealey, Myers & Allen — Principles of Corporate Finance.
# ---------------------------------------------------------------------------

def debt_to_revenue(df: pd.DataFrame, year: int) -> dict:
    """
    Debt-to-Revenue = Debt / Revenue

    What it tells you: how much debt the company carries relative to its
    top-line revenue. Not a standard ratio (debt-to-equity is more common),
    but useful when equity data isn't available — which is often the case
    with simplified financial uploads.
    """
    revenue = _get(df, year, "revenue")
    debt    = _get(df, year, "debt")

    return {
        "value":   debt / revenue,
        "year":    year,
        "formula": "debt / revenue",
        "sources": {"revenue": revenue, "debt": debt},
    }


def cash_to_revenue(df: pd.DataFrame, year: int) -> dict:
    """
    Cash-to-Revenue = Cash / Revenue

    What it tells you: the company's liquidity cushion relative to its size.
    A very low ratio may signal vulnerability to short-term shocks.
    """
    revenue = _get(df, year, "revenue")
    cash    = _get(df, year, "cash")

    return {
        "value":   cash / revenue,
        "year":    year,
        "formula": "cash / revenue",
        "sources": {"revenue": revenue, "cash": cash},
    }


# ---------------------------------------------------------------------------
# MASTER FUNCTION
# This is the one function you'll call from outside this module.
# It runs all metrics for the most recent year and returns them
# as a single dictionary — the "metrics bundle."
# ---------------------------------------------------------------------------

def compute_all_metrics(df: pd.DataFrame) -> dict:
    """
    Compute all metrics for the latest year available in the DataFrame.
    Also computes YoY growth metrics if at least two years of data exist.

    Returns a flat dictionary:
        { "gross_margin": {...}, "operating_margin": {...}, ... }

    Each value is a metric dict with: value, year, formula, sources.
    """
    # Ensure the DataFrame is sorted by year (defensive programming —
    # we never assume the CSV was uploaded in the right order)
    df = df.sort_values("year").reset_index(drop=True)

    latest_year = int(df["year"].max())
    has_prior   = len(df["year"].unique()) >= 2

    metrics = {}

    # --- Profitability ---
    metrics["gross_margin"]     = gross_margin(df, latest_year)
    metrics["operating_margin"] = operating_margin(df, latest_year)

    # --- Cost Structure ---
    metrics["cogs_ratio"] = cogs_ratio(df, latest_year)
    metrics["opex_ratio"] = opex_ratio(df, latest_year)

    # --- Liquidity & Leverage ---
    metrics["debt_to_revenue"] = debt_to_revenue(df, latest_year)
    metrics["cash_to_revenue"] = cash_to_revenue(df, latest_year)

    # --- Growth (only if we have prior year data) ---
    if has_prior:
        metrics["revenue_growth_yoy"]         = revenue_growth_yoy(df, latest_year)
        metrics["operating_profit_growth_yoy"] = operating_profit_growth_yoy(df, latest_year)

    return metrics
