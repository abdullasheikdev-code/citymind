"""City API routes for roads, facilities, zones, and infrastructure edits."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from engine import db as db_module
from ..deps import get_db, require_permission

router = APIRouter(prefix="/city", tags=["city"])


@router.get("/roads")
def list_roads(conn=Depends(get_db)):
    """
    Return road data, endpoint coordinates, and detailed OSM geometry
    when the connected SQLite database contains a road_geometry table.
    """

    roads = db_module.get_all_roads(conn)
    nodes = db_module.get_all_nodes(conn)

    geometry_by_road = {}

    # Detect whether detailed road geometry is available.
    geometry_table = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'road_geometry'
        """
    ).fetchone()

    if geometry_table:
        geometry_rows = conn.execute(
            """
            SELECT road_id, coordinates_json
            FROM road_geometry
            """
        ).fetchall()

        for row in geometry_rows:
            try:
                coordinates = json.loads(row["coordinates_json"])

                # Validate the expected [[lat, lon], ...] structure.
                if (
                    isinstance(coordinates, list)
                    and len(coordinates) >= 2
                    and all(
                        isinstance(point, (list, tuple))
                        and len(point) >= 2
                        for point in coordinates
                    )
                ):
                    geometry_by_road[row["road_id"]] = coordinates
                else:
                    geometry_by_road[row["road_id"]] = []

            except (json.JSONDecodeError, TypeError, ValueError):
                geometry_by_road[row["road_id"]] = []

    result = []

    for road in roads:
        road_data = dict(road)

        node_a = nodes.get(road_data.get("node_a"))
        node_b = nodes.get(road_data.get("node_b"))

        # Skip malformed roads with missing endpoint nodes.
        if node_a is None or node_b is None:
            continue

        road_data.update({
            "node_a_lat": node_a["lat"],
            "node_a_lon": node_a["lon"],
            "node_b_lat": node_b["lat"],
            "node_b_lon": node_b["lon"],
        })

        geometry = geometry_by_road.get(road_data["id"], [])

        # Fallback for the original synthetic database or invalid geometry.
        if len(geometry) < 2:
            geometry = [
                [node_a["lat"], node_a["lon"]],
                [node_b["lat"], node_b["lon"]],
            ]

        road_data["geometry"] = geometry
        result.append(road_data)

    return result


@router.get("/facilities")
def list_facilities(
    type: Optional[str] = None,
    conn=Depends(get_db),
):
    """List facilities, optionally filtered by type."""
    return db_module.get_facilities(conn, type)


@router.get("/zones")
def list_zones(conn=Depends(get_db)):
    """List population zones."""
    return db_module.get_population_zones(conn)


class FacilityCreate(BaseModel):
    facility_type: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    capacity: Optional[int] = Field(default=None, ge=0)


@router.post("/facilities", status_code=201)
def create_facility(
    payload: FacilityCreate,
    conn=Depends(get_db),
    user: dict = Depends(require_permission("edit_infrastructure")),
):
    """Create a facility and connect it to its nearest road node."""

    from engine.graph_builder import build_graph, node_coords
    from engine.geo import nearest_node

    graph = build_graph(conn)

    if graph.number_of_nodes() == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot create a facility because the road network is empty.",
        )

    snapped = nearest_node(
        payload.lat,
        payload.lon,
        node_coords(graph),
    )

    cursor = conn.execute(
        """
        INSERT INTO facilities
            (facility_type, name, lat, lon, nearest_node_id, capacity)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload.facility_type,
            payload.name,
            payload.lat,
            payload.lon,
            snapped,
            payload.capacity,
        ),
    )

    facility_id = cursor.lastrowid

    # Keep the existing audit logging behavior.
    conn.execute(
        """
        INSERT INTO audit_log (user_id, action, detail_json)
        VALUES (?, 'add_facility', ?)
        """,
        (
            int(user["sub"]),
            json.dumps({"facility_id": facility_id}),
        ),
    )

    conn.commit()

    return {"id": facility_id}


@router.delete("/facilities/{facility_id}", status_code=204)
def delete_facility(
    facility_id: int,
    conn=Depends(get_db),
    user: dict = Depends(require_permission("edit_infrastructure")),
):
    """Delete a facility."""
    result = conn.execute(
        "DELETE FROM facilities WHERE id = ?",
        (facility_id,),
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Facility not found",
        )

    conn.commit()
    return None


class FacilityMove(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


@router.patch("/facilities/{facility_id}/move")
def move_facility(
    facility_id: int,
    payload: FacilityMove,
    conn=Depends(get_db),
    user: dict = Depends(require_permission("edit_infrastructure")),
):
    """Move a facility and update its nearest road node."""

    from engine.graph_builder import build_graph, node_coords
    from engine.geo import nearest_node

    existing = conn.execute(
        "SELECT id FROM facilities WHERE id = ?",
        (facility_id,),
    ).fetchone()

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Facility not found",
        )

    graph = build_graph(conn)

    if graph.number_of_nodes() == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot move a facility because the road network is empty.",
        )

    snapped = nearest_node(
        payload.lat,
        payload.lon,
        node_coords(graph),
    )

    conn.execute(
        """
        UPDATE facilities
        SET lat = ?, lon = ?, nearest_node_id = ?
        WHERE id = ?
        """,
        (
            payload.lat,
            payload.lon,
            snapped,
            facility_id,
        ),
    )

    conn.commit()

    return {
        "id": facility_id,
        "nearest_node_id": snapped,
    }