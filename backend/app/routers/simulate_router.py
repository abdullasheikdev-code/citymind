import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from engine.simulations import (
    simulate_road_closure,
    simulate_new_facility,
)
from engine.simulations_extra import (
    simulate_bridge_closure,
    simulate_new_flyover,
    simulate_accident,
    simulate_power_failure,
    simulate_festival,
)
from engine import db as db_module

from ..schemas import SimulationResponse
from ..deps import get_db, require_permission
from ..llm import explain_with_ai_fallback


router = APIRouter(prefix="/simulate", tags=["simulate"])


def _explain(result: dict) -> str:
    """Generate an AI explanation with a deterministic fallback."""
    return explain_with_ai_fallback(result)


class RoadClosureRequest(BaseModel):
    road_id: int = Field(gt=0)


class NewFacilityRequest(BaseModel):
    facility_type: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    name: str | None = None


def _save_simulation(conn, scenario_type: str, inputs: dict, result: dict):
    """Save a simulation result and return the standard API response."""
    explanation = _explain(result)

    scenario_id = db_module.save_scenario(
        conn,
        scenario_type,
        json.dumps(inputs),
        json.dumps(result),
    )
    conn.commit()

    return SimulationResponse(
        scenario_id=scenario_id,
        result=result,
        explanation=explanation,
    )


@router.post("/road-closure", response_model=SimulationResponse)
def road_closure(
    payload: RoadClosureRequest,
    conn=Depends(get_db),
    user: dict = Depends(require_permission("simulate")),
):
    try:
        result = simulate_road_closure(conn, payload.road_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _save_simulation(
        conn,
        "road_closure",
        {"road_id": payload.road_id},
        result,
    )


@router.post("/new-facility", response_model=SimulationResponse)
def new_facility(
    payload: NewFacilityRequest,
    conn=Depends(get_db),
    user: dict = Depends(require_permission("simulate")),
):
    facility_type = payload.facility_type.strip().lower()

    if facility_type not in {"hospital", "school"}:
        raise HTTPException(
            status_code=400,
            detail="facility_type must be 'hospital' or 'school'",
        )

    try:
        result = simulate_new_facility(
            conn,
            facility_type=facility_type,
            lat=payload.lat,
            lon=payload.lon,
            name=payload.name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _save_simulation(
        conn,
        "new_facility",
        {
            "facility_type": facility_type,
            "lat": payload.lat,
            "lon": payload.lon,
            "name": payload.name,
        },
        result,
    )


@router.post("/bridge-closure", response_model=SimulationResponse)
def bridge_closure(
    road_id: int,
    conn=Depends(get_db),
    user: dict = Depends(require_permission("simulate")),
):
    try:
        result = simulate_bridge_closure(conn, road_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _save_simulation(
        conn, "bridge_closure", {"road_id": road_id}, result
    )


@router.post("/new-flyover", response_model=SimulationResponse)
def new_flyover(
    node_a: int,
    node_b: int,
    speed_kmph: int = 70,
    conn=Depends(get_db),
    user: dict = Depends(require_permission("simulate")),
):
    try:
        result = simulate_new_flyover(
            conn, node_a, node_b, speed_kmph=speed_kmph
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _save_simulation(
        conn,
        "new_flyover",
        {
            "node_a": node_a,
            "node_b": node_b,
            "speed_kmph": speed_kmph,
        },
        result,
    )


@router.post("/accident", response_model=SimulationResponse)
def accident(
    road_id: int,
    severity: str = "moderate",
    conn=Depends(get_db),
    user: dict = Depends(require_permission("simulate")),
):
    try:
        result = simulate_accident(conn, road_id, severity=severity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _save_simulation(
        conn,
        "accident",
        {"road_id": road_id, "severity": severity},
        result,
    )


@router.post("/power-failure", response_model=SimulationResponse)
def power_failure(
    node_ids: list[int],
    conn=Depends(get_db),
    user: dict = Depends(require_permission("simulate")),
):
    try:
        result = simulate_power_failure(conn, node_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _save_simulation(
        conn,
        "power_failure",
        {"node_ids": node_ids},
        result,
    )


@router.post("/festival", response_model=SimulationResponse)
def festival(
    lat: float,
    lon: float,
    radius_m: float = 300,
    conn=Depends(get_db),
    user: dict = Depends(require_permission("simulate")),
):
    try:
        result = simulate_festival(
            conn, lat, lon, radius_m=radius_m
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _save_simulation(
        conn,
        "festival",
        {"lat": lat, "lon": lon, "radius_m": radius_m},
        result,
    )