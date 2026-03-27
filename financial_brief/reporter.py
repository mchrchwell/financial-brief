"""
reporter.py — Stage 5: Report Generator.

generate_report(analysis, company_name, year) -> str
    Formats the Stage 4 analysis dict into clean plain-text output.

save_report(report_text, path)
    Writes the report string to a .txt file.
"""


def generate_report(analysis: dict, company_name: str, year: int | str, sector: str | None = None) -> str:
    sector_label = (sector or "general").replace("_", " ").title()
    lines = []

    # Header
    lines.append(f"{company_name} -- Financial Brief {year}")
    lines.append(f"Sector: {sector_label}")
    lines.append("=" * 60)
    lines.append("")

    # Executive Summary
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 60)
    lines.append(analysis["executive_summary"])
    lines.append("")

    # Sections
    sections = [
        ("STRENGTHS",    analysis["strengths"]),
        ("RISKS",        analysis["risks"]),
        ("OBSERVATIONS", analysis["observations"]),
    ]

    for title, items in sections:
        lines.append(title)
        lines.append("-" * 60)
        for item in items:
            lines.append(item["finding"])
            lines.append(f"  Framework: {item['framework']}  |  Source: {item['source']}")
            lines.append("")
        if not items:
            lines.append("None identified.")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def save_report(report_text: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(report_text)
