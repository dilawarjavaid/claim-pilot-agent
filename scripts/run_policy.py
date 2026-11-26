import sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claim_pilot.schemas import ClaimSubmission
from claim_pilot.agents.intake import run_intake
from claim_pilot.agents.policy import run_policy_check
from claim_pilot.policies import get_policy

claims = json.loads((ROOT / "data/claims/sample_claims.json").read_text())

for raw in claims:
    claim = ClaimSubmission(**raw)
    policy = get_policy(claim.policy_number)
    extracted = run_intake(claim)
    decision = run_policy_check(extracted, policy)
    print(f"\n=== {claim.claim_id} ({policy.product}) ===")
    print(decision.model_dump_json(indent=2))