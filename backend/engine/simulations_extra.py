"""
CityMind Phase 4 — Extended Simulation Types.

Same architecture rule as engine/simulations.py: every number is
computed from the graph, never invented.

Known limitation (documented, not hidden): none of these model
volume-vs-capacity queuing — a detour road doesn't "fill up" and
gridlock under redirected load. What IS modeled is deterministic
travel-time impact from speed/capacity degradation or new links.
"""

import networkx as nx

from . import db as db_module
from . import graph_builder
from .simulations import _od_pairs_zone_to_facility, _path_uses_edge, simulate_road_closure


# ---------------------------------------------------------------------
# Bridge Closure — mechanically identical to road closure (a bridge is
# just a road segment in the graph), labeled distinctly because bridge
# closures typically have no nearby parallel route.
# ---------------------------------------------------------------------

def simulate_bridge_closure(conn, road_id: int) -> dict:
    result = simulate_road_closure(conn, road_id)
    result["scenario_type"] = "bridge_closure"
    if result["recommendation"]["type"] == "no_detour_available":
        result["metrics"]["single_point_of_failure"] = True
    else:
        result["metrics"]["single_point_of_failure"] = False
    return result


# ---------------------------------------------------------------------
# New Flyover / New Metro — models a new high-capacity direct link
# between two existing intersections.
# ---------------------------------------------------------------------

def simulate_new_flyover(conn, node_a: int, node_b: int, speed_kmph: int = 70,
                           capacity_vph: int = 3000, name: str = "Proposed Flyover") -> dict:
    G_before = graph_builder.build_graph(conn)
    if node_a not in G_before or node_b not in G_before:
        raise ValueError("Both endpoint nodes must exist in the road network.")

    from .geo import haversine_m
    lat_a, lon_a = G_before.nodes[node_a]["lat"], G_before.nodes[node_a]["lon"]
    lat_b, lon_b = G_before.nodes[node_b]["lat"], G_before.nodes[node_b]["lon"]
    length_m = haversine_m(lat_a, lon_a, lat_b, lon_b)
    travel_time_min = (length_m / 1000.0) / speed_kmph * 60.0

    G_after = G_before.copy()
    existing_time = None
    if G_before.has_edge(node_a, node_b):
        existing_time = G_before[node_a][node_b]["travel_time_min"]
    if existing_time is None or travel_time_min < existing_time:
        G_after.add_edge(node_a, node_b, name=name, road_class="arterial",
                          length_m=length_m, speed_kmph=speed_kmph,
                          capacity_vph=capacity_vph, travel_time_min=travel_time_min)

    hospital_pairs = _od_pairs_zone_to_facility(conn, G_before, "hospital")
    school_pairs = _od_pairs_zone_to_facility(conn, G_before, "school")

    def evaluate(pairs):
        results = []
        for p in pairs:
            src, tgt = p["source_node"], p["target_node"]
            try:
                time_before = nx.shortest_path_length(G_before, src, tgt, weight="travel_time_min")
                time_after = nx.shortest_path_length(G_after, src, tgt, weight="travel_time_min")
            except nx.NetworkXNoPath:
                continue
            results.append({
                "zone": p["zone"]["name"], "population": p["zone"]["population"],
                "facility": p["facility"]["name"],
                "time_before_min": round(time_before, 2),
                "time_after_min": round(time_after, 2),
                "delta_min": round(time_after - time_before, 2),
                "delta_pct": round((time_after - time_before) / time_before * 100, 1) if time_before > 0 else 0.0,
            })
        return results

    hospital_results = evaluate(hospital_pairs)
    school_results = evaluate(school_pairs)

    def aggregate_improvement(results):
        improved = [r for r in results if r["delta_min"] < 0]
        if not improved:
            return 0.0, 0
        avg_saved = sum(-r["delta_min"] for r in improved) / len(improved)
        return round(avg_saved, 1), len(improved)

    avg_hospital_time_saved, hospital_zones_improved = aggregate_improvement(hospital_results)
    avg_school_time_saved, school_zones_improved = aggregate_improvement(school_results)

    return {
        "scenario_type": "new_flyover",
        "input": {"node_a": node_a, "node_b": node_b, "speed_kmph": speed_kmph,
                   "capacity_vph": capacity_vph, "name": name},
        "basis": {
            "method": "Added a direct edge between the two nodes at the given speed, "
                      "recomputed Dijkstra shortest paths for all zone->facility OD pairs, "
                      "kept the new edge only if it improves on any existing direct route.",
            "new_link_travel_time_min": round(travel_time_min, 2),
        },
        "metrics": {
            "avg_hospital_time_saved_min": avg_hospital_time_saved,
            "avg_school_time_saved_min": avg_school_time_saved,
            "zones_with_improved_hospital_access": hospital_zones_improved,
            "zones_with_improved_school_access": school_zones_improved,
        },
        "hospital_route_detail": hospital_results,
        "school_route_detail": school_results,
    }


