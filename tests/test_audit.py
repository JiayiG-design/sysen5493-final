import json
import unittest
from pathlib import Path

from chartaccess.audit import audit_chart, summarize
from chartaccess.color import contrast_ratio

ROOT = Path(__file__).resolve().parents[1]


class ChartAccessAuditTests(unittest.TestCase):
    def load_example(self, name):
        with (ROOT / "examples" / name).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_contrast_ratio_known_values(self):
        self.assertAlmostEqual(contrast_ratio("#000000", "#ffffff"), 21.0, places=1)

    def test_accessible_chart_passes_all_requirements(self):
        findings = audit_chart(self.load_example("good_chart.json"))
        self.assertTrue(summarize(findings)["overall_pass"])

    def test_inaccessible_chart_fails_multiple_requirements(self):
        findings = audit_chart(self.load_example("bad_chart.json"))
        failed_requirements = [finding.requirement for finding in findings if not finding.passed]

        self.assertIn("All data colors meet minimum contrast against the chart background", failed_requirements)
        self.assertIn("Chart text uses at least 12 pt font", failed_requirements)
        self.assertIn("Chart includes title and axis labels", failed_requirements)
        self.assertIn("Alt text explains the chart in plain language", failed_requirements)


if __name__ == "__main__":
    unittest.main()
