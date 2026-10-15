import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import db as db_module
from engine import graph_builder
from engine.simulations import simulate_road_closure, simulate_new_facility
from engine.geo import haversine_m


class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_graph_has_all_nodes_and_roads(self):
        G = graph_builder.build_graph(self.conn)
        self.assertEqual(G.number_of_nodes(), len(db_module.get_all_nodes(self.conn)))
        self.assertEqual(G.number_of_edges(), len(db_module.get_all_roads(self.conn)))

    def test_excluding_a_road_removes_exactly_one_edge(self):
        G_full = graph_builder.build_graph(self.conn)
        G_minus = graph_builder.build_graph(self.conn, exclude_road_ids=[1])
        self.assertEqual(G_full.number_of_edges() - 1, G_minus.number_of_edges())

    def test_travel_time_matches_length_and_speed(self):
        G = graph_builder.build_graph(self.conn)
        for u, v, data in G.edges(data=True):
            expected = (data["length_m"] / 1000.0) / data["speed_kmph"] * 60.0
            self.assertAlmostEqual(data["travel_time_min"], expected, places=6)


class TestRoadClosure(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_closing_nonexistent_road_raises(self):
        with self.assertRaises(ValueError):
            simulate_road_closure(self.conn, 999999)

    def test_closing_bottleneck_road_increases_delay(self):
        result = simulate_road_closure(self.conn, 16)
        self.assertGreater(result["metrics"]["avg_hospital_route_delay_pct"], 0)

    def test_closing_redundant_road_has_zero_impact(self):
        result = simulate_road_closure(self.conn, 1)
        self.assertEqual(result["metrics"]["avg_hospital_route_delay_pct"], 0.0)

    def test_deterministic_reproducible(self):
        r1 = simulate_road_closure(self.conn, 16)
        r2 = simulate_road_closure(self.conn, 16)
        self.assertEqual(r1["metrics"], r2["metrics"])

    def test_every_metric_traces_to_explicit_route_detail(self):
        result = simulate_road_closure(self.conn, 16)
        affected = [r for r in result["hospital_route_detail"] if r["delta_pct"] and r["delta_pct"] > 0]
        recomputed_avg = round(sum(r["delta_pct"] for r in affected) / len(affected), 1)
        self.assertEqual(recomputed_avg, result["metrics"]["avg_hospital_route_delay_pct"])


class TestNewFacility(unittest.TestCase):
    def setUp(self):
        self.conn = db_module.connect()

    def test_new_hospital_near_underserved_zone_improves_coverage(self):
        zones = db_module.get_population_zones(self.conn)
        millbrook = next(z for z in zones if "Millbrook" in z["name"])
        result = simulate_new_facility(self.conn, "hospital", millbrook["centroid_lat"], millbrook["centroid_lon"])
        self.assertGreater(result["metrics"]["population_newly_best_served"], 0)


class TestGeo(unittest.TestCase):
    def test_haversine_known_distance(self):
        d = haversine_m(13.05, 80.21, 13.06, 80.21)
        self.assertAlmostEqual(d, 1113.0, delta=15)


if __name__ == "__main__":
    unittest.main(verbosity=2)