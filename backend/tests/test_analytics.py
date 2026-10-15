import sys
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import db as db_module
from engine.simulations import simulate_road_closure
from engine.analytics import (
    compute_dashboard_summary, compute_infrastructure_health,
    compute_emergency_response_coverage, compute_scenario_trends,
)

REAL_DB_PATH = Path(__file__).parent.parent / "data" / "city.db"


class TestDashboardSummary(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_counts_match_known_generated_dataset(self):
        summary = compute_dashboard_summary(self.conn)
        self.assertEqual(summary["total_road_segments"], 84)
        self.assertEqual(summary["population_zones"], 12)
        self.assertEqual(summary["total_population_tracked"], 168900)
        self.assertEqual(summary["facility_counts"]["hospital"], 3)

    def test_arterial_plus_local_equals_total(self):
        summary = compute_dashboard_summary(self.conn)
        self.assertEqual(
            summary["arterial_road_segments"] + summary["local_road_segments"],
            summary["total_road_segments"],
        )


class TestInfrastructureHealth(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_full_coverage_scores_100(self):
        health = compute_infrastructure_health(self.conn)
        self.assertEqual(health["coverage_gaps"], [])
        self.assertEqual(health["infrastructure_health_score"], 100.0)

    def test_removing_all_fire_stations_creates_a_real_gap(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_db = Path(d) / "test_city.db"
            shutil.copy(REAL_DB_PATH, tmp_db)
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row
            conn.execute("DELETE FROM facilities WHERE facility_type = 'fire_station'")
            conn.commit()

            health = compute_infrastructure_health(conn)
            self.assertLess(health["infrastructure_health_score"], 100.0)
            gap_types = [g["facility_type"] for g in health["coverage_gaps"]]
            self.assertIn("fire_station", gap_types)
            conn.close()


class TestEmergencyResponseCoverage(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_every_zone_has_a_response_time(self):
        coverage = compute_emergency_response_coverage(self.conn)
        self.assertEqual(len(coverage["zone_detail"]), 12)
        for z in coverage["zone_detail"]:
            self.assertIsNotNone(z["fire_response_min"])
            self.assertIsNotNone(z["police_response_min"])

    def test_worst_response_time_is_actually_the_max(self):
        coverage = compute_emergency_response_coverage(self.conn)
        times = [z["fire_response_min"] for z in coverage["zone_detail"]]
        self.assertEqual(coverage["worst_fire_response_min"], max(times))

    def test_removing_fire_stations_increases_response_times(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_db = Path(d) / "test_city.db"
            shutil.copy(REAL_DB_PATH, tmp_db)
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row

            before = compute_emergency_response_coverage(conn)
            conn.execute(
                "DELETE FROM facilities WHERE facility_type = 'fire_station' "
                "AND name != 'Riverside Fire Outpost'"
            )
            conn.commit()
            after = compute_emergency_response_coverage(conn)

            self.assertGreaterEqual(after["avg_fire_response_min"], before["avg_fire_response_min"])
            conn.close()


class TestScenarioTrends(unittest.TestCase):
    def test_empty_history_is_honest_not_faked(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_db = Path(d) / "test_city.db"
            shutil.copy(REAL_DB_PATH, tmp_db)
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row

            trends = compute_scenario_trends(conn)
            self.assertEqual(trends["total_scenarios_run"], 0)
            self.assertEqual(trends["by_type"], {})
            conn.close()

    def test_trends_reflect_real_saved_scenarios(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_db = Path(d) / "test_city.db"
            shutil.copy(REAL_DB_PATH, tmp_db)
            conn = sqlite3.connect(tmp_db)
            conn.row_factory = sqlite3.Row

            import json
            result = simulate_road_closure(conn, 16)
            db_module.save_scenario(conn, "road_closure", "{}", json.dumps(result))
            result2 = simulate_road_closure(conn, 1)
            db_module.save_scenario(conn, "road_closure", "{}", json.dumps(result2))

            trends = compute_scenario_trends(conn)
            self.assertEqual(trends["total_scenarios_run"], 2)
            self.assertEqual(trends["by_type"]["road_closure"], 2)
            conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)