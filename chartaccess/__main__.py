"""Command-line interface for ChartAccess Audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import audit_chart, summarize
from .image_audit import audit_png


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


def format_image_report(source: Path) -> str:
    """Return a readable text report for a PNG chart image."""
    findings, metadata = audit_png(source)
    summary = metadata["score"]
    lines = [
        "ChartAccess Image Audit Report",
        f"Source: {source}",
        f"Image: {metadata['width']} x {metadata['height']} px",
        f"Estimated background: {metadata['background']}",
        "Prominent colors: " + ", ".join(metadata["prominent_colors"]),
        f"Score: {summary['passed']}/{summary['total']}",
        f"Overall: {'PASS' if summary['overall_pass'] else 'NEEDS WORK'}",
        "",
    ]
    for finding in findings:
        marker = "PASS" if finding.passed else "FAIL"
        lines.append(f"[{marker}] {finding.requirement}")
        lines.append(f"       {finding.detail}")
    lines.extend(["", f"Note: {metadata['limitation']}"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a chart JSON file or PNG image for accessibility requirements.")
    parser.add_argument("input_path", type=Path, help="Path to a chart metadata JSON file or PNG image.")
    parser.add_argument("--image", action="store_true", help="Treat the input as a PNG chart image.")
    args = parser.parse_args()

    if args.image or args.input_path.suffix.lower() == ".png":
        findings, metadata = audit_png(args.input_path)
        print(format_image_report(args.input_path))
        return 0 if metadata["score"]["overall_pass"] else 1

    chart = load_chart(args.input_path)
    print(format_report(chart, args.input_path))
    return 0 if summarize(audit_chart(chart))["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
