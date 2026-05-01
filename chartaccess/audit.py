"""Audit chart metadata against accessibility and inclusivity requirements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .color import contrast_ratio

MIN_CONTRAST_RATIO = 3.0
MIN_FONT_SIZE = 14
MIN_ALT_TEXT_WORDS = 8


@dataclass(frozen=True)
class AuditFinding:
    """A single requirement check result."""

    requirement: str
    passed: bool
    detail: str


def _word_count(text: str) -> int:
    return len([word for word in text.strip().split() if word])


def _has_text(chart: dict[str, Any], key: str) -> bool:
    return bool(str(chart.get(key, "")).strip())


def audit_chart(chart: dict[str, Any]) -> list[AuditFinding]:
    """Return accessibility findings for a chart specification dictionary."""
    findings: list[AuditFinding] = []
    background = chart.get("background", "#ffffff")

    colors = chart.get("colors", [])
    low_contrast = []
    for color in colors:
        ratio = contrast_ratio(str(color), str(background))
        if ratio < MIN_CONTRAST_RATIO:
            low_contrast.append(f"{color} ({ratio:.2f}:1)")

    findings.append(
        AuditFinding(
            "All data colors meet minimum contrast against the chart background",
            not low_contrast,
            "Low-contrast colors: " + ", ".join(low_contrast)
            if low_contrast
            else f"All {len(colors)} colors meet {MIN_CONTRAST_RATIO}:1 contrast.",
        )
    )

    font_size = int(chart.get("font_size", 0) or 0)
    findings.append(
        AuditFinding(
            "Chart text uses at least 12 pt font",
            font_size >= MIN_FONT_SIZE,
            f"Font size is {font_size} pt; minimum is {MIN_FONT_SIZE} pt.",
        )
    )

    required_text = ["title", "x_label", "y_label"]
    missing = [key for key in required_text if not _has_text(chart, key)]
    findings.append(
        AuditFinding(
            "Chart includes title and axis labels",
            not missing,
            "Missing fields: " + ", ".join(missing) if missing else "Title and axis labels are present.",
        )
    )

    alt_text = str(chart.get("alt_text", ""))
    findings.append(
        AuditFinding(
            "Alt text explains the chart in plain language",
            _word_count(alt_text) >= MIN_ALT_TEXT_WORDS,
            f"Alt text has {_word_count(alt_text)} words; minimum is {MIN_ALT_TEXT_WORDS}.",
        )
    )

    return findings


def summarize(findings: list[AuditFinding]) -> dict[str, Any]:
    """Summarize findings for display or tests."""
    passed = sum(1 for finding in findings if finding.passed)
    return {
        "passed": passed,
        "total": len(findings),
        "score": round(passed / len(findings), 2) if findings else 0,
        "overall_pass": passed == len(findings),
    }
