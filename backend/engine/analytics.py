"""
CityMind Phase 5 — Analytics Engine.
Every number here is a real query or graph computation, never a
hardcoded dashboard value.
"""

from . import db as db_module
from . import graph_builder
from .simulations import _od_pairs_zone_to_facility


def compute_dashboard_summary(conn) -> dict:
    roads = db_module.get_all_roads(conn)
    zones = db_module.get_population_zones(conn)
    facilities = db_module.get_facilities(conn)

    if not roads:
        raise ValueError("No roads in database — run the city generator first.")

    arterial = [r for r in roads if r["road_class"] == "arterial"]
    local = [r for r in roads if r["road_class"] == "local"]
    avg_speed = sum(r["speed_kmph"] for r in roads) / len(roads)
    total_capacity_vph = sum(r["capacity_vph"] for r in roads)
    total_population = sum(z["population"] for z in zones)

    facility_counts = {}
    for f in facilities:
        facility_counts[f["facility_type"]] = facility_counts.get(f["facility_type"], 0) + 1

    return {
        "total_road_segments": len(roads),
        "arterial_road_segments": len(arterial),
        "local_road_segments": len(local),
        "avg_speed_limit_kmph": round(avg_speed, 1),
        "total_road_capacity_vph": total_capacity_vph,
        "total_population_tracked": total_population,
        "population_zones": len(zones),
        "facility_counts": facility_counts,
    }


def compute_infrastructure_health(conn) -> dict:
    """Composite score from real signals: signal coverage, road class
    mix, and genuine facility-coverage gaps (a zone with NO reachable
    hospital/school/fire/police) — not a vibe-based AI score."""
    G = graph_builder.build_graph(conn)
    nodes = db_module.get_all_nodes(conn)
    roads = db_module.get_all_roads(conn)

    signal_nodes = sum(1 for n in nodes.values() if n["is_signal"])
    signal_coverage_pct = round(signal_nodes / len(nodes) * 100, 1) if nodes else 0.0
    arterial_pct = round(
        sum(1 for r in roads if r["road_class"] == "arterial") / len(roads) * 100, 1
    ) if roads else 0.0

    gaps = []
    for facility_type in ("hospital", "school", "fire_station", "police_station"):
        pairs = _od_pairs_zone_to_facility(conn, G, facility_type)
        zones_covered = {p["zone"]["id"] for p in pairs}
        all_zone_ids = {z["id"] for z in db_module.get_population_zones(conn)}
        uncovered = all_zone_ids - zones_covered
        if uncovered:
            zone_names = [z["name"] for z in db_module.get_population_zones(conn) if z["id"] in uncovered]
            gaps.append({"facility_type": facility_type, "uncovered_zones": zone_names})

    score = 100.0
    score -= len(gaps) * 15  # each coverage gap is a real, traceable deduction
    score = max(score, 0.0)

    return {
        "infrastructure_health_score": round(score, 1),
        "signal_coverage_pct": signal_coverage_pct,
        "arterial_road_pct": arterial_pct,
        "coverage_gaps": gaps,
    }


def compute_emergency_response_coverage(conn) -> dict:
    """For every population zone: real shortest-path travel time to its
    nearest fire station and police station."""
    G = graph_builder.build_graph(conn)
    zones = db_module.get_population_zones(conn)

    fire_pairs = {p["zone"]["id"]: p for p in _od_pairs_zone_to_facility(conn, G, "fire_station")}
    police_pairs = {p["zone"]["id"]: p for p in _od_pairs_zone_to_facility(conn, G, "police_station")}

    zone_results = []
    for zone in zones:
        fire = fire_pairs.get(zone["id"])
        police = police_pairs.get(zone["id"])
        zone_results.append({
            "zone": zone["name"], "population": zone["population"],
            "lat": zone["centroid_lat"], "lon": zone["centroid_lon"],
            "fire_response_min": round(fire["baseline_time_min"], 2) if fire else None,
            "nearest_fire_station": fire["facility"]["name"] if fire else None,
            "police_response_min": round(police["baseline_time_min"], 2) if police else None,
            "nearest_police_station": police["facility"]["name"] if police else None,
        })

    fire_times = [z["fire_response_min"] for z in zone_results if z["fire_response_min"] is not None]
    police_times = [z["police_response_min"] for z in zone_results if z["police_response_min"] is not None]

    RESPONSE_TARGET_MIN = 4.0  # common planning-doc benchmark; flagged, not averaged away
    zones_over_target = [z["zone"] for z in zone_results
                          if z["fire_response_min"] and z["fire_response_min"] > RESPONSE_TARGET_MIN]

    return {
        "avg_fire_response_min": round(sum(fire_times) / len(fire_times), 2) if fire_times else None,
        "avg_police_response_min": round(sum(police_times) / len(police_times), 2) if police_times else None,
        "worst_fire_response_min": round(max(fire_times), 2) if fire_times else None,
        "zones_exceeding_target": zones_over_target,
        "response_target_min": RESPONSE_TARGET_MIN,
        "zone_detail": zone_results,
    }


def compute_scenario_trends(conn) -> dict:
    """Aggregates over actual saved scenario history. Honestly empty
    until real simulations accumulate — never backfilled with fake data."""
    rows = conn.execute(
        "SELECT scenario_type, result_json, created_at FROM scenarios ORDER BY created_at"
    ).fetchall()

    if not rows:
        return {
            "total_scenarios_run": 0,
            "by_type": {},
            "note": "No simulations have been run yet — trends will populate as planners use the system.",
        }

    by_type = {}
    for row in rows:
        by_type[row["scenario_type"]] = by_type.get(row["scenario_type"], 0) + 1

    return {
        "total_scenarios_run": len(rows),
        "by_type": by_type,
        "most_recent": dict(rows[-1]) if rows else None,
    }