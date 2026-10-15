"""
Generates a synthetic reference district and loads it into SQLite.
Real OSM import (data/import_osm.py) needs network + a Postgres server,
neither available in this sandbox — this stand-in keeps the engine
buildable and testable now.
"""

import math
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "city.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "sqlite_schema.sql"

ORIGIN_LAT = 13.0500
ORIGIN_LON = 80.2100
GRID_SIZE = 7
BLOCK_M = 400
M_PER_DEG_LAT = 111_320.0


def m_per_deg_lon(lat_deg):
    return 111_320.0 * math.cos(math.radians(lat_deg))


def grid_to_latlon(row, col):
    lat = ORIGIN_LAT + (row * BLOCK_M) / M_PER_DEG_LAT
    lon = ORIGIN_LON + (col * BLOCK_M) / m_per_deg_lon(ORIGIN_LAT)
    return lat, lon


def node_id(row, col):
    return row * GRID_SIZE + col + 1


def build():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())

    nodes = {}
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            nid = node_id(row, col)
            lat, lon = grid_to_latlon(row, col)
            is_signal = 1 if (row % 2 == 0 and col % 2 == 0) else 0
            nodes[nid] = (lat, lon)
            conn.execute(
                "INSERT INTO road_nodes (id, osm_node_id, lat, lon, is_signal) VALUES (?, NULL, ?, ?, ?)",
                (nid, lat, lon, is_signal),
            )

    road_id = 1
    street_names = [
        "MG Road", "Anna Salai", "Ring Road", "Nehru Street", "Gandhi Avenue",
        "College Road", "Market Street", "Station Road", "Lake View Road",
        "Temple Street", "Park Avenue", "Hospital Road", "School Lane",
        "River Road", "Old Mill Road",
    ]

    def road_class_and_specs(is_arterial):
        return ("arterial", 50, 1800, 3) if is_arterial else ("local", 30, 600, 1)

    def insert_road(a, b, name, cls, speed, cap, lanes):
        nonlocal road_id
        lat_a, lon_a = nodes[a]
        lat_b, lon_b = nodes[b]
        from geo import haversine_m
        length_m = haversine_m(lat_a, lon_a, lat_b, lon_b)
        conn.execute(
            "INSERT INTO roads (id, osm_way_id, name, road_class, node_a, node_b, "
            "length_m, speed_kmph, capacity_vph, lanes, oneway, is_closed) "
            "VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)",
            (road_id, name, cls, a, b, length_m, speed, cap, lanes),
        )
        road_id += 1

    name_i = 0
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            a = node_id(row, col)
            if col < GRID_SIZE - 1:
                b = node_id(row, col + 1)
                cls, speed, cap, lanes = road_class_and_specs(row % 3 == 0)
                insert_road(a, b, street_names[name_i % len(street_names)], cls, speed, cap, lanes)
                name_i += 1
            if row < GRID_SIZE - 1:
                b = node_id(row + 1, col)
                cls, speed, cap, lanes = road_class_and_specs(col % 3 == 0)
                insert_road(a, b, street_names[name_i % len(street_names)], cls, speed, cap, lanes)
                name_i += 1

    facilities = [
        ("hospital", "Meridian General Hospital", (1, 1), 350),
        ("hospital", "Riverside Medical Center", (5, 5), 220),
        ("hospital", "St. Anne's Community Hospital", (3, 0), 150),
        ("school", "Lakeview Public School", (0, 4), 800),
        ("school", "Meridian High School", (2, 2), 1200),
        ("school", "Gandhi Memorial School", (6, 1), 650),
        ("school", "St. Mary's Convent School", (4, 6), 900),
        ("school", "Riverside Elementary", (6, 5), 500),
        ("fire_station", "Central Fire Station", (2, 4), 6),
        ("fire_station", "North Ward Fire Station", (0, 0), 4),
        ("fire_station", "Riverside Fire Outpost", (5, 6), 3),
        ("police_station", "MG Road Police Station", (1, 3), None),
        ("police_station", "South Ward Police Station", (5, 1), None),
        ("bus_stop", "Market Street Bus Stop", (1, 0), None),
        ("bus_stop", "College Road Bus Stop", (2, 3), None),
        ("bus_stop", "Station Road Bus Stop", (3, 5), None),
        ("bus_stop", "Temple Street Bus Stop", (4, 2), None),
        ("bus_stop", "Ring Road Bus Stop", (6, 6), None),
        ("parking", "Central Parking Complex", (2, 1), 300),
        ("parking", "Market Parking Lot", (1, 5), 120),
        ("parking", "Riverside Parking", (5, 4), 150),
    ]
    for ftype, fname, (row, col), capacity in facilities:
        lat, lon = grid_to_latlon(row, col)
        conn.execute(
            "INSERT INTO facilities (facility_type, name, lat, lon, nearest_node_id, capacity) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ftype, fname, lat, lon, node_id(row, col), capacity),
        )

    zones = [
        ("Meridian Central", (1, 2), 18500), ("North Heights", (0, 1), 9200),
        ("College Quarter", (2, 3), 15800), ("Old Town", (3, 1), 21000),
        ("Riverside Estates", (5, 4), 12600), ("South Gate", (6, 2), 17300),
        ("Lakeview Suburb", (0, 5), 8400), ("Eastfield", (3, 6), 11200),
        ("Millbrook (underserved)", (6, 0), 9800),
        ("Northgate Fringe (underserved)", (0, 6), 6700),
        ("Station District", (3, 3), 24500), ("Temple Quarter", (4, 1), 13900),
    ]
    for zname, (row, col), pop in zones:
        lat, lon = grid_to_latlon(row, col)
        conn.execute(
            "INSERT INTO population_zones (name, centroid_lat, centroid_lon, nearest_node_id, population) "
            "VALUES (?, ?, ?, ?, ?)",
            (zname, lat, lon, node_id(row, col), pop),
        )

    conn.commit()
    conn.close()
    print(f"Synthetic city built: {DB_PATH}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))
    build()