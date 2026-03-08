#!/usr/bin/env python3
"""
main.py — Entry point: wires all five stages together.

Usage:
    python3 main.py <csv_path> "Company Name"

Required CSV columns: year, revenue, cogs, opex, cash, debt
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Fall back to environment variable already set

import pandas as pd

from financial_brief.metrics  import compute_all_metrics
from financial_brief.signals  import detect_signals
from financial_brief.matcher  import load_library, match_citations
from financial_brief.analyst  import generate_analysis
from financial_brief.reporter import generate_report, save_report

REQUIRED_COLUMNS = {"year", "revenue", "cogs", "opex", "cash", "debt"}
LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "financial_brief", "library.json")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python3 main.py <csv_path> \"Company Name\"")
        sys.exit(1)

    csv_path, company_name = sys.argv[1], sys.argv[2]

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        print(f"Error: CSV is missing required columns: {', '.join(sorted(missing))}")
        sys.exit(1)

    year = int(df["year"].max())

    # Stage 1 — Metrics
    metrics = compute_all_metrics(df)

    # Stage 2 — Signals
    signals = detect_signals(metrics)

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
