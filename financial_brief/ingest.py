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


FINANCIAL_INCOME_FIELDS = {
    "revenue":            "Total Revenue",
    "net_interest_income": "Net Interest Income",
    "opex":               "Selling General And Administration",
    "pretax_income":      "Pretax Income",
    "net_income":         "Net Income",
}

FINANCIAL_BALANCE_FIELDS = {
    "cash":         "Cash And Cash Equivalents",
    "equity":       "Common Stock Equity",
    "total_assets": "Total Assets",
    "total_debt":   "Total Debt",
}


def fetch_company_data_financial(ticker_symbol: str) -> pd.DataFrame:
    """Fetch financial-sector data (banks, brokerages) as a pipeline-ready DataFrame.

    Output columns: year, revenue, net_interest_income, opex, pretax_income,
                    net_income, cash, equity, total_assets, total_debt
    """
    ticker = yf.Ticker(ticker_symbol)

    financials = ticker.financials
    balance    = ticker.balance_sheet

    if financials is None or financials.empty:
        raise ValueError(f"No financial data found for ticker '{ticker_symbol}'. "
                         "Check that the symbol is valid.")
    if balance is None or balance.empty:
        raise ValueError(f"No balance sheet data found for ticker '{ticker_symbol}'.")

    rows = {}

    for col in financials.columns:
        year = col.year
        rows.setdefault(year, {})["year"] = year
        for field, label in FINANCIAL_INCOME_FIELDS.items():
            rows[year][field] = financials.loc[label, col] if label in financials.index else None

    for col in balance.columns:
        year = col.year
        rows.setdefault(year, {})["year"] = year
        for field, label in FINANCIAL_BALANCE_FIELDS.items():
            rows[year][field] = balance.loc[label, col] if label in balance.index else None

    required = ["year", "revenue", "net_interest_income", "opex", "pretax_income",
                "net_income", "cash", "equity", "total_assets", "total_debt"]
    df = pd.DataFrame(rows.values())
    df = df[required].dropna().sort_values("year").reset_index(drop=True)
    df["year"] = df["year"].astype(int)

    if df.empty:
        raise ValueError(
            f"No complete rows (all ten columns present) found for '{ticker_symbol}'."
        )

    return df


FINANCIAL_SECTORS = {"Financial Services", "Finance", "Banking", "Insurance"}

SECTOR_MAP = {
    "Technology":             "technology",
    "Healthcare":             "healthcare",
    "Consumer Cyclical":      "consumer_cyclical",
    "Consumer Defensive":     "consumer_defensive",
    "Industrials":            "industrials",
    "Energy":                 "energy",
    "Communication Services": "communication_services",
    "Financial Services":     "financial_services",
    "Finance":                "financial_services",
    "Banking":                "financial_services",
    "Insurance":              "financial_services",
}


def get_sector(ticker_symbol: str) -> str:
    """Return an internal sector code based on yfinance sector string."""
    info   = yf.Ticker(ticker_symbol).info
    sector = info.get("sector") if info else None
    if not sector:
        print(f"[get_sector] Warning: no sector found for {ticker_symbol}, defaulting to 'general'.")
        return "general"
    code = SECTOR_MAP.get(sector)
    if code is None:
        print(f"[get_sector] Warning: unmapped sector '{sector}' for {ticker_symbol}, defaulting to 'general'.")
        return "general"
    return code
