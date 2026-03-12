"""
ingest.py — Data ingestion from Yahoo Finance via yfinance.

fetch_company_data(ticker_symbol) -> pd.DataFrame
    Returns a DataFrame with columns: year, revenue, cogs, opex, cash, debt
    Rows are complete (no NaNs), sorted by year ascending.

get_company_name(ticker_symbol) -> str
    Returns the company's full name from Yahoo Finance.
"""

import pandas as pd
import yfinance as yf

INCOME_FIELDS = {
    "revenue": "Total Revenue",
    "cogs":    "Cost Of Revenue",
    "opex":    "Operating Expense",
}

BALANCE_FIELDS = {
    "cash": "Cash And Cash Equivalents",
    "debt": "Total Debt",
}


def fetch_company_data(ticker_symbol: str) -> pd.DataFrame:
    """Fetch and return financial data for a ticker as a pipeline-ready DataFrame."""
    ticker = yf.Ticker(ticker_symbol)

    financials   = ticker.financials
    balance      = ticker.balance_sheet

    if financials is None or financials.empty:
        raise ValueError(f"No financial data found for ticker '{ticker_symbol}'. "
                         "Check that the symbol is valid.")
    if balance is None or balance.empty:
        raise ValueError(f"No balance sheet data found for ticker '{ticker_symbol}'.")

    rows = {}

    for col in financials.columns:
        year = col.year
        rows.setdefault(year, {})["year"] = year
        for field, label in INCOME_FIELDS.items():
            rows[year][field] = financials.loc[label, col] if label in financials.index else None

    for col in balance.columns:
        year = col.year
        rows.setdefault(year, {})["year"] = year
        for field, label in BALANCE_FIELDS.items():
            rows[year][field] = balance.loc[label, col] if label in balance.index else None

    df = pd.DataFrame(rows.values())

    required = ["year", "revenue", "cogs", "opex", "cash", "debt"]
    df = df[required].dropna().sort_values("year").reset_index(drop=True)
    df["year"] = df["year"].astype(int)

    if df.empty:
        raise ValueError(f"No complete rows (all six columns present) found for '{ticker_symbol}'.")

    return df


def get_company_name(ticker_symbol: str) -> str:
    """Return the company's full name from Yahoo Finance."""
    info = yf.Ticker(ticker_symbol).info
    name = info.get("longName") or info.get("shortName")
    if not name:
        raise ValueError(f"Could not retrieve company name for ticker '{ticker_symbol}'.")
    return name
