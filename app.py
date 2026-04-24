"""
app.py — Flask web interface for the Financial Brief pipeline.

Usage:
    python3 app.py
    Then open http://localhost:5000
"""

import io
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pandas as pd
from flask import Flask, render_template_string, request

from financial_brief.analyst           import generate_analysis
from financial_brief.ingest            import fetch_company_data, fetch_company_data_financial, get_company_name, get_sector
from financial_brief.matcher           import load_library, match_citations
from financial_brief.metrics           import compute_all_metrics
from financial_brief.metrics_financial import compute_all_metrics_financial
from financial_brief.reporter          import generate_report
from financial_brief.signals           import detect_signals
from financial_brief.signals_financial import detect_signals_financial
from financial_brief.signals_sector    import detect_signals_sector

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

REQUIRED_COLUMNS = {"year", "revenue", "cogs", "opex", "cash", "debt"}
LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "financial_brief", "library.json")

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Financial Brief</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      background: #f4f5f7;
      color: #1a1a2e;
      min-height: 100vh;
      padding: 48px 16px;
    }

    .container { max-width: 720px; margin: 0 auto; }

    header { margin-bottom: 36px; }
    header h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.3px; }
    header p  { margin-top: 6px; color: #555; font-size: 0.95rem; line-height: 1.5; }

    .card {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 32px;
      margin-bottom: 28px;
    }

    label { display: block; font-size: 0.85rem; font-weight: 600;
            color: #333; margin-bottom: 6px; }

    input[type="text"], input[type="file"] {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid #ccc;
      border-radius: 6px;
      font-size: 0.95rem;
      margin-bottom: 20px;
      background: #fafafa;
    }
    input[type="text"]:focus, input[type="file"]:focus {
      outline: none;
      border-color: #4a6cf7;
      background: #fff;
    }

    .columns-note {
      font-size: 0.8rem;
      color: #777;
      margin-top: -14px;
      margin-bottom: 20px;
    }

    .divider {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 4px 0 24px;
      color: #aaa;
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.05em;
    }
    .divider::before, .divider::after {
      content: "";
      flex: 1;
      height: 1px;
      background: #e0e0e0;
    }

    button[type="submit"] {
      width: 100%;
      padding: 12px;
      background: #1a1a2e;
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    button[type="submit"]:hover    { background: #2e2e50; }
    button[type="submit"]:disabled { background: #888; cursor: not-allowed; }

    .loading {
      display: none;
      text-align: center;
      padding: 24px;
      color: #555;
      font-size: 0.95rem;
    }
    .spinner {
      display: inline-block;
      width: 22px; height: 22px;
      border: 3px solid #ddd;
      border-top-color: #1a1a2e;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      vertical-align: middle;
      margin-right: 10px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    .error {
      background: #fff5f5;
      border: 1px solid #f5c6c6;
      border-radius: 6px;
      padding: 16px 20px;
      color: #b00020;
      font-size: 0.9rem;
      margin-bottom: 28px;
    }
    .error strong { display: block; margin-bottom: 4px; }

    .report-card { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; }
    .report-header {
      padding: 20px 28px;
      border-bottom: 1px solid #e0e0e0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .report-header h2 { font-size: 1rem; font-weight: 600; }
    .report-body {
      padding: 28px;
      font-family: "SF Mono", "Fira Code", "Courier New", monospace;
      font-size: 0.82rem;
      line-height: 1.7;
      white-space: pre-wrap;
      color: #1a1a2e;
      overflow-x: auto;
    }
  </style>
</head>
<body>
  <div class="container">

    <header>
      <h1>Financial Brief</h1>
      <p>Enter a ticker symbol or upload a CSV to get an MBA-level executive brief,
         with every finding cited back to real frameworks.</p>
    </header>

    {% if error %}
    <div class="error">
      <strong>Error</strong>{{ error }}
    </div>
    {% endif %}

    <div class="card">
      <form method="POST" enctype="multipart/form-data"
            onsubmit="showLoading(event)">

        <label for="ticker">Ticker Symbol</label>
        <input type="text" id="ticker" name="ticker"
               placeholder="e.g. AAPL"
               value="{{ ticker | e }}"
               style="text-transform: uppercase;" />

        <div class="divider">or</div>

        <label for="csv_file">Upload CSV</label>
        <input type="file" id="csv_file" name="csv_file" accept=".csv" />
        <p class="columns-note">
          Required columns: year, revenue, cogs, opex, cash, debt
        </p>

        <label for="company_name">Company Name <span style="font-weight:400;color:#999;">(required with CSV)</span></label>
        <input type="text" id="company_name" name="company_name"
               placeholder="e.g. Acme Corp"
               value="{{ company_name | e }}" />

        <button type="submit" id="submit-btn">Generate Brief</button>
      </form>

      <div class="loading" id="loading">
        <span class="spinner"></span>
        Analyzing&hellip; this takes about 10&ndash;20 seconds.
      </div>
    </div>

    <div class="card" style="margin-bottom: 28px;">
      <h2 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 16px; letter-spacing: -0.1px;">How it works</h2>
      <ul style="list-style: none; padding: 0; margin: 0 0 14px; display: flex; flex-direction: column; gap: 10px;">
        <li style="font-size: 0.875rem; color: #444; line-height: 1.55; padding-left: 16px; position: relative;">
          <span style="position: absolute; left: 0; color: #aaa;">&rsaquo;</span>
          Pulls live financial data via Yahoo Finance for any public ticker
        </li>
        <li style="font-size: 0.875rem; color: #444; line-height: 1.55; padding-left: 16px; position: relative;">
          <span style="position: absolute; left: 0; color: #aaa;">&rsaquo;</span>
          Detects company sector and applies Damodaran NYU Stern (January 2026) sector-specific benchmarks across 7 sectors: Technology, Healthcare, Consumer Cyclical, Consumer Defensive, Industrials, Energy, and Communication Services. Financial Services firms use a dedicated pipeline.
        </li>
        <li style="font-size: 0.875rem; color: #444; line-height: 1.55; padding-left: 16px; position: relative;">
          <span style="position: absolute; left: 0; color: #aaa;">&rsaquo;</span>
          Identifies signals &mdash; strengths, risks, and observations &mdash; calibrated to sector peer benchmarks
        </li>
        <li style="font-size: 0.875rem; color: #444; line-height: 1.55; padding-left: 16px; position: relative;">
          <span style="position: absolute; left: 0; color: #aaa;">&rsaquo;</span>
          Every finding is cited to a real academic framework: Porter, Damodaran, Koller/McKinsey, Brealey/Myers/Allen, Higgins, or Rose &amp; Hudgins
        </li>
        <li style="font-size: 0.875rem; color: #444; line-height: 1.55; padding-left: 16px; position: relative;">
          <span style="position: absolute; left: 0; color: #aaa;">&rsaquo;</span>
          Analysis generated by Claude (Anthropic)
        </li>
      </ul>
      <p style="font-size: 0.8rem; color: #999; margin-top: 4px;">CSV upload available for private companies or custom datasets.</p>
    </div>

    {% if report %}
    <div class="report-card">
      <div class="report-header">
        <h2>Executive Brief</h2>
      </div>
      <div class="report-body">{{ report }}</div>
    </div>
    {% endif %}

  </div>

  <script>
    function showLoading(e) {
      const btn = document.getElementById("submit-btn");
      const loading = document.getElementById("loading");
      btn.disabled = true;
      btn.textContent = "Analyzing\u2026";
      loading.style.display = "block";
    }
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    report = None
    error = None
    company_name = ""

    if request.method == "POST":
        ticker       = request.form.get("ticker", "").strip().upper()
        company_name = request.form.get("company_name", "").strip()
        file         = request.files.get("csv_file")

        try:
            if ticker:
                company_name = get_company_name(ticker)
                sector       = get_sector(ticker)
                if sector == "financial_services":
                    df      = fetch_company_data_financial(ticker)
                    metrics = compute_all_metrics_financial(df)
                    signals = detect_signals_financial(metrics)
                else:
                    df      = fetch_company_data(ticker)
                    metrics = compute_all_metrics(df)
                    signals = detect_signals_sector(metrics, sector)
            elif file and file.filename != "":
                if not company_name:
                    raise ValueError("Company name is required when uploading a CSV.")
                df = pd.read_csv(io.StringIO(file.read().decode("utf-8")))
                missing = REQUIRED_COLUMNS - set(df.columns)
                if missing:
                    raise ValueError(
                        f"CSV is missing required columns: {', '.join(sorted(missing))}"
                    )
            else:
                raise ValueError("Please enter a ticker symbol or upload a CSV file.")

            year = int(df["year"].max())
            if not ticker:
                metrics = compute_all_metrics(df)
                signals = detect_signals_sector(metrics, "general")
            library          = load_library(LIBRARY_PATH)
            enriched_signals = match_citations(signals, library)
            analysis         = generate_analysis(enriched_signals, metrics, company_name)
            report           = generate_report(analysis, company_name, year, sector if ticker else "general")

        except Exception as exc:
            error = str(exc)

    return render_template_string(
        HTML, report=report, error=error, company_name=company_name,
        ticker=request.form.get("ticker", "").strip().upper() if request.method == "POST" else ""
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)