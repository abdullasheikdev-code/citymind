import json
import tempfile
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..deps import get_db, require_permission
from ..reports import generate_report
from ..llm import explain_locally

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{scenario_id}")
def get_report(scenario_id: int, conn=Depends(get_db), user: dict = Depends(require_permission("view"))):
    row = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    result = json.loads(row["result_json"])
    explanation = explain_locally(result)
    tmp_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
    generate_report(result, explanation, tmp_path)
    return FileResponse(tmp_path, media_type="application/pdf",
                         filename=f"citymind-report-scenario-{scenario_id}.pdf")