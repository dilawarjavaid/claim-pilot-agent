import json
from datetime import date
from langchain_core.tools import tool
from claim_pilot.config import DATA_DIR
from claim_pilot.policies import get_policy

_history = json.loads((DATA_DIR / "claims/claim_history.json").read_text())
_weather = json.loads((DATA_DIR / "weather_events.json").read_text())


@tool
def check_policy_age(policy_number: str, incident_date: str) -> dict:
    """Return how many days the policy had been active on the incident date (YYYY-MM-DD).
    Claims within 30 days of policy start are a known fraud indicator."""
    policy = get_policy(policy_number)
    if not policy:
        return {"error": "policy not found"}
    days = (date.fromisoformat(incident_date) - policy.start_date).days
    return {"policy_start": policy.start_date.isoformat(), "days_active": days}


@tool
def find_prior_claims(policy_number: str, incident_date: str) -> dict:
    """Return previous claims on this policy, with how many days before the
    current incident (YYYY-MM-DD) each one happened."""
    current = date.fromisoformat(incident_date)
    claims = [
        {**c, "days_before_incident": (current - date.fromisoformat(c["date"])).days}
        for c in _history.get(policy_number, [])
    ]
    return {"prior_claim_count": len(claims), "claims": claims}


@tool
def check_weather(region: str, incident_date: str) -> dict:
    """Check whether a weather event was recorded in a region (city name) on a date (YYYY-MM-DD).
    Use this to verify weather-related claims such as wind, hail or storms."""
    matches = [
        e for e in _weather
        if e["region"].lower() in region.lower() and e["date"] == incident_date
    ]
    return {"events_found": matches} if matches else {"events_found": [], "note": "No recorded event"}


TOOLS = [check_policy_age, find_prior_claims, check_weather]
TOOL_MAP = {t.name: t for t in TOOLS}