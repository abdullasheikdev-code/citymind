"""
CityMind Phase 1 — Simulation Engine.
Every number returned is computed via NetworkX Dijkstra shortest-path,
never estimated by an LLM.
"""

import networkx as nx
from . import db as db_module
from . import graph_builder
from .geo import nearest_node as geo_nearest_node


def _od_pairs_zone_to_facility(conn, G, facility_type):
    zones = db_module.get_population_zones(conn)
    facilities = db_module.get_facilities(conn, facility_type)

    if not facilities:
        return []

    pairs = []

    for zone in zones:
        source = zone["nearest_node_id"]

        if source not in G:
            continue

        best_facility, best_time = None, float("inf")

        for fac in facilities:
            target = fac["nearest_node_id"]

            if target not in G:
                continue

            try:
                travel_time = nx.shortest_path_length(
                    G,
                    source,
                    target,
                    weight="travel_time_min",
                )
            except nx.NetworkXNoPath:
                continue

            if travel_time < best_time:
                best_facility, best_time = fac, travel_time

        if best_facility is not None:
            pairs.append({
                "zone": zone,
                "facility": best_facility,
                "source_node": source,
                "target_node": best_facility["nearest_node_id"],
                "baseline_time_min": best_time,
            })

    return pairs


def _path_uses_edge(G, path_nodes, node_a, node_b):
    edges_in_path = set()

    for i in range(len(path_nodes) - 1):
        edges_in_path.add(
            frozenset((path_nodes[i], path_nodes[i + 1]))
        )

    return frozenset((node_a, node_b)) in edges_in_path


