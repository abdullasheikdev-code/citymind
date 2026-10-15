"""
Import real OpenStreetMap roads into a separate SQLite test database.

The existing city.db is read-only during this process.
The output database is city_osm_test.db.
"""

import json
import math
import sqlite3
from pathlib import Path

import osmnx as ox

DATA_DIR = Path(__file__).parent
SOURCE_DB = DATA_DIR / "city.db"
OUTPUT_DB = DATA_DIR / "city_osm_test.db"
SCHEMA_FILE = DATA_DIR.parent / "schema" / "sqlite_schema.sql"

# Existing CityMind map center, Chennai.
CENTER_LAT = 13.053
CENTER_LON = 80.213
DISTANCE_METERS = 2500


def road_class(highway):
    """Convert OSM road classifications to the existing SQLite values."""
    if isinstance(highway, list):
        highway = highway[0] if highway else "residential"

    if highway in {
        "motorway", "motorway_link", "trunk", "trunk_link",
        "primary", "primary_link", "secondary", "secondary_link",
    }:
        return "arterial"

    if highway in {
        "tertiary", "tertiary_link", "unclassified",
    }:
        return "collector"

    return "local"


def parse_speed(value, highway):
    """Return a reasonable speed in km/h."""
    if isinstance(value, list):
        value = value[0] if value else None

    if value:
        try:
            digits = "".join(c for c in str(value) if c.isdigit())
            if digits:
                speed = int(digits)
                if 5 <= speed <= 130:
                    return speed
        except (TypeError, ValueError):
            pass

    if highway in {"motorway", "motorway_link"}:
        return 80
    if highway in {"trunk", "trunk_link", "primary", "primary_link"}:
        return 50
    if highway in {"secondary", "secondary_link", "tertiary"}:
        return 40
    return 30


def parse_lanes(value):
    if isinstance(value, list):
        value = value[0] if value else None

    try:
        return max(1, min(int(str(value).split(";")[0]), 12))
    except (TypeError, ValueError):
        return 2


def haversine_m(lat1, lon1, lat2, lon2):
    radius = 6_371_000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return 2 * radius * math.asin(min(1, math.sqrt(a)))


def nearest_node_id(lat, lon, node_rows):
    best_id = None
    best_distance = float("inf")

    for node_id, node_lat, node_lon in node_rows:
        distance = haversine_m(lat, lon, node_lat, node_lon)
        if distance < best_distance:
            best_distance = distance
            best_id = node_id

    return best_id


