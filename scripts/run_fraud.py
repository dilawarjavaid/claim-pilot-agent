import sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claim_pilot.schemas import ClaimSubmission
from claim_pilot.agents.intake import run_intake
from claim_pilot.agents.fraud import run_fraud_check

claims = json.loads((ROOT / "data/claims/sample_claims.json").read_text())

for raw in claims:
    sub = ClaimSubmission(**raw)
    extracted = run_intake(sub)
    assessment, trace = run_fraud_check(sub, extracted)
    print(f"\n=== {sub.claim_id} ===")
    for t in trace:
        print(f"  tool: {t['tool']}({t['args']}) -> {t['result']}")
    print(assessment.model_dump_json(indent=2))