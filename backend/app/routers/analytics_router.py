from fastapi import APIRouter, Depends, HTTPException

from engine.analytics import (
    compute_dashboard_summary, compute_infrastructure_health,
    compute_emergency_response_coverage, compute_scenario_trends,
)
from ..deps import get_db, require_permission

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def dashboard(conn=Depends(get_db), user: dict = Depends(require_permission("view"))):
    try:
        return compute_dashboard_summary(conn)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/infrastructure-health")
def infrastructure_health(conn=Depends(get_db), user: dict = Depends(require_permission("view"))):
    try:
        return compute_infrastructure_health(conn)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emergency-coverage")
def emergency_coverage(conn=Depends(get_db), user: dict = Depends(require_permission("view"))):
    try:
        return compute_emergency_response_coverage(conn)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenario-trends")
def scenario_trends(conn=Depends(get_db), user: dict = Depends(require_permission("view"))):
    try:
        return compute_scenario_trends(conn)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))