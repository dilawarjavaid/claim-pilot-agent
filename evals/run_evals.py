import sys, json, time, pathlib
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from claim_pilot.config import MODEL
from claim_pilot.graph import build_graph
from claim_pilot.llm import get_llm
from claim_pilot.schemas import ClaimSubmission

CHECKS = ["route", "incident_date", "amount", "coverage", "clauses", "fraud", "grounded"]

JUDGE_PROMPT = """You are auditing an AI fraud analyst for factual accuracy.
Ground truth = the customer's claim facts + the tool results.
A statement is UNSUPPORTED only if it contradicts these sources or states a fact found in neither
(wrong numbers, wrong time spans, invented records). Compute date differences carefully.
Do NOT flag statements for being irrelevant, obvious, or about missing information.
General risk reasoning (e.g. "this is a known fraud indicator") is fine."""


class GroundingVerdict(BaseModel):
    unsupported_statements: list[str]


def judge_grounding(state) -> list[str]:
    fraud, claim = state["fraud"], state["extracted"]
    statements = [s for s in fraud.flags + fraud.evidence if not s.startswith("Rule:")]
    if not statements:
        return []
    judge = get_llm().with_structured_output(GroundingVerdict)
    verdict = judge.invoke([
        SystemMessage(JUDGE_PROMPT),
        HumanMessage(
            f"Incident date: {claim.incident_date}\n\n"
            f"Customer claim facts:\n{claim.model_dump_json(indent=2)}\n\n"
            f"Tool results:\n{json.dumps(state['fraud_trace'], indent=2, default=str)}\n\n"
            "Statements:\n" + "\n".join(f"- {s}" for s in statements)
        ),
    ])
    return verdict.unsupported_statements


def evaluate(state, exp) -> tuple[dict, list[str]]:
    x, cov, fraud = state["extracted"], state["coverage"], state["fraud"]
    actual = {
        "route": state["route"],
        "incident_date": x.incident_date.isoformat() if x.incident_date else None,
        "amount": x.estimated_amount,
        "coverage": cov.status.value if cov else None,
        "clauses": cov.cited_clauses if cov else [],
        "fraud": fraud.risk_level,
    }
    results = {
        "route": actual["route"] == exp["route"],
        "incident_date": exp["incident_date"] == "skip" or actual["incident_date"] == exp["incident_date"],
        "amount": actual["amount"] == exp["amount"],
        "coverage": actual["coverage"] == exp["coverage"],
        "clauses": any(c in actual["clauses"] for c in exp["clauses_any"]),
        "fraud": actual["fraud"] == exp["fraud"],
    }
    notes = [
        f"{k}: expected {exp[k if k != 'clauses' else 'clauses_any']}, got {actual[k]}"
        for k, ok in results.items() if not ok
    ]
    unsupported = judge_grounding(state)
    results["grounded"] = not unsupported
    notes += [f"ungrounded: {s}" for s in unsupported]
    return results, notes


def main():
    claims = {c["claim_id"]: c for c in json.loads((ROOT / "data/claims/sample_claims.json").read_text())}
    labels = json.loads((ROOT / "evals/labels.json").read_text())
    graph = build_graph()
    rows, failures = [], []

    for i, (cid, exp) in enumerate(labels.items()):
        print(f"Evaluating {cid}...")
        sub = ClaimSubmission(**claims[cid])
        state = graph.invoke({"submission": sub}, {"configurable": {"thread_id": f"eval-{cid}-{time.time()}"}})
        results, notes = evaluate(state, exp)
        rows.append((cid, results))
        failures += [f"**{cid}** {n}" for n in notes]
        if i < len(labels) - 1:
            time.sleep(20)  # Groq free-tier rate limit

    totals = {k: sum(r[k] for _, r in rows) for k in CHECKS}
    n = len(rows)

    lines = [
        "# Eval results", "",
        f"Model: `{MODEL}` · Run: {datetime.now():%Y-%m-%d %H:%M} · Claims: {n}", "",
        "| Claim | " + " | ".join(c.replace("_", " ").title() for c in CHECKS) + " |",
        "|---|" + "---|" * len(CHECKS),
    ]
    for cid, r in rows:
        lines.append(f"| {cid} | " + " | ".join("✅" if r[k] else "❌" for k in CHECKS) + " |")
    lines.append("| **Total** | " + " | ".join(f"**{totals[k]}/{n}**" for k in CHECKS) + " |")
    lines += ["", "## Failures", ""] + ([f"- {f}" for f in failures] or ["None 🎉"])

    report = "\n".join(lines)
    (ROOT / "evals/results.md").write_text(report, encoding="utf-8")
    print("\n" + report)


if __name__ == "__main__":
    main()