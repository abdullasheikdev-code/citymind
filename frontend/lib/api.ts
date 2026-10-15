const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let authToken: string | null = null;
export function setAuthToken(token: string) {
  authToken = token;
  if (typeof window !== "undefined") localStorage.setItem("citymind_token", token);
}
export function loadAuthToken() {
  if (typeof window !== "undefined") authToken = localStorage.getItem("citymind_token");
  return authToken;
}
// Call once on app load (e.g. in a top-level layout effect) so an
// existing session survives a page refresh.
if (typeof window !== "undefined") {
  loadAuthToken();
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export interface TokenResponse { access_token: string; token_type: string; role: string; }
export interface RouteDetail {
  zone: string; population: number; facility?: string;
  time_before_min?: number; time_after_min?: number | null;
  delta_min?: number | null; delta_pct?: number | null;
  reachable_after_closure?: boolean;
  time_to_new_facility_min?: number | null;
  time_to_nearest_existing_min?: number | null;
  new_facility_becomes_closest?: boolean;
}
export interface SimulationResult {
  scenario_type: string;
  input: Record<string, any>;
  basis: Record<string, any>;
  metrics: Record<string, number>;
  hospital_route_detail?: RouteDetail[];
  school_route_detail?: RouteDetail[];
  zone_detail?: RouteDetail[];
  recommendation?: { type: string; text: string; detour_roads: string[] };
}
export interface SimulationResponse {
  scenario_id: number;
  result: SimulationResult;
  explanation: string;
}
export interface ScenarioSummary { id: number; scenario_type: string; created_at: string; }

export const login = (email: string, password: string) =>
  request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });

export const register = (email: string, password: string, role: string) =>
  request<TokenResponse>("/auth/register", { method: "POST", body: JSON.stringify({ email, password, role }) });

export const simulateRoadClosure = (roadId: number) =>
  request<SimulationResponse>("/simulate/road-closure", { method: "POST", body: JSON.stringify({ road_id: roadId }) });

export const simulateNewFacility = (facilityType: string, lat: number, lon: number, name?: string) =>
  request<SimulationResponse>("/simulate/new-facility", {
    method: "POST",
    body: JSON.stringify({ facility_type: facilityType, lat, lon, name }),
  });

export const listScenarios = () => request<ScenarioSummary[]>("/scenarios");
export const getScenario = (id: number) => request<any>(`/scenarios/${id}`);
export const compareScenarios = (idA: number, idB: number) =>
  request<any>("/scenarios/compare", { method: "POST", body: JSON.stringify({ scenario_id_a: idA, scenario_id_b: idB }) });

export function reportDownloadUrl(scenarioId: number) {
  return `${API_BASE}/reports/${scenarioId}`;
}

export const getRoads = () => request<any[]>("/city/roads");
export const getFacilities = (type?: string) => request<any[]>(`/city/facilities${type ? `?type=${type}` : ""}`);
export const getZones = () => request<any[]>("/city/zones");

export const getDashboardSummary = () => request<any>("/analytics/dashboard");
export const getInfrastructureHealth = () => request<any>("/analytics/infrastructure-health");
export const getEmergencyCoverage = () => request<any>("/analytics/emergency-coverage");
export const getScenarioTrends = () => request<any>("/analytics/scenario-trends");