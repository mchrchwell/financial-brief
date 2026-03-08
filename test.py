import pandas as pd
from financial_brief.metrics import compute_all_metrics

df = pd.DataFrame([
    {"year": 2022, "revenue": 1150000, "cogs": 690000, "opex": 270000, "cash": 180000, "debt": 350000},
    {"year": 2023, "revenue": 1300000, "cogs": 780000, "opex": 300000, "cash": 210000, "debt": 320000},
])

metrics = compute_all_metrics(df)
for name, m in metrics.items():
    print(f"{name}: {m['value']:.2%}")
    