def main():
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Source database not found: {SOURCE_DB}")

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"SQLite schema not found: {SCHEMA_FILE}")

    print("Downloading OpenStreetMap street network...")
    print(f"Center: {CENTER_LAT}, {CENTER_LON}")
    print(f"Radius: {DISTANCE_METERS} metres")

    graph = ox.graph_from_point(
        (CENTER_LAT, CENTER_LON),
        dist=DISTANCE_METERS,
        network_type="drive",
        simplify=True,
        retain_all=False,
    )

    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        raise RuntimeError("OpenStreetMap returned an empty road network.")

    # Existing CityMind graph_builder uses an undirected graph.
    graph = ox.convert.to_undirected(graph)

    # Create a fresh test database; never delete the original city.db.
    if OUTPUT_DB.exists():
        OUTPUT_DB.unlink()

    conn = sqlite3.connect(OUTPUT_DB)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

        osm_to_internal = {}
        node_rows = []

        print("Importing road nodes...")
        for internal_id, (osm_id, attrs) in enumerate(
            graph.nodes(data=True), start=1
        ):
            lat = float(attrs["y"])
            lon = float(attrs["x"])
            osm_to_internal[osm_id] = internal_id

            conn.execute(
                """
                INSERT INTO road_nodes
                    (id, osm_node_id, lat, lon, is_signal)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    internal_id,
                    int(osm_id),
                    lat,
                    lon,
                    int(bool(attrs.get("highway") == "traffic_signals")),
                ),
            )
            node_rows.append((internal_id, lat, lon))

        print("Importing road segments and geometry...")
        road_id = 1

        for u, v, attrs in graph.edges(data=True):
            if u not in osm_to_internal or v not in osm_to_internal:
                continue

            node_a = osm_to_internal[u]
            node_b = osm_to_internal[v]

            # OSMnx supplies the actual curved line when available.
            geometry = attrs.get("geometry")

            if geometry is not None:
                coordinates = [
                    [float(lat), float(lon)]
                    for lon, lat in geometry.coords
                ]
            else:
                coordinates = [
                    [float(graph.nodes[u]["y"]), float(graph.nodes[u]["x"])],
                    [float(graph.nodes[v]["y"]), float(graph.nodes[v]["x"])],
                ]

            # Ensure geometry has at least two points.
            if len(coordinates) < 2:
                continue

            length_m = float(attrs.get("length", 0))
            if length_m <= 0:
                length_m = sum(
                    haversine_m(
                        coordinates[i][0], coordinates[i][1],
                        coordinates[i + 1][0], coordinates[i + 1][1],
                    )
                    for i in range(len(coordinates) - 1)
                )

            highway = attrs.get("highway", "residential")
            if isinstance(highway, list):
                highway = highway[0] if highway else "residential"

            name = attrs.get("name", f"Unnamed road {road_id}")
            if isinstance(name, list):
                name = name[0] if name else f"Unnamed road {road_id}"
            if not name:
                name = f"Unnamed road {road_id}"

            speed = parse_speed(attrs.get("maxspeed"), highway)
            lanes = parse_lanes(attrs.get("lanes"))
            category = road_class(highway)
            capacity = (
                1800 if category == "arterial"
                else 1000 if category == "collector"
                else 600
            )

            conn.execute(
                """
                INSERT INTO roads (
                    id, osm_way_id, name, road_class, node_a, node_b,
                    length_m, speed_kmph, capacity_vph, lanes, oneway,
                    is_closed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    road_id,
                    int(attrs["osmid"][0])
                    if isinstance(attrs.get("osmid"), list)
                    else int(attrs["osmid"])
                    if attrs.get("osmid") is not None
                    else None,
                    str(name),
                    category,
                    node_a,
                    node_b,
                    length_m,
                    speed,
                    capacity,
                    lanes,
                    int(bool(attrs.get("oneway", False))),
                ),
            )

            # SQLite needs a migration to add this column.
            # Store geometry in a side table to keep the original schema valid.
            if road_id == 1:
                conn.execute(
                    """
                    CREATE TABLE road_geometry (
                        road_id INTEGER PRIMARY KEY
                            REFERENCES roads(id) ON DELETE CASCADE,
                        coordinates_json TEXT NOT NULL
                    )
                    """
                )

            conn.execute(
                """
                INSERT INTO road_geometry (road_id, coordinates_json)
                VALUES (?, ?)
                """,
                (road_id, json.dumps(coordinates)),
            )

            road_id += 1

        print("Copying existing facilities, zones and scenario history...")
        source = sqlite3.connect(SOURCE_DB)
        source.row_factory = sqlite3.Row

        try:
            for row in source.execute("SELECT * FROM facilities"):
                row = dict(row)
                nearest = nearest_node_id(row["lat"], row["lon"], node_rows)

                conn.execute(
                    """
                    INSERT INTO facilities
                        (id, facility_type, name, lat, lon,
                         nearest_node_id, capacity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"], row["facility_type"], row["name"],
                        row["lat"], row["lon"], nearest, row["capacity"],
                    ),
                )

            for row in source.execute("SELECT * FROM population_zones"):
                row = dict(row)
                nearest = nearest_node_id(
                    row["centroid_lat"], row["centroid_lon"], node_rows
                )

                conn.execute(
                    """
                    INSERT INTO population_zones
                        (id, name, centroid_lat, centroid_lon,
                         nearest_node_id, population)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"], row["name"], row["centroid_lat"],
                        row["centroid_lon"], nearest, row["population"],
                    ),
                )

            for row in source.execute("SELECT * FROM scenarios"):
                conn.execute(
                    """
                    INSERT INTO scenarios
                        (id, scenario_type, input_params, result_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"], row["scenario_type"], row["input_params"],
                        row["result_json"], row["created_at"],
                    ),
                )
        finally:
            source.close()

        conn.commit()

        print("\nImport successful.")
        print(f"Test database: {OUTPUT_DB}")
        print(f"Road nodes: {len(node_rows)}")
        print(f"Road segments: {road_id - 1}")
        print("Original city.db has not been modified.")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()