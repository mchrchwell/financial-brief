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

from financial_brief.analyst  import generate_analysis
from financial_brief.matcher  import load_library, match_citations
from financial_brief.metrics  import compute_all_metrics
from financial_brief.reporter import generate_report
from financial_brief.signals  import detect_signals

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
      <p>Upload a company's financial CSV and get an MBA-level executive brief,
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

        <label for="company_name">Company Name</label>
        <input type="text" id="company_name" name="company_name"
               placeholder="e.g. Acme Corp"
               value="{{ company_name | e }}" required />

        <label for="csv_file">Financial Data (CSV)</label>
        <input type="file" id="csv_file" name="csv_file"
               accept=".csv" required />
        <p class="columns-note">
          Required columns: year, revenue, cogs, opex, cash, debt
        </p>

        <button type="submit" id="submit-btn">Generate Brief</button>
      </form>

      <div class="loading" id="loading">
        <span class="spinner"></span>
        Analyzing&hellip; this takes about 10&ndash;20 seconds.
      </div>
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
        company_name = request.form.get("company_name", "").strip()
        file = request.files.get("csv_file")

        try:
            if not company_name:
                raise ValueError("Company name is required.")
            if not file or file.filename == "":
                raise ValueError("Please upload a CSV file.")

            df = pd.read_csv(io.StringIO(file.read().decode("utf-8")))

            missing = REQUIRED_COLUMNS - set(df.columns)
            if missing:
                raise ValueError(
                    f"CSV is missing required columns: {', '.join(sorted(missing))}"
                )

            year = int(df["year"].max())
            metrics          = compute_all_metrics(df)
            signals          = detect_signals(metrics)
            library          = load_library(LIBRARY_PATH)
            enriched_signals = match_citations(signals, library)
            analysis         = generate_analysis(enriched_signals, metrics, company_name)
            report           = generate_report(analysis, company_name, year)

        except Exception as exc:
            error = str(exc)

    return render_template_string(
        HTML, report=report, error=error, company_name=company_name
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)