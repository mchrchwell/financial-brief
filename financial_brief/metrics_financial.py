"""
metrics_financial.py — Stage 1 (Financial Sector): Metrics Engine

compute_all_metrics_financial(df: pd.DataFrame) -> dict
    Computes sector-appropriate metrics for banks and brokerages.
    Input DataFrame must have columns produced by fetch_company_data_financial().

Same metric structure as metrics.py: {value, year, formula, sources}.
"""

import pandas as pd


def _get(df: pd.DataFrame, year: int, column: str):
    return df.loc[df["year"] == year, column].iloc[0]


def _to_serializable(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(v) for v in obj]
    return obj


def net_interest_margin(df, year):
    nim = _get(df, year, "net_interest_income")
    rev = _get(df, year, "revenue")
    return {"value": nim / rev, "year": year,
            "formula": "net_interest_income / revenue",
            "sources": {"net_interest_income": nim, "revenue": rev}}


def efficiency_ratio(df, year):
    opex = _get(df, year, "opex")
    rev  = _get(df, year, "revenue")
    return {"value": opex / rev, "year": year,
            "formula": "opex / revenue",
            "sources": {"opex": opex, "revenue": rev}}


def roe(df, year):
    ni     = _get(df, year, "net_income")
    equity = _get(df, year, "equity")
    return {"value": ni / equity, "year": year,
            "formula": "net_income / equity",
            "sources": {"net_income": ni, "equity": equity}}


def pretax_margin(df, year):
    pti = _get(df, year, "pretax_income")
    rev = _get(df, year, "revenue")
    return {"value": pti / rev, "year": year,
            "formula": "pretax_income / revenue",
            "sources": {"pretax_income": pti, "revenue": rev}}


def net_margin(df, year):
    ni  = _get(df, year, "net_income")
    rev = _get(df, year, "revenue")
    return {"value": ni / rev, "year": year,
            "formula": "net_income / revenue",
            "sources": {"net_income": ni, "revenue": rev}}


def leverage_ratio(df, year):
    assets = _get(df, year, "total_assets")
    equity = _get(df, year, "equity")
    return {"value": assets / equity, "year": year,
            "formula": "total_assets / equity",
            "sources": {"total_assets": assets, "equity": equity}}


def debt_to_equity(df, year):
    debt   = _get(df, year, "total_debt")
    equity = _get(df, year, "equity")
    return {"value": debt / equity, "year": year,
            "formula": "total_debt / equity",
            "sources": {"total_debt": debt, "equity": equity}}


def revenue_growth_yoy(df, year):
    years = sorted(df["year"].unique())
    idx   = years.index(year)
    if idx == 0:
        raise ValueError(f"No prior year available to compute growth for {year}.")
    prior     = years[idx - 1]
    rev_now   = _get(df, year, "revenue")
    rev_prior = _get(df, prior, "revenue")
    return {"value": (rev_now - rev_prior) / rev_prior, "year": year,
            "formula": "(revenue_t - revenue_t1) / revenue_t1",
            "sources": {"revenue_t": rev_now, "revenue_t1": rev_prior,
                        "year_t": year, "year_t1": prior}}


def compute_all_metrics_financial(df: pd.DataFrame) -> dict:
    """Compute all financial-sector metrics for the latest year in the DataFrame."""
    df          = df.sort_values("year").reset_index(drop=True)
    latest_year = int(df["year"].max())
    has_prior   = len(df["year"].unique()) >= 2

    metrics = {
        "net_interest_margin": net_interest_margin(df, latest_year),
        "efficiency_ratio":    efficiency_ratio(df, latest_year),
        "roe":                 roe(df, latest_year),
        "pretax_margin":       pretax_margin(df, latest_year),
        "net_margin":          net_margin(df, latest_year),
        "leverage_ratio":      leverage_ratio(df, latest_year),
        "debt_to_equity":      debt_to_equity(df, latest_year),
    }

    if has_prior:
        metrics["revenue_growth_yoy"] = revenue_growth_yoy(df, latest_year)

    return _to_serializable(metrics)
