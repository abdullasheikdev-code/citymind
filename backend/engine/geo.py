"""Pure-stdlib geospatial helpers. No shapely/geopandas dependency."""

import math

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in meters."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_M * c


def nearest_node(target_lat: float, target_lon: float, nodes: dict) -> int:
    """nodes: {node_id: (lat, lon)}. Linear scan — fine at this graph size."""
    best_id, best_dist = None, float("inf")
    for node_id, (lat, lon) in nodes.items():
        d = haversine_m(target_lat, target_lon, lat, lon)
        if d < best_dist:
            best_id, best_dist = node_id, d
    return best_id