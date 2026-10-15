"""
CityMind AI explanation layer.

All numerical simulation metrics come from the graph engine.
Ollama explains the computed results; deterministic templates
are used if the local model is unavailable or too slow.
"""

import json
import os
import urllib.error
import urllib.request


SYSTEM_PROMPT = """
You are CityMind, an urban planning assistant.

Explain the supplied road-network simulation results in concise,
professional language for a city planner.

Strict rules:
1. Never invent or change numerical values.
2. Use only facts present in the supplied JSON.
3. Clearly distinguish computed results from recommendations.
4. If a metric is zero, report zero accurately.
5. Keep the answer under 120 words.
"""


def build_user_prompt(simulation_result: dict) -> str:
    """Send only the information needed to explain the simulation."""
    result = {
        "scenario_type": simulation_result.get("scenario_type"),
        "input": simulation_result.get("input", {}),
        "metrics": simulation_result.get("metrics", {}),
        "recommendation": simulation_result.get("recommendation"),
    }

    return (
        "Explain these computed simulation results. "
        "Do not invent numbers or facts.\n\n"
        + json.dumps(result, separators=(",", ":"), ensure_ascii=False)
    )


def call_openai_explain(
    simulation_result: dict,
    api_key: str = None,
) -> str:
    """Optional OpenAI explanation; requires a configured API key."""
    api_key = api_key or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key, timeout=10.0, max_retries=0)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(simulation_result),
            },
        ],
        temperature=0.2,
        max_tokens=180,
    )

    answer = response.choices[0].message.content
    if not answer:
        raise RuntimeError("OpenAI returned an empty explanation.")

    return answer.strip()


def call_ollama_explain(simulation_result: dict) -> str:
    """Generate a locally hosted explanation with a strict time limit."""
    import urllib.request
    import urllib.error
    import time

    payload = {
        "model": os.environ.get("OLLAMA_MODEL", "llama3.2"),
        "system": SYSTEM_PROMPT,
        "prompt": build_user_prompt(simulation_result),
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 180,
        },
    }

    request = urllib.request.Request(
        os.environ.get(
            "OLLAMA_URL",
            "http://127.0.0.1:11434/api/generate",
        ),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            result = json.loads(response.read().decode("utf-8"))

        explanation = result.get("response", "").strip()

        if not explanation:
            raise RuntimeError("Ollama returned an empty explanation.")

        print(
            f"[CityMind] Ollama explanation: "
            f"{time.perf_counter() - start:.2f}s"
        )

        return explanation

    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(
            f"[CityMind] Ollama unavailable or timed out: {exc}"
        )
        raise RuntimeError("Local AI explanation timed out.") from exc

def explain_with_ai_fallback(simulation_result: dict) -> str:
    """
    Try local AI first, then use a deterministic explanation.
    A slow local model should not block the request for 120 seconds.
    """
    try:
        return call_ollama_explain(simulation_result)
    except Exception:
        try:
            return explain_locally(simulation_result)
        except (ValueError, KeyError, TypeError):
            return _explain_generic(simulation_result)


def explain_locally(simulation_result: dict) -> str:
    """Deterministic fallback based on precomputed engine metrics."""
    scenario_type = simulation_result.get("scenario_type")

    if scenario_type in ("road_closure", "bridge_closure"):
        return _explain_road_closure(simulation_result)

    if scenario_type == "new_facility":
        return _explain_new_facility(simulation_result)

    return _explain_generic(simulation_result)


def _explain_road_closure(result: dict) -> str:
    metrics = result["metrics"]
    road_name = result.get("input", {}).get("road_name", "the selected road")

    lines = [
        f"Road closure scenario for {road_name}.",
        (
            "Zones cut off entirely: "
            f"{metrics.get('zones_cut_off_entirely', 0)}."
        ),
        (
            "Average hospital route delay: "
            f"{metrics.get('avg_hospital_route_delay_pct', 0)}%."
        ),
        (
            "Average school route delay: "
            f"{metrics.get('avg_school_route_delay_pct', 0)}%."
        ),
        (
            "Zones with increased hospital travel: "
            f"{metrics.get('zones_with_increased_hospital_travel', 0)}."
        ),
        (
            "Zones with increased school travel: "
            f"{metrics.get('zones_with_increased_school_travel', 0)}."
        ),
    ]

    recommendation = result.get("recommendation")
    if recommendation and recommendation.get("text"):
        lines.append(f"Recommendation: {recommendation['text']}")

    return " ".join(lines)


def _explain_new_facility(result: dict) -> str:
    metrics = result["metrics"]
    inputs = result.get("input", {})
    name = inputs.get("name", "the proposed facility")
    facility_type = inputs.get("facility_type", "facility").replace("_", " ")

    population = metrics.get("population_newly_best_served", 0)
    zones = metrics.get("zones_better_served", 0)
    coverage = metrics.get("population_coverage_pct_of_city", 0)
    saved = metrics.get("avg_time_saved_min_for_those_zones", 0)

    if population == 0:
        return (
            f"The proposed {facility_type}, {name}, does not become the closest "
            "facility for any population zone in this simulation. "
            "Consider evaluating another location."
        )

    return (
        f"The proposed {name} becomes the closest {facility_type} for "
        f"{zones} zone(s), covering {population} people "
        f"({coverage}% of the tracked population). "
        f"Average travel-time saving for those zones: {saved} minutes."
    )


def _explain_generic(result: dict) -> str:
    """Fallback for simulation types without a dedicated template."""
    scenario_type = result.get("scenario_type", "unknown")
    metrics = result.get("metrics", {})

    lines = [
        f"Scenario: {scenario_type.replace('_', ' ').title()}."
    ]

    for key, value in metrics.items():
        lines.append(f"{key.replace('_', ' ').title()}: {value}.")

    recommendation = result.get("recommendation")
    if recommendation and recommendation.get("text"):
        lines.append(f"Recommendation: {recommendation['text']}")

    return " ".join(lines)