# ---------------------------------------------------------------------
# Accident — models a temporary, partial capacity/speed reduction on a
# road (not a full closure). Severity maps to a speed multiplier.
# ---------------------------------------------------------------------

SEVERITY_SPEED_FACTOR = {"minor": 0.75, "moderate": 0.45, "severe": 0.15}


def simulate_accident(conn, road_id: int, severity: str = "moderate") -> dict:
    if severity not in SEVERITY_SPEED_FACTOR:
        raise ValueError(f"severity must be one of {list(SEVERITY_SPEED_FACTOR)}")

    road = db_module.get_road_by_id(conn, road_id)
    if road is None:
        raise ValueError(f"No road with id {road_id}")

    factor = SEVERITY_SPEED_FACTOR[severity]
    degraded_speed = max(road["speed_kmph"] * factor, 5)  # floor at 5 km/h, not zero

    G_before = graph_builder.build_graph(conn)
    G_after = G_before.copy()
    u, v = road["node_a"], road["node_b"]
    degraded_time = (road["length_m"] / 1000.0) / degraded_speed * 60.0
    G_after[u][v]["travel_time_min"] = degraded_time
    G_after[u][v]["speed_kmph"] = degraded_speed

    hospital_pairs = _od_pairs_zone_to_facility(conn, G_before, "hospital")

    results = []
    for p in hospital_pairs:
        src, tgt = p["source_node"], p["target_node"]
        try:
            path_before = nx.shortest_path(G_before, src, tgt, weight="travel_time_min")
            time_before = nx.path_weight(G_before, path_before, weight="travel_time_min")
        except nx.NetworkXNoPath:
            continue
        if not _path_uses_edge(G_before, path_before, u, v):
            continue
        time_after = nx.shortest_path_length(G_after, src, tgt, weight="travel_time_min")
        results.append({
            "zone": p["zone"]["name"], "population": p["zone"]["population"],
            "facility": p["facility"]["name"],
            "time_before_min": round(time_before, 2), "time_after_min": round(time_after, 2),
            "delta_min": round(time_after - time_before, 2),
            "delta_pct": round((time_after - time_before) / time_before * 100, 1) if time_before > 0 else 0.0,
        })

    avg_delay_pct = round(sum(r["delta_pct"] for r in results) / len(results), 1) if results else 0.0
    max_delay_min = round(max((r["delta_min"] for r in results), default=0.0), 1)

    return {
        "scenario_type": "accident",
        "input": {"road_id": road_id, "road_name": road["name"], "severity": severity,
                   "degraded_speed_kmph": round(degraded_speed, 1)},
        "basis": {
            "method": f"Reduced {road['name']}'s effective speed to {round(degraded_speed,1)} km/h "
                      f"({int(factor*100)}% of normal) rather than removing it; recomputed shortest "
                      f"paths for zone->hospital OD pairs whose route uses this road.",
        },
        "metrics": {
            "zones_directly_affected": len(results),
            "avg_hospital_route_delay_pct": avg_delay_pct,
            "max_hospital_route_delay_min": max_delay_min,
        },
        "hospital_route_detail": results,
    }


# ---------------------------------------------------------------------
# Power Failure — signals go dark; every intersection normally
# controlled by a signal adds a fixed manual-control delay.
# ---------------------------------------------------------------------

SIGNAL_OUTAGE_DELAY_MIN = 1.5


def simulate_power_failure(conn, affected_node_ids: list) -> dict:
    G_before = graph_builder.build_graph(conn)
    nodes = db_module.get_all_nodes(conn)
    affected = [n for n in affected_node_ids if nodes.get(n, {}).get("is_signal")]
    if not affected:
        raise ValueError("None of the given node ids are signal-controlled intersections.")

    G_after = G_before.copy()
    for n in affected:
        for neighbor in list(G_after.neighbors(n)):
            G_after[n][neighbor]["travel_time_min"] += SIGNAL_OUTAGE_DELAY_MIN / 2

    hospital_pairs = _od_pairs_zone_to_facility(conn, G_before, "hospital")
    results = []
    for p in hospital_pairs:
        src, tgt = p["source_node"], p["target_node"]
        try:
            path_before = nx.shortest_path(G_before, src, tgt, weight="travel_time_min")
            time_before = nx.path_weight(G_before, path_before, weight="travel_time_min")
        except nx.NetworkXNoPath:
            continue
        crosses_affected = any(node in affected for node in path_before)
        if not crosses_affected:
            continue
        time_after = nx.shortest_path_length(G_after, src, tgt, weight="travel_time_min")
        results.append({
            "zone": p["zone"]["name"], "population": p["zone"]["population"],
            "time_before_min": round(time_before, 2), "time_after_min": round(time_after, 2),
            "delta_min": round(time_after - time_before, 2),
        })

    return {
        "scenario_type": "power_failure",
        "input": {"affected_signal_nodes": affected},
        "basis": {
            "method": f"Added a {SIGNAL_OUTAGE_DELAY_MIN}-minute manual-control delay to each "
                      f"traversal of the affected intersection(s); recomputed routes for "
                      f"zone->hospital pairs that cross them.",
        },
        "metrics": {
            "signal_intersections_affected": len(affected),
            "zones_with_route_through_affected_signals": len(results),
            "avg_added_delay_min": round(sum(r["delta_min"] for r in results) / len(results), 2) if results else 0.0,
        },
        "hospital_route_detail": results,
    }


# ---------------------------------------------------------------------
# Festival — temporary capacity/speed reduction across all roads within
# a radius of the event location.
# ---------------------------------------------------------------------

def simulate_festival(conn, lat: float, lon: float, radius_m: float = 300, speed_factor: float = 0.4) -> dict:
    from .geo import haversine_m

    G_before = graph_builder.build_graph(conn)
    G_after = G_before.copy()

    affected_edges = []
    for u, v, data in G_before.edges(data=True):
        u_lat, u_lon = G_before.nodes[u]["lat"], G_before.nodes[u]["lon"]
        v_lat, v_lon = G_before.nodes[v]["lat"], G_before.nodes[v]["lon"]
        mid_lat, mid_lon = (u_lat + v_lat) / 2, (u_lon + v_lon) / 2
        if haversine_m(lat, lon, mid_lat, mid_lon) <= radius_m:
            new_speed = max(data["speed_kmph"] * speed_factor, 5)
            new_time = (data["length_m"] / 1000.0) / new_speed * 60.0
            G_after[u][v]["travel_time_min"] = new_time
            affected_edges.append({"road_id": data["road_id"], "name": data["name"]})

    if not affected_edges:
        raise ValueError(f"No roads found within {radius_m}m of the given location.")

    hospital_pairs = _od_pairs_zone_to_facility(conn, G_before, "hospital")
    results = []
    for p in hospital_pairs:
        src, tgt = p["source_node"], p["target_node"]
        try:
            time_before = nx.shortest_path_length(G_before, src, tgt, weight="travel_time_min")
            time_after = nx.shortest_path_length(G_after, src, tgt, weight="travel_time_min")
        except nx.NetworkXNoPath:
            continue
        if time_after > time_before:
            results.append({
                "zone": p["zone"]["name"], "population": p["zone"]["population"],
                "time_before_min": round(time_before, 2), "time_after_min": round(time_after, 2),
                "delta_pct": round((time_after - time_before) / time_before * 100, 1) if time_before > 0 else 0.0,
            })

    avg_delay_pct = round(sum(r["delta_pct"] for r in results) / len(results), 1) if results else 0.0

    return {
        "scenario_type": "festival",
        "input": {"lat": lat, "lon": lon, "radius_m": radius_m, "speed_factor": speed_factor},
        "basis": {
            "method": f"Reduced speed to {int(speed_factor*100)}% of normal on all "
                      f"{len(affected_edges)} road segment(s) within {radius_m}m of the event "
                      f"location; recomputed zone->hospital shortest paths.",
            "affected_roads": affected_edges,
        },
        "metrics": {
            "roads_affected": len(affected_edges),
            "zones_with_increased_hospital_travel": len(results),
            "avg_hospital_route_delay_pct": avg_delay_pct,
        },
        "hospital_route_detail": results,
    }