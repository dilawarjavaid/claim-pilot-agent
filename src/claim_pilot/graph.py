from typing import Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from claim_pilot.agents.intake import run_intake
from claim_pilot.agents.policy import run_policy_check
from claim_pilot.agents.fraud import run_fraud_check
from claim_pilot.policies import get_policy
from claim_pilot.schemas import (
    ClaimSubmission, CoverageDecision, CoverageStatus,
    ExtractedClaim, FraudAssessment, PolicyRecord,
)

AUTO_APPROVE_LIMIT = 5000  # CAD


class ClaimState(TypedDict, total=False):
    submission: ClaimSubmission
    policy: Optional[PolicyRecord]
    extracted: ExtractedClaim
    coverage: Optional[CoverageDecision]
    fraud: FraudAssessment
    fraud_trace: list
    route: str            # auto_approve | adjuster | investigate
    reasons: list[str]
    human_decision: Optional[dict]
    final_status: str


# ---------- nodes ----------
def intake_node(state: ClaimState):
    sub = state["submission"]
    return {"extracted": run_intake(sub), "policy": get_policy(sub.policy_number)}


def policy_node(state: ClaimState):
    if state.get("policy") is None:
        return {"coverage": None}
    return {"coverage": run_policy_check(state["extracted"], state["policy"])}


def fraud_node(state: ClaimState):
    assessment, trace = run_fraud_check(state["submission"], state["extracted"])
    return {"fraud": assessment, "fraud_trace": trace}


def router_node(state: ClaimState):
    cov, fraud, claim = state.get("coverage"), state["fraud"], state["extracted"]

    if state.get("policy") is None:
        return {"route": "adjuster", "reasons": ["Policy number not found"]}

    if fraud.risk_level == "high":
        return {"route": "investigate", "reasons": ["High fraud risk", *fraud.flags]}

    reasons = []
    if cov.status != CoverageStatus.COVERED:
        reasons.append(f"Coverage status: {cov.status.value} ({'; '.join(cov.concerns) or 'no concerns given'})")
    if fraud.risk_level == "medium":
        reasons.append("Medium fraud risk: " + "; ".join(fraud.flags))
    if claim.injuries:
        reasons.append("Injury reported")
    if claim.estimated_amount is None:
        reasons.append("No cost estimate provided")
    elif claim.estimated_amount > AUTO_APPROVE_LIMIT:
        reasons.append(f"Amount ${claim.estimated_amount:,.0f} exceeds ${AUTO_APPROVE_LIMIT:,} auto-approve limit")

    if reasons:
        return {"route": "adjuster", "reasons": reasons}
    return {
        "route": "auto_approve",
        "reasons": [
            f"Covered under {', '.join(cov.cited_clauses)}, low fraud risk, "
            f"${claim.estimated_amount:,.0f} within auto-approve limit"
        ],
    }


def human_review_node(state: ClaimState):
    # Pauses the graph. Execution resumes when Command(resume=...) is sent.
    decision = interrupt({
        "claim_id": state["submission"].claim_id,
        "route": state["route"],
        "reasons": state["reasons"],
    })
    return {"human_decision": decision}


def finalize_node(state: ClaimState):
    if state["route"] == "auto_approve":
        return {"final_status": "approved_automatically"}
    action = state["human_decision"]["action"]
    return {"final_status": f"{action}_by_adjuster"}


def route_after_router(state: ClaimState) -> str:
    return "finalize" if state["route"] == "auto_approve" else "human_review"


# ---------- graph ----------
def build_graph(checkpointer=None):
    g = StateGraph(ClaimState)
    g.add_node("intake", intake_node)
    g.add_node("policy_check", policy_node)
    g.add_node("fraud_check", fraud_node)
    g.add_node("router", router_node)
    g.add_node("human_review", human_review_node)
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "intake")
    g.add_edge("intake", "policy_check")              # fan out: run in parallel
    g.add_edge("intake", "fraud_check")
    g.add_edge(["policy_check", "fraud_check"], "router")  # wait for both
    g.add_conditional_edges("router", route_after_router, ["finalize", "human_review"])
    g.add_edge("human_review", "finalize")
    g.add_edge("finalize", END)

    serde = JsonPlusSerializer(allowed_msgpack_modules=[
        ("claim_pilot.schemas", name) for name in (
            "ClaimSubmission", "ExtractedClaim", "LossType", "PolicyRecord",
            "CoverageStatus", "CoverageDecision", "FraudAssessment",
        )
    ])
    return g.compile(checkpointer=checkpointer or MemorySaver(serde=serde))