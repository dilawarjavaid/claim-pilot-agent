from langchain_core.prompts import ChatPromptTemplate
from claim_pilot.llm import get_llm
from claim_pilot.rag import search_clauses
from claim_pilot.schemas import (
    CoverageDecision, CoverageStatus, ExtractedClaim, PolicyRecord,
)

SYSTEM_PROMPT = """You are the coverage analyst for a property and casualty insurer.
Decide whether the claim is covered using ONLY the policy clauses provided.

Rules:
- Cite clause IDs (e.g. A2, H4) for every conclusion. Never cite a clause not shown below.
- If a special limit or sub-limit applies, use status "partial" and explain it in concerns.
- If key facts are missing to decide, use status "insufficient_info".
- Policy deductible is {deductible}. Report 0 if a clause waives it.
- Do not judge fraud. That is another agent's job.

Policy clauses:
{clauses}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Claim facts:\n{claim}"),
])


def run_policy_check(claim: ExtractedClaim, policy: PolicyRecord) -> CoverageDecision:
    query = f"{claim.loss_type.value}: {claim.summary} Items: {', '.join(claim.damaged_items)}"
    clauses = search_clauses(query, policy.product)
    clause_text = "\n\n".join(f"[{c['clause_id']}] {c['text']}" for c in clauses)

    llm = get_llm().with_structured_output(CoverageDecision)
    decision: CoverageDecision = (prompt | llm).invoke({
        "deductible": policy.deductible,
        "clauses": clause_text,
        "claim": claim.model_dump_json(indent=2),
    })

    # Guardrail: every citation must come from the retrieved clauses
    retrieved = {c["clause_id"] for c in clauses}
    bad = [c for c in decision.cited_clauses if c not in retrieved]
    if bad or not decision.cited_clauses:
        decision.status = CoverageStatus.INSUFFICIENT_INFO
        decision.concerns.append(f"Citation check failed (invalid or missing: {bad or 'none cited'})")
    return decision