def simulate_road_closure(conn, road_id: int) -> dict:
    road = db_module.get_road_by_id(conn, road_id)

    if road is None:
        raise ValueError(f"No road with id {road_id}")

    G_before = graph_builder.build_graph(conn)
    G_after = graph_builder.build_graph(
        conn,
        exclude_road_ids=[road_id],
    )

    node_a, node_b = road["node_a"], road["node_b"]

    hospital_pairs = _od_pairs_zone_to_facility(
        conn, G_before, "hospital"
    )
    school_pairs = _od_pairs_zone_to_facility(
        conn, G_before, "school"
    )

    def evaluate(pairs, G_after):
        results = []

        for pair in pairs:
            src = pair["source_node"]
            tgt = pair["target_node"]

            try:
                path_before = nx.shortest_path(
                    G_before,
                    src,
                    tgt,
                    weight="travel_time_min",
                )
                time_before = nx.path_weight(
                    G_before,
                    path_before,
                    weight="travel_time_min",
                )
            except nx.NetworkXNoPath:
                continue

            used_closed_edge = _path_uses_edge(
                G_before,
                path_before,
                node_a,
                node_b,
            )

            try:
                time_after = nx.shortest_path_length(
                    G_after,
                    src,
                    tgt,
                    weight="travel_time_min",
                )
                reachable = True
            except nx.NetworkXNoPath:
                time_after = None
                reachable = False

            delta_min = (
                round(time_after - time_before, 2)
                if reachable
                else None
            )

            delta_pct = (
                round(
                    (time_after - time_before) / time_before * 100,
                    1,
                )
                if reachable and time_before > 0
                else None
            )

            results.append({
                "zone": pair["zone"]["name"],
                "population": pair["zone"]["population"],
                "facility": pair["facility"]["name"],
                "time_before_min": round(time_before, 2),
                "time_after_min": (
                    round(time_after, 2) if reachable else None
                ),
                "delta_min": delta_min,
                "delta_pct": delta_pct,
                "used_closed_road": used_closed_edge,
                "reachable_after_closure": reachable,
            })

        return results

    hospital_results = evaluate(hospital_pairs, G_after)
    school_results = evaluate(school_pairs, G_after)

    # Calculate affected-zone averages and all-valid-zone averages.
    def aggregate_delay(results):
        affected = [
            result
            for result in results
            if result["delta_pct"] is not None
            and result["delta_pct"] > 0
        ]

        valid = [
            result
            for result in results
            if result["delta_pct"] is not None
        ]

        affected_avg = (
            round(
                sum(result["delta_pct"] for result in affected)
                / len(affected),
                1,
            )
            if affected
            else 0.0
        )

        all_zones_avg = (
            round(
                sum(result["delta_pct"] for result in valid)
                / len(valid),
                1,
            )
            if valid
            else 0.0
        )

        return affected_avg, all_zones_avg, len(affected)

    (
        avg_hospital_delay_pct,
        all_hospital_delay_pct,
        hospitals_affected_zones,
    ) = aggregate_delay(hospital_results)

    (
        avg_school_delay_pct,
        all_school_delay_pct,
        schools_affected_zones,
    ) = aggregate_delay(school_results)

    ambulance_deltas = [
        result["delta_min"]
        for result in hospital_results
        if result["delta_min"] is not None
        and result["delta_min"] > 0
    ]

    max_ambulance_delay_min = (
        round(max(ambulance_deltas), 1)
        if ambulance_deltas
        else 0.0
    )

    unreachable = [
        result
        for result in hospital_results + school_results
        if not result["reachable_after_closure"]
    ]

    FUEL_L_PER_KM = 0.09
    total_extra_km = 0.0

    for result in hospital_results + school_results:
        if (
            result["delta_min"] is not None
            and result["delta_min"] > 0
        ):
            total_extra_km += (
                result["delta_min"] / 60.0
            ) * 35

    extra_fuel_liters = round(
        total_extra_km * FUEL_L_PER_KM,
        1,
    )

    baseline_km_estimate = sum(
        (result["time_before_min"] / 60.0) * 35
        for result in hospital_results + school_results
    ) or 1.0

    fuel_pct_increase = round(
        (
            total_extra_km * FUEL_L_PER_KM
        ) / (
            baseline_km_estimate * FUEL_L_PER_KM
        ) * 100,
        1,
    ) if baseline_km_estimate else 0.0

    recommendation = _recommend_alternative(
        G_before,
        G_after,
        node_a,
        node_b,
        road,
    )

    return {
        "scenario_type": "road_closure",

        "input": {
            "road_id": road_id,
            "road_name": road["name"],
            "road_class": road["road_class"],
        },

        "basis": {
            "closed_edge": {
                "node_a": node_a,
                "node_b": node_b,
                "name": road["name"],
            },
            "method": (
                "Dijkstra shortest path (networkx), "
                "weight=travel_time_min, recomputed on graph "
                "with the closed road's edge removed."
            ),
        },

        "metrics": {
            # Average among zones with increased travel time.
            "avg_hospital_route_delay_pct": (
                avg_hospital_delay_pct
            ),

            # Average across all zones with a calculable percentage.
            "avg_hospital_route_delay_pct_all_zones": (
                all_hospital_delay_pct
            ),

            "avg_school_route_delay_pct": (
                avg_school_delay_pct
            ),

            "avg_school_route_delay_pct_all_zones": (
                all_school_delay_pct
            ),

            "zones_with_increased_hospital_travel": (
                hospitals_affected_zones
            ),

            "zones_with_increased_school_travel": (
                schools_affected_zones
            ),

            "max_ambulance_delay_min": (
                max_ambulance_delay_min
            ),

            "estimated_extra_fuel_liters_per_day": (
                extra_fuel_liters
            ),

            "estimated_fuel_increase_pct": (
                fuel_pct_increase
            ),

            "zones_cut_off_entirely": len(unreachable),
        },

        "hospital_route_detail": hospital_results,
        "school_route_detail": school_results,
        "recommendation": recommendation,
    }


