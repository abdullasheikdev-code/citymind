"""Builds a NetworkX graph. Edge weight = travel_time_min = length_km/speed*60."""

import networkx as nx
from . import db as db_module


def build_graph(conn, exclude_road_ids=None) -> nx.Graph:
    exclude_road_ids = set(exclude_road_ids or [])
    nodes = db_module.get_all_nodes(conn)
    roads = db_module.get_all_roads(conn, include_closed=True)

    G = nx.Graph()
    for node_id, attrs in nodes.items():
        G.add_node(node_id, lat=attrs["lat"], lon=attrs["lon"], is_signal=attrs["is_signal"])

    for road in roads:
        if road["id"] in exclude_road_ids or road["is_closed"]:
            continue
        travel_time_min = (road["length_m"] / 1000.0) / road["speed_kmph"] * 60.0
        if G.has_edge(road["node_a"], road["node_b"]):
            if G[road["node_a"]][road["node_b"]]["travel_time_min"] <= travel_time_min:
                continue
        G.add_edge(
            road["node_a"], road["node_b"],
            road_id=road["id"], name=road["name"], road_class=road["road_class"],
            length_m=road["length_m"], speed_kmph=road["speed_kmph"],
            capacity_vph=road["capacity_vph"], travel_time_min=travel_time_min,
        )
    return G


def node_coords(G: nx.Graph) -> dict:
    return {n: (data["lat"], data["lon"]) for n, data in G.nodes(data=True)}