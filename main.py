#!/usr/bin/env python3
"""
main.py — Entry point: wires all five stages together.

Usage:
    python3 main.py AAPL
    python3 main.py <csv_path> "Company Name"

Required CSV columns: year, revenue, cogs, opex, cash, debt
"""

import os
import re
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Fall back to environment variable already set

import pandas as pd

from financial_brief.ingest            import fetch_company_data, fetch_company_data_financial, get_company_name, get_sector
from financial_brief.metrics           import compute_all_metrics
from financial_brief.metrics_financial import compute_all_metrics_financial
from financial_brief.signals           import detect_signals
from financial_brief.signals_financial import detect_signals_financial
from financial_brief.signals_sector    import detect_signals_sector
from financial_brief.matcher           import load_library, match_citations
from financial_brief.analyst           import generate_analysis
from financial_brief.reporter          import generate_report, save_report

REQUIRED_COLUMNS = {"year", "revenue", "cogs", "opex", "cash", "debt"}
LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "financial_brief", "library.json")


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print("Usage: python3 main.py TICKER")
        print("       python3 main.py <csv_path> \"Company Name\"")
        sys.exit(1)

    first_arg = sys.argv[1]
    is_ticker = re.fullmatch(r"[A-Z]{1,5}", first_arg) is not None

    if is_ticker:
        ticker = first_arg
        try:
            company_name = get_company_name(ticker)
            sector       = get_sector(ticker)
            print(f"Sector detected: {sector}")
            if sector == "financial_services":
                df      = fetch_company_data_financial(ticker)
                metrics = compute_all_metrics_financial(df)
                signals = detect_signals_financial(metrics)
            else:
                df      = fetch_company_data(ticker)
                metrics = compute_all_metrics(df)
                signals = detect_signals_sector(metrics, sector)
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(1)
    else:
        if len(sys.argv) != 3:
            print("Usage: python3 main.py <csv_path> \"Company Name\"")
            sys.exit(1)

        csv_path, company_name = first_arg, sys.argv[2]

        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found: {csv_path}")
            sys.exit(1)

        df = pd.read_csv(csv_path)

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            print(f"Error: CSV is missing required columns: {', '.join(sorted(missing))}")
            sys.exit(1)

    year = int(df["year"].max())

    if not is_ticker:
        # Stage 1 — Metrics
        metrics = compute_all_metrics(df)

        # Stage 2 — Signals
        signals = detect_signals_sector(metrics, "general")

    # Stage 3 — Citations
    library = load_library(LIBRARY_PATH)
    enriched_signals = match_citations(signals, library)

    # Stage 4 — Analysis
    try:
        analysis = generate_analysis(enriched_signals, metrics, company_name)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    # Stage 5 — Report
    report = generate_report(analysis, company_name, year)

    print(report)

    filename = company_name.lower().replace(" ", "_") + "_report.txt"
    save_report(report, filename)
    print(f"Saved: {filename}")


if __name__ == "__main__":
    main()
