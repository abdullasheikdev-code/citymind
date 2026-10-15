from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str
    password: str
    role: Literal["admin", "planner", "viewer"] = "viewer"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class RoadClosureRequest(BaseModel):
    road_id: Optional[int] = None
    road_name: Optional[str] = None


class NewFacilityRequest(BaseModel):
    facility_type: Literal["hospital", "school", "fire_station", "police_station", "bus_stop", "parking"]
    lat: float
    lon: float
    name: Optional[str] = None


class SimulationResponse(BaseModel):
    scenario_id: Optional[int] = None
    result: dict
    explanation: str


class ScenarioSummary(BaseModel):
    id: int
    scenario_type: str
    created_at: datetime


class ScenarioCompareRequest(BaseModel):
    scenario_id_a: int
    scenario_id_b: int


class KnowledgeBaseQuery(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


class ReportRequest(BaseModel):
    scenario_id: int