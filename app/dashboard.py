import json
import os
from datetime import date
from pathlib import Path

import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
ROOT = Path(__file__).resolve().parents[1]
SAMPLES = {
    c["claim_id"]: c
    for c in json.loads((ROOT / "data/claims/sample_claims.json").read_text())
}
ROUTE_BADGE = {
    "auto_approve": "🟢 Auto-approve",
    "adjuster": "🟡 Adjuster review",
    "investigate": "🔴 Investigate",
}

st.set_page_config(page_title="Claim Pilot", page_icon="🛡️", layout="wide")
st.title("🛡️ Claim Pilot")
st.caption("Multi-agent insurance claims triage · intake → coverage (RAG) + fraud (tools) → router → human review")


def show_claim(c: dict):
    col1, col2, col3 = st.columns(3)
    col1.metric("Route", ROUTE_BADGE.get(c["route"], c["route"]))
    col2.metric("Coverage", (c["coverage"] or {}).get("status", "n/a"))
    col3.metric("Fraud risk", (c["fraud"] or {}).get("risk_level", "n/a"))

    st.markdown("**Why this route:**")
    for r in c["reasons"]:
        st.markdown(f"- {r}")

    with st.expander("📋 Extracted facts (intake agent)"):
        st.json(c["extracted"])
    with st.expander("📜 Coverage decision (policy agent)"):
        cov = c["coverage"]
        if cov:
            st.write(cov["reasoning"])
            st.caption("Cited clauses: " + ", ".join(cov["cited_clauses"]))
            st.json(cov)
    with st.expander("🔍 Fraud checks (tool calls)"):
        for t in c["fraud_trace"]:
            st.code(f"{t['tool']}({t['args']}) -> {t['result']}", language="text")
        st.json(c["fraud"])


def fetch_claims() -> list[dict]:
    try:
        return requests.get(f"{API}/claims", timeout=10).json()
    except requests.RequestException:
        st.error("Can't reach the API. Is uvicorn running?")
        return []


submit_tab, queue_tab, done_tab = st.tabs(["📝 Submit claim", "🧑‍⚖️ Adjuster queue", "✅ Processed"])

# ---------- Submit ----------
with submit_tab:
    choice = st.selectbox("Start from", ["Custom"] + list(SAMPLES))
    sample = SAMPLES.get(choice, {})
    policy = st.text_input("Policy number", sample.get("policy_number", ""), key=f"policy_{choice}")
    submitted_on = st.date_input(
        "Submitted on",
        date.fromisoformat(sample["submitted_on"]) if sample else date.today(),
        key=f"date_{choice}",
    )
    description = st.text_area("What happened?", sample.get("description", ""), height=150, key=f"desc_{choice}")

    if st.button("Submit claim", type="primary", disabled=not (policy and description)):
        with st.spinner("Agents are reviewing the claim…"):
            r = requests.post(
                f"{API}/claims",
                json={"policy_number": policy, "description": description,
                      "submitted_on": submitted_on.isoformat()},
                timeout=300,
            )
        if r.ok:
            st.success(f"Claim {r.json()['claim_id']} processed")
            show_claim(r.json())
        else:
            st.error(f"API error {r.status_code}: {r.text}")

claims = fetch_claims()

# ---------- Queue ----------
with queue_tab:
    st.button("🔄 Refresh")
    pending = [c for c in claims if c["status"] == "pending_review"]
    if not pending:
        st.info("No claims waiting for review.")
    for c in pending:
        cid = c["claim_id"]
        with st.container(border=True):
            st.subheader(f"{cid} · {c['submission']['policy_number']}")
            st.write(f"_{c['submission']['description']}_")
            show_claim(c)
            note = st.text_input("Adjuster note", key=f"note_{cid}")
            b1, b2, b3 = st.columns(3)
            action = None
            if b1.button("✅ Approve", key=f"approve_{cid}"):
                action = "approve"
            if b2.button("❌ Deny", key=f"deny_{cid}"):
                action = "deny"
            if b3.button("🚩 Escalate to SIU", key=f"escalate_{cid}"):
                action = "escalate"
            if action:
                r = requests.post(f"{API}/claims/{cid}/decision",
                                  json={"action": action, "note": note}, timeout=60)
                if r.ok:
                    st.rerun()
                else:
                    st.error(f"API error {r.status_code}: {r.text}")

# ---------- Processed ----------
with done_tab:
    done = [c for c in claims if c["status"] != "pending_review"]
    if not done:
        st.info("No processed claims yet.")
    else:
        st.dataframe(
            [{
                "Claim": c["claim_id"],
                "Policy": c["submission"]["policy_number"],
                "Route": ROUTE_BADGE.get(c["route"], c["route"]),
                "Final status": c["status"],
                "Adjuster note": (c["human_decision"] or {}).get("note", ""),
            } for c in done],
            use_container_width=True,
        )