import sys
import unittest
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import db as db_module
from engine.simulations import simulate_road_closure, simulate_new_facility
from app.llm import explain_locally
from app.reports import generate_report, _risk_level


class TestExplainLocally(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_every_number_in_explanation_traces_to_input(self):
        result = simulate_road_closure(self.conn, 16)
        text = explain_locally(result)
        m = result["metrics"]
        self.assertIn(str(m["avg_hospital_route_delay_pct"]), text)
        self.assertIn(str(m["max_ambulance_delay_min"]), text)

    def test_redundant_road_produces_reassuring_not_alarming_text(self):
        result = simulate_road_closure(self.conn, 1)
        text = explain_locally(result)
        self.assertIn("No zone loses meaningful hospital access", text)

    def test_new_facility_zero_impact_says_so(self):
        result = simulate_new_facility(self.conn, "hospital", 13.052, 80.213, "Redundant Hospital")
        text = explain_locally(result)
        self.assertIn("does not improve coverage", text)

    def test_unknown_scenario_type_raises(self):
        with self.assertRaises(ValueError):
            explain_locally({"scenario_type": "not_a_real_type", "metrics": {}})


class TestReportGeneration(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_generates_valid_pdf_for_road_closure(self):
        result = simulate_road_closure(self.conn, 16)
        text = explain_locally(result)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.pdf")
            generate_report(result, text, path)
            self.assertTrue(os.path.exists(path))
            with open(path, "rb") as f:
                header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_generates_valid_pdf_for_new_facility(self):
        result = simulate_new_facility(self.conn, "hospital", 13.06, 80.22, "Test Hospital")
        text = explain_locally(result)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "report.pdf")
            generate_report(result, text, path)
            with open(path, "rb") as f:
                header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_risk_level_high_when_zones_cut_off(self):
        fake_result = {
            "scenario_type": "road_closure",
            "metrics": {"zones_cut_off_entirely": 2, "avg_hospital_route_delay_pct": 0, "max_ambulance_delay_min": 0},
        }
        label, _ = _risk_level(fake_result)
        self.assertEqual(label, "HIGH")

    def test_risk_level_minimal_when_no_impact(self):
        fake_result = {
            "scenario_type": "road_closure",
            "metrics": {"zones_cut_off_entirely": 0, "avg_hospital_route_delay_pct": 0, "max_ambulance_delay_min": 0},
        }
        label, _ = _risk_level(fake_result)
        self.assertEqual(label, "MINIMAL")


if __name__ == "__main__":
    unittest.main(verbosity=2)