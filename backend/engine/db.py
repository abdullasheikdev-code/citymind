"""
Data access layer. Only file that knows SQL.
Swap SQLite -> Postgres here later without touching
graph_builder.py or simulations.py.
"""

import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

DEFAULT_DB_PATH = DATA_DIR / "city.db"

# Set CITYMIND_DB_PATH to choose a different database.
# Without the environment variable, the original city.db is used.
DB_PATH = Path(
    os.environ.get("CITYMIND_DB_PATH", str(DEFAULT_DB_PATH))
).resolve()


def connect(db_path=None):
    """Open a connection to the selected SQLite database."""
    selected_path = Path(db_path).resolve() if db_path else DB_PATH

    if not selected_path.exists():
        raise FileNotFoundError(
            f"Database not found: {selected_path}"
        )

    conn = sqlite3.connect(
        str(selected_path),
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    return conn


def get_all_nodes(conn):
    rows = conn.execute(
        "SELECT id, lat, lon, is_signal FROM road_nodes"
    ).fetchall()

    return {
        r["id"]: {
            "lat": r["lat"],
            "lon": r["lon"],
            "is_signal": bool(r["is_signal"]),
        }
        for r in rows
    }


def get_all_roads(conn, include_closed=True):
    query = "SELECT * FROM roads"

    if not include_closed:
        query += " WHERE is_closed = 0"

    rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def get_road_by_id(conn, road_id: int):
    row = conn.execute(
        "SELECT * FROM roads WHERE id = ?",
        (road_id,),
    ).fetchone()

    return dict(row) if row else None


def get_road_by_name(conn, name: str):
    row = conn.execute(
        "SELECT * FROM roads WHERE name = ? LIMIT 1",
        (name,),
    ).fetchone()

    return dict(row) if row else None


def get_facilities(conn, facility_type: str = None):
    if facility_type:
        rows = conn.execute(
            "SELECT * FROM facilities WHERE facility_type = ?",
            (facility_type,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM facilities"
        ).fetchall()

    return [dict(row) for row in rows]


def get_population_zones(conn):
    rows = conn.execute(
        "SELECT * FROM population_zones"
    ).fetchall()

    return [dict(row) for row in rows]


def save_scenario(
    conn,
    scenario_type: str,
    input_params_json: str,
    result_json: str,
):
    cursor = conn.execute(
        """
        INSERT INTO scenarios
        (scenario_type, input_params, result_json)
        VALUES (?, ?, ?)
        """,
        (scenario_type, input_params_json, result_json),
    )

    conn.commit()
    return cursor.lastrowid