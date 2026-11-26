from datetime import date
from typing import Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.types import Command

from claim_pilot.graph import build_graph
from claim_pilot.schemas import ClaimSubmission

app = FastAPI(title="Claim Pilot API", version="0.1.0")
graph = build_graph()
CLAIM_IDS: list[str] = []   # in-memory index; swap for a DB later


class ClaimIn(BaseModel):
    policy_number: str
    description: str
    submitted_on: Optional[date] = None


class DecisionIn(BaseModel):
    action: Literal["approve", "deny", "escalate"]
    note: str = ""


def _config(claim_id: str) -> dict:
    return {"configurable": {"thread_id": claim_id}}


def _dump(obj):
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj


def claim_view(claim_id: str) -> dict:
    snap = graph.get_state(_config(claim_id))
    if not snap.values:
        raise HTTPException(404, "Claim not found")
    v = snap.values
    pending = "human_review" in snap.next
    return {
        "claim_id": claim_id,
        "status": "pending_review" if pending else v.get("final_status", "processing"),
        "route": v.get("route"),
        "reasons": v.get("reasons", []),
        "submission": _dump(v["submission"]),
        "extracted": _dump(v.get("extracted")),
        "coverage": _dump(v.get("coverage")),
        "fraud": _dump(v.get("fraud")),
        "fraud_trace": v.get("fraud_trace", []),
        "human_decision": v.get("human_decision"),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/claims")
def submit_claim(body: ClaimIn):
    claim_id = f"CLM-{uuid4().hex[:6].upper()}"
    submission = ClaimSubmission(
        claim_id=claim_id,
        policy_number=body.policy_number.strip().upper(),
        submitted_on=body.submitted_on or date.today(),
        description=body.description,
    )
    graph.invoke({"submission": submission}, _config(claim_id))
    CLAIM_IDS.append(claim_id)
    return claim_view(claim_id)


@app.get("/claims")
def list_claims():
    return [claim_view(cid) for cid in reversed(CLAIM_IDS)]


@app.get("/claims/{claim_id}")
def get_claim(claim_id: str):
    return claim_view(claim_id)


@app.post("/claims/{claim_id}/decision")
def decide(claim_id: str, body: DecisionIn):
    if claim_view(claim_id)["status"] != "pending_review":
        raise HTTPException(409, "Claim is not awaiting review")
    graph.invoke(Command(resume=body.model_dump()), _config(claim_id))
    return claim_view(claim_id)