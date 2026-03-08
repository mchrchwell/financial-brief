import pandas as pd
from financial_brief.metrics import compute_all_metrics
from financial_brief.signals import detect_signals
from financial_brief.matcher import load_library, match_citations
from financial_brief.analyst import generate_analysis

df = pd.DataFrame([
    {"year": 2022, "revenue": 1150000, "cogs": 690000, "opex": 270000, "cash": 180000, "debt": 350000},
    {"year": 2023, "revenue": 1300000, "cogs": 780000, "opex": 300000, "cash": 210000, "debt": 320000},
])

metrics  = compute_all_metrics(df)
signals  = detect_signals(metrics)
library  = load_library("financial_brief/library.json")
enriched = match_citations(signals, library)

result = generate_analysis(enriched, metrics, "Acme Corp")

import json
print(json.dumps(result, indent=2))