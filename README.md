# Financial Brief

A Python pipeline that takes a company's financial CSV and produces an MBA-level executive brief with every finding cited back to real frameworks from top business school reading lists (Porter, Damodaran, Koller/McKinsey, Brealey/Myers/Allen, Higgins).

---

## How It Works

```
CSV Data  →  Metrics  →  Signals  →  Citations  →  Analysis  →  Report
              Stage 1     Stage 2      Stage 3       Stage 4     Stage 5
           (compute    (detect      (match each   (Claude     (formatted
            ratios)     what the     signal to     writes the   plain-text
                        numbers      library.json) brief)       output)
                        say)
```

1. **Metrics** — Computes standard financial ratios from the raw CSV (gross margin, operating margin, revenue growth, debt load, cash cushion, and more).
2. **Signals** — Applies deterministic threshold rules to identify what's notable: strengths, risks, and observations.
3. **Citations** — Looks up each signal in a curated library of 17 entries, attaching the framework name and source from real business school texts.
4. **Analysis** — Claude synthesizes the signals into an executive brief. It can only cite frameworks and sources explicitly provided in the library — no hallucinated references.
5. **Report** — Formats the analysis into clean, printable plain text and saves it to a `.txt` file.

---

## Installation

```bash
# Clone the repo and navigate to the project
cd FINANCIAL_BRIEF

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install anthropic pandas python-dotenv

# Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

---

## Usage

```bash
python3 main.py your_file.csv "Company Name"
```

Example:

```bash
python3 main.py data/acme_2024.csv "Acme Corp"
```

The report prints to the terminal and is saved as `acme_corp_report.txt`.

---

## Required CSV Format

The input CSV must contain these six columns:

| Column    | Description                        |
|-----------|------------------------------------|
| `year`    | Fiscal year (e.g. 2022, 2023)      |
| `revenue` | Total revenue                      |
| `cogs`    | Cost of goods sold                 |
| `opex`    | Operating expenses (excl. COGS)    |
| `cash`    | Cash and cash equivalents          |
| `debt`    | Total debt                         |

Multiple years of data are supported and recommended — year-over-year growth signals require at least two rows.

---

## Citation Library

The library covers 17 financial signals across four categories:

- **Profitability** — gross margin, operating margin
- **Growth** — revenue growth, operating profit growth, operational leverage, margin compression
- **Cost structure** — COGS ratio, Opex ratio
- **Leverage & liquidity** — debt load, cash cushion

Every signal is mapped to a specific framework and source from texts including:

- Porter, *Competitive Strategy* (1980)
- Damodaran, *Investment Valuation* (2012)
- Koller, Goedhart & Wessels / McKinsey, *Valuation* (2020)
- Brealey, Myers & Allen, *Principles of Corporate Finance* (2020)
- Higgins, *Analysis for Financial Management* (2012)

---

## Trust Layer

This pipeline is designed so Claude cannot fabricate citations. Every framework reference and source that appears in the output was explicitly provided in `library.json` before the API call was made. The system prompt instructs Claude to cite only what is in the input — and the input only contains what the library matched.

---

## Author

Matt Churchwell
