"""Command-line interface for ChartAccess Audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import audit_chart, summarize


def load_chart(path: Path) -> dict:
    """Load a chart specification from JSON."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def format_report(chart: dict, source: Path) -> str:
    """Return a readable text report for a chart audit."""
    findings = audit_chart(chart)
    summary = summarize(findings)
    lines = [
        "ChartAccess Audit Report",
        f"Source: {source}",
        f"Score: {summary['passed']}/{summary['total']}",
        f"Overall: {'PASS' if summary['overall_pass'] else 'NEEDS WORK'}",
        "",
    ]
    for finding in findings:
        marker = "PASS" if finding.passed else "FAIL"
        lines.append(f"[{marker}] {finding.requirement}")
        lines.append(f"       {finding.detail}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a chart JSON file for accessibility requirements.")
    parser.add_argument("chart_json", type=Path, help="Path to a chart metadata JSON file.")
    args = parser.parse_args()

    chart = load_chart(args.chart_json)
    print(format_report(chart, args.chart_json))
    return 0 if summarize(audit_chart(chart))["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
