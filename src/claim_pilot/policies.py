import json
from claim_pilot.config import DATA_DIR
from claim_pilot.schemas import PolicyRecord

_records = json.loads((DATA_DIR / "policies/policyholders.json").read_text())


def get_policy(policy_number: str) -> PolicyRecord | None:
    raw = _records.get(policy_number)
    return PolicyRecord(policy_number=policy_number, **raw) if raw else None