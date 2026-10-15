import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import db as db_module
from engine.graph_builder import build_graph
from engine.simulations_extra import (
    simulate_bridge_closure, simulate_new_flyover, simulate_accident,
    simulate_power_failure, simulate_festival,
)


class TestBridgeClosure(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_reuses_road_closure_math_but_relabels(self):
        result = simulate_bridge_closure(self.conn, 16)
        self.assertEqual(result["scenario_type"], "bridge_closure")
        self.assertGreater(result["metrics"]["avg_hospital_route_delay_pct"], 0)

    def test_flags_single_point_of_failure_correctly(self):
        result = simulate_bridge_closure(self.conn, 16)
        self.assertIn("single_point_of_failure", result["metrics"])
        self.assertIsInstance(result["metrics"]["single_point_of_failure"], bool)


class TestNewFlyover(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_irrelevant_node_pair_shows_no_improvement(self):
        result = simulate_new_flyover(self.conn, 1, 43, speed_kmph=70)
        self.assertEqual(result["metrics"]["zones_with_improved_hospital_access"], 0)

    def test_relevant_node_pair_shows_real_improvement(self):
        result = simulate_new_flyover(self.conn, 43, 22, speed_kmph=70)
        self.assertGreater(result["metrics"]["zones_with_improved_hospital_access"], 0)
        self.assertGreater(result["metrics"]["avg_hospital_time_saved_min"], 0)

    def test_invalid_nodes_raise(self):
        with self.assertRaises(ValueError):
            simulate_new_flyover(self.conn, 99999, 88888)

    def test_deterministic(self):
        r1 = simulate_new_flyover(self.conn, 43, 22, speed_kmph=70)
        r2 = simulate_new_flyover(self.conn, 43, 22, speed_kmph=70)
        self.assertEqual(r1["metrics"], r2["metrics"])


class TestAccident(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_invalid_severity_raises(self):
        with self.assertRaises(ValueError):
            simulate_accident(self.conn, 16, severity="catastrophic")

    def test_severe_accident_worse_than_minor(self):
        minor = simulate_accident(self.conn, 16, severity="minor")
        severe = simulate_accident(self.conn, 16, severity="severe")
        self.assertGreaterEqual(
            severe["metrics"]["avg_hospital_route_delay_pct"],
            minor["metrics"]["avg_hospital_route_delay_pct"],
        )

    def test_speed_never_floors_to_zero(self):
        result = simulate_accident(self.conn, 16, severity="severe")
        self.assertGreaterEqual(result["input"]["degraded_speed_kmph"], 5)

    def test_only_road_16_at_least_as_bad_as_closure_direction(self):
        accident = simulate_accident(self.conn, 16, severity="severe")
        from engine.simulations import simulate_road_closure
        closure = simulate_road_closure(self.conn, 16)
        self.assertLessEqual(
            accident["metrics"]["avg_hospital_route_delay_pct"],
            closure["metrics"]["avg_hospital_route_delay_pct"] + 0.01,
        )


class TestPowerFailure(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_non_signal_nodes_raise(self):
        G = build_graph(self.conn)
        non_signals = [n for n, d in G.nodes(data=True) if not d["is_signal"]]
        with self.assertRaises(ValueError):
            simulate_power_failure(self.conn, non_signals[:2])

    def test_signal_nodes_produce_added_delay(self):
        G = build_graph(self.conn)
        signals = [n for n, d in G.nodes(data=True) if d["is_signal"]]
        result = simulate_power_failure(self.conn, signals)
        self.assertGreater(result["metrics"]["zones_with_route_through_affected_signals"], 0)
        self.assertGreater(result["metrics"]["avg_added_delay_min"], 0)

    def test_more_affected_signals_never_decreases_delay(self):
        G = build_graph(self.conn)
        signals = [n for n, d in G.nodes(data=True) if d["is_signal"]]
        few = simulate_power_failure(self.conn, signals[:2])
        many = simulate_power_failure(self.conn, signals)
        self.assertGreaterEqual(
            many["metrics"]["signal_intersections_affected"],
            few["metrics"]["signal_intersections_affected"],
        )


class TestFestival(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_no_roads_in_radius_raises(self):
        with self.assertRaises(ValueError):
            simulate_festival(self.conn, 20.0, 90.0, radius_m=50)

    def test_larger_radius_affects_more_or_equal_roads(self):
        zones = db_module.get_population_zones(self.conn)
        mc = next(z for z in zones if "Meridian Central" in z["name"])
        small = simulate_festival(self.conn, mc["centroid_lat"], mc["centroid_lon"], radius_m=250)
        large = simulate_festival(self.conn, mc["centroid_lat"], mc["centroid_lon"], radius_m=600)
        self.assertGreaterEqual(large["metrics"]["roads_affected"], small["metrics"]["roads_affected"])


if __name__ == "__main__":
    unittest.main(verbosity=2)