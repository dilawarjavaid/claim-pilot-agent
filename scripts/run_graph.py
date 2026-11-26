import time
import sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from langgraph.types import Command
from claim_pilot.graph import build_graph
from claim_pilot.schemas import ClaimSubmission

graph = build_graph()
claims = json.loads((ROOT / "data/claims/sample_claims.json").read_text())
correct = 0

for raw in claims:
    sub = ClaimSubmission(**raw)
    config = {"configurable": {"thread_id": sub.claim_id}}
    result = graph.invoke({"submission": sub}, config)

    print(f"\n=== {sub.claim_id} → {result['route'].upper()} ===")
    for r in result["reasons"]:
        print(f"  - {r}")

    if "__interrupt__" in result:
        action = ""
        while action not in {"approve", "deny", "escalate"}:
            action = input("  Adjuster decision [approve/deny/escalate]: ").strip().lower() or "approve"
        note = input("  Note: ").strip()
        result = graph.invoke(Command(resume={"action": action, "note": note}), config)

    print(f"  Final status: {result['final_status']}")
    expected = raw["expected_route"]
    correct += result["route"] == expected
    print(f"  Expected route: {expected} {'✅' if result['route'] == expected else '❌'}")
    time.sleep(15)

print(f"\nRouting accuracy: {correct}/{len(claims)}")