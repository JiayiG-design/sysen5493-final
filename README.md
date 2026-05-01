# ChartAccess Audit

[![CI](https://github.com/JiayiG-design/sysen5493-final/actions/workflows/ci.yml/badge.svg)](https://github.com/JiayiG-design/sysen5493-final/actions/workflows/ci.yml)

AI-augmented final project for SYSEN 5493.

ChartAccess Audit is a small command-line tool that checks whether a chart design
meets basic accessibility and inclusivity requirements. It turns graph design
guidelines into measurable checks for color contrast, font size, labels, and
plain-language alt text.

## Quick Start

```bash
python -m chartaccess examples/good_chart.json
python -m chartaccess examples/bad_chart.json
python -m unittest discover -s tests
```

The `good_chart.json` example should pass all requirements. The
`bad_chart.json` example should fail and explain what needs to be improved.

## Why This Is A Systems Engineering Problem

Charts are part of decision systems. If a graph is hard to read, people may miss
risks, misunderstand tradeoffs, or be excluded from the analysis. This project
defines stakeholder needs as testable requirements, runs verification checks,
and produces a report that supports design iteration.

## Requirements Checked

| Requirement | Verification Rule |
| --- | --- |
| Data colors are readable | Each data color must meet at least 3.0:1 contrast against the background |
| Text is readable | Chart font size must be at least 12 pt |
| Chart context is clear | Title, x-axis label, and y-axis label must be present |
| Screen-reader summary exists | Alt text must contain at least 8 words |

## Project Structure

```text
chartaccess/
  audit.py       # Requirement checks and scoring
  color.py       # WCAG contrast calculation
  __main__.py    # Command-line report
examples/
  good_chart.json
  bad_chart.json
tests/
  test_audit.py
docs/
  AI_COLLABORATION.md
```

## Demo Script

```bash
python -m chartaccess examples/good_chart.json
python -m chartaccess examples/bad_chart.json
python -m unittest discover -s tests
git log --oneline --graph --all
```

## AI Collaboration

See [docs/AI_COLLABORATION.md](docs/AI_COLLABORATION.md) for the prompt,
accepted suggestions, rejected suggestions, and reflection.
