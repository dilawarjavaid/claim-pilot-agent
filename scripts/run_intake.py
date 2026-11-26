import sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claim_pilot.schemas import ClaimSubmission
from claim_pilot.agents.intake import run_intake

claims = json.loads((ROOT / "data/claims/sample_claims.json").read_text())

for raw in claims:
    claim = ClaimSubmission(**raw)
    result = run_intake(claim)
    print(f"\n=== {claim.claim_id} ===")
    print(result.model_dump_json(indent=2))