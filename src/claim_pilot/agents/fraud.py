import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from claim_pilot.llm import get_llm
from claim_pilot.policies import get_policy
from claim_pilot.schemas import ClaimSubmission, ExtractedClaim, FraudAssessment, LossType
from claim_pilot.tools import TOOLS, TOOL_MAP

INVESTIGATE_PROMPT = """You are a fraud screening analyst at a property and casualty insurer.
Use the tools to check for red flags. Always check policy age and prior claims.
If the loss is weather-related and a location and date are known, verify the weather.
Call tools as needed, then reply with a short plain-text summary of what you found.
Be fair: most claims are legitimate. Missing information is not fraud by itself."""

ASSESS_PROMPT = """Based on the investigation findings, produce a fraud risk assessment.
- low: no meaningful red flags
- medium: one notable flag (e.g. prior similar claim, unverifiable weather)
- high: strong indicators (e.g. theft or major loss shortly after policy start)
Evidence must only contain facts from the tool results."""

THEFT_TYPES = {LossType.AUTO_THEFT, LossType.HOME_THEFT}


def run_fraud_check(submission: ClaimSubmission, claim: ExtractedClaim, max_steps: int = 6):
    llm = get_llm().bind_tools(TOOLS)
    messages = [
        SystemMessage(INVESTIGATE_PROMPT),
        HumanMessage(
            f"Policy number: {submission.policy_number}\n"
            f"Submitted on: {submission.submitted_on}\n"
            f"Extracted claim:\n{claim.model_dump_json(indent=2)}"
        ),
    ]
    trace = []

    # Agent loop: the LLM picks tools until it stops asking for them
    for _ in range(max_steps):
        ai = llm.invoke(messages)
        messages.append(ai)
        if not ai.tool_calls:
            break
        for call in ai.tool_calls:
            result = TOOL_MAP[call["name"]].invoke(call["args"])
            trace.append({"tool": call["name"], "args": call["args"], "result": result})
            messages.append(ToolMessage(content=json.dumps(result), tool_call_id=call["id"]))

    findings = ai.content
    evidence_text = json.dumps(trace, indent=2, default=str)

    assessor = get_llm().with_structured_output(FraudAssessment)
    assessment: FraudAssessment = assessor.invoke([
        SystemMessage(ASSESS_PROMPT),
        HumanMessage(f"Claim:\n{claim.model_dump_json()}\n\nTool results:\n{evidence_text}\n\nAnalyst notes:\n{findings}"),
    ])

    # Deterministic guardrail: a business rule the LLM cannot override
    policy = get_policy(submission.policy_number)
    if policy and claim.incident_date and claim.loss_type in THEFT_TYPES:
        days = (claim.incident_date - policy.start_date).days
        if days < 30 and assessment.risk_level != "high":
            assessment.risk_level = "high"
            assessment.flags.append(f"Rule: theft claim {days} days after policy start")

    return assessment, trace