def _recommend_alternative(
    G_before,
    G_after,
    node_a,
    node_b,
    road,
):
    try:
        detour_path = nx.shortest_path(
            G_after,
            node_a,
            node_b,
            weight="travel_time_min",
        )

        detour_time = nx.path_weight(
            G_after,
            detour_path,
            weight="travel_time_min",
        )

        original_time = G_before[node_a][node_b][
            "travel_time_min"
        ]

        road_names = []

        for i in range(len(detour_path) - 1):
            edge = G_after[detour_path[i]][detour_path[i + 1]]

            if not road_names or road_names[-1] != edge["name"]:
                road_names.append(edge["name"])

        return {
            "type": "existing_detour",
            "text": (
                f"Route traffic via {', '.join(road_names)}. "
                f"This detour adds about "
                f"{round(detour_time - original_time, 1)} minutes "
                f"versus the closed segment of {road['name']}."
            ),
            "detour_roads": road_names,
            "detour_extra_time_min": round(
                detour_time - original_time,
                1,
            ),
        }

    except nx.NetworkXNoPath:
        return {
            "type": "no_detour_available",
            "text": (
                f"No alternate route currently connects these two "
                f"intersections once {road['name']} is closed. "
                f"Recommend opening a temporary direct link between "
                f"the two endpoints before proceeding with this closure."
            ),
            "detour_roads": [],
            "detour_extra_time_min": None,
        }


def simulate_new_facility(
    conn,
    facility_type: str,
    lat: float,
    lon: float,
    name: str = None,
) -> dict:
    G = graph_builder.build_graph(conn)
    coords = graph_builder.node_coords(G)

    new_node = geo_nearest_node(lat, lon, coords)

    if new_node is None:
        raise ValueError(
            "Could not snap the given coordinates to the road network."
        )

    existing_facilities = db_module.get_facilities(
        conn,
        facility_type,
    )
    zones = db_module.get_population_zones(conn)

    zone_results = []
    newly_best_population = 0

    for zone in zones:
        source = zone["nearest_node_id"]

        if source not in G:
            continue

        best_existing_name = None
        best_existing_time = float("inf")

        for facility in existing_facilities:
            target = facility["nearest_node_id"]

            if target not in G:
                continue

            try:
                travel_time = nx.shortest_path_length(
                    G,
                    source,
                    target,
                    weight="travel_time_min",
                )
            except nx.NetworkXNoPath:
                continue

            if travel_time < best_existing_time:
                best_existing_name = facility["name"]
                best_existing_time = travel_time

        try:
            time_to_new = nx.shortest_path_length(
                G,
                source,
                new_node,
                weight="travel_time_min",
            )
        except nx.NetworkXNoPath:
            time_to_new = None

        becomes_closer = (
            time_to_new is not None
            and (
                best_existing_time == float("inf")
                or time_to_new < best_existing_time
            )
        )

        if becomes_closer:
            newly_best_population += zone["population"]

        zone_results.append({
            "zone": zone["name"],
            "population": zone["population"],

            "time_to_new_facility_min": (
                round(time_to_new, 2)
                if time_to_new is not None
                else None
            ),

            "time_to_nearest_existing_min": (
                round(best_existing_time, 2)
                if best_existing_time != float("inf")
                else None
            ),

            "nearest_existing_facility": best_existing_name,
            "new_facility_becomes_closest": becomes_closer,

            "time_saved_min": (
                round(best_existing_time - time_to_new, 2)
                if (
                    becomes_closer
                    and best_existing_time != float("inf")
                )
                else None
            ),
        })

    total_population = sum(
        zone["population"] for zone in zones
    )

    coverage_pct = (
        round(
            newly_best_population / total_population * 100,
            1,
        )
        if total_population
        else 0.0
    )

    served_better = [
        zone
        for zone in zone_results
        if zone["new_facility_becomes_closest"]
    ]

    avg_time_saved = (
        round(
            sum(
                zone["time_saved_min"]
                for zone in served_better
            ) / len(served_better),
            1,
        )
        if served_better
        else 0.0
    )

    return {
        "scenario_type": "new_facility",

        "input": {
            "facility_type": facility_type,
            "name": name or (
                f"New {facility_type.replace('_', ' ').title()}"
            ),
            "lat": lat,
            "lon": lon,
            "snapped_node": new_node,
        },

        "basis": {
            "method": (
                "Dijkstra shortest path (networkx), "
                "weight=travel_time_min, comparing every zone's "
                "travel time to the proposed facility vs. its "
                "current nearest facility of the same type."
            ),
        },

        "metrics": {
            "population_newly_best_served": newly_best_population,
            "population_coverage_pct_of_city": coverage_pct,
            "zones_better_served": len(served_better),
            "avg_time_saved_min_for_those_zones": avg_time_saved,
        },

        "zone_detail": zone_results,
    }