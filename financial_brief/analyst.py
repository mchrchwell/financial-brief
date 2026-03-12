"""
analyst.py — Stage 4: Claude-powered financial analysis.

generate_analysis(enriched_signals, metrics, company_name)
    Calls the Claude API and returns a structured dict with four keys:
    executive_summary, strengths, risks, observations.

build_prompt(enriched_signals, metrics, company_name)
    Returns the user-turn prompt string without making an API call,
    so callers can inspect or log it before committing to a request.

Each item in strengths / risks / observations carries:
    finding  – the analytical insight
    framework – exactly as labeled in the input signal
    source    – exactly as labeled in the input signal

Expected enriched_signals shape (list of dicts):
    [
        {
            "signal":    "Revenue declined 12% YoY ...",
            "framework": "DuPont Analysis",
            "source":    "10-K FY2024, p. 42",
            "category":  "risk"   # "strength" | "risk" | "observation"
        },
        ...
    ]

Expected metrics shape (dict of scalar values):
    {
        "revenue_usd_m": 1240,
        "gross_margin_pct": 38.4,
        ...
    }
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import anthropic


def _to_serializable(obj):
    """Convert numpy/pandas types to plain Python for JSON serialization."""
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(v) for v in obj]
    return obj

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior financial analyst producing internal executive briefings.

Rules you must follow without exception:
1. FRAMEWORKS AND SOURCES — Only cite frameworks and sources that appear verbatim in the signals provided to you. Never introduce a framework, methodology, or source of your own.
2. NUMBERS — Never introduce any figure, percentage, ratio, or metric that is not already present in the metrics block. Quote metrics exactly as given; do not round, derive, or estimate additional figures.
3. SCOPE — This is an internal analysis only. Do not benchmark against industry averages, sector peers, or external indices. All comparisons must be internal (e.g., year-over-year using provided data).
4. AUDIENCE — Write for a senior executive audience. Be direct and specific. No jargon, no hedging language, no filler phrases like "it is worth noting" or "it is important to consider".
5. ATTRIBUTION — Every finding in strengths, risks, and observations must reference the specific framework and source it comes from, as provided in the input.
6. FORMATTING — Format all ratio metrics as percentages (e.g. 0.32 → 32.0%). Format all large integers with comma separators (e.g. 416161000000 → $416,161,000,000). Never display raw decimals or unformatted integers in the output.

Output format — respond with valid JSON matching this schema exactly:
{
  "executive_summary": "<string: 3–5 sentence synthesis of the company's financial position>",
  "strengths": [
    {
      "finding":   "<specific positive insight>",
      "framework": "<framework name from input>",
      "source":    "<source citation from input>"
    }
  ],
  "risks": [
    {
      "finding":   "<specific concern or vulnerability>",
      "framework": "<framework name from input>",
      "source":    "<source citation from input>"
    }
  ],
  "observations": [
    {
      "finding":   "<neutral or mixed insight requiring executive attention>",
      "framework": "<framework name from input>",
      "source":    "<source citation from input>"
    }
  ]
}

Do not include any text outside the JSON object."""


# ---------------------------------------------------------------------------
# Prompt builder (public, testable without an API call)
# ---------------------------------------------------------------------------


def build_prompt(
    enriched_signals: list[dict[str, Any]],
    metrics: dict[str, Any],
    company_name: str,
) -> str:
    """Return the user-turn prompt without calling the API."""
    signals_block = json.dumps(_to_serializable(enriched_signals), indent=2)
    metrics_block = json.dumps(_to_serializable(metrics), indent=2)

    return f"""Company: {company_name}

=== METRICS (use only these numbers) ===
{metrics_block}

Note: When citing these metrics in your output, format ratio values as percentages \
(e.g. 0.32 → 32.0%) and large integers with comma separators \
(e.g. 416161000000 → $416,161,000,000).

=== SIGNALS (use only these frameworks and sources) ===
{signals_block}

Produce the analysis JSON now."""


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------


def generate_analysis(
    enriched_signals: list[dict[str, Any]],
    metrics: dict[str, Any],
    company_name: str,
) -> dict[str, Any]:
    """
    Call Claude and return a structured analysis dict.

    Returns:
        {
            "executive_summary": str,
            "strengths":     [{"finding": str, "framework": str, "source": str}, ...],
            "risks":         [{"finding": str, "framework": str, "source": str}, ...],
            "observations":  [{"finding": str, "framework": str, "source": str}, ...],
        }

    Raises:
        RuntimeError: if the API call fails, with status code and message.
    """
    client = anthropic.Anthropic()

    user_prompt = build_prompt(enriched_signals, metrics, company_name)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIStatusError as exc:
        raise RuntimeError(
            f"Claude API error {exc.status_code}: {exc.message}"
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError(f"Claude API connection error: {exc}") from exc

    raw_text = response.content[0].text

    try:
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
        result = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Claude returned non-JSON output: {exc}\n\nRaw response:\n{raw_text}"
        ) from exc

    # Validate top-level keys so callers get a clear error early.
    required_keys = {"executive_summary", "strengths", "risks", "observations"}
    missing = required_keys - result.keys()
    if missing:
        raise RuntimeError(
            f"Claude response is missing required keys: {missing}\n\nRaw response:\n{raw_text}"
        )

    return result
