# ChartAccess Audit

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

## Why This Is A Systems Engineering Problem

Charts are part of decision systems. If a graph is hard to read, people may miss
risks, misunderstand tradeoffs, or be excluded from the analysis. This project
defines stakeholder needs as testable requirements, runs verification checks,
and produces a report that supports design iteration.
