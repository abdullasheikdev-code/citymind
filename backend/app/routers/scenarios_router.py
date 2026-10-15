import json
from fastapi import APIRouter, Depends, HTTPException

from ..schemas import ScenarioSummary, ScenarioCompareRequest
from ..deps import get_db, require_permission

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioSummary])
def list_scenarios(conn=Depends(get_db), user: dict = Depends(require_permission("view"))):
    rows = conn.execute("SELECT id, scenario_type, created_at FROM scenarios ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@router.get("/{scenario_id}")
def get_scenario(scenario_id: int, conn=Depends(get_db), user: dict = Depends(require_permission("view"))):
    row = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    d = dict(row)
    d["input_params"] = json.loads(d["input_params"])
    d["result_json"] = json.loads(d["result_json"])
    return d


@router.post("/compare")
def compare_scenarios(payload: ScenarioCompareRequest, conn=Depends(get_db),
                       user: dict = Depends(require_permission("view"))):
    def load(scenario_id):
        row = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")
        return json.loads(row["result_json"])

    result_a = load(payload.scenario_id_a)
    result_b = load(payload.scenario_id_b)
    if result_a["scenario_type"] != result_b["scenario_type"]:
        raise HTTPException(status_code=400, detail="Cannot compare different scenario types")

    metric_diff = {
        key: {"option_a": result_a["metrics"].get(key), "option_b": result_b["metrics"].get(key)}
        for key in result_a["metrics"]
    }
    return {
        "scenario_type": result_a["scenario_type"],
        "option_a": {"id": payload.scenario_id_a, "input": result_a["input"]},
        "option_b": {"id": payload.scenario_id_b, "input": result_b["input"]},
        "metric_comparison": metric_diff,
    }