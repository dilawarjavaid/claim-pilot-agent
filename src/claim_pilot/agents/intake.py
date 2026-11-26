from langchain_core.prompts import ChatPromptTemplate
from claim_pilot.llm import get_llm
from claim_pilot.schemas import ClaimSubmission, ExtractedClaim

SYSTEM_PROMPT = """You are the intake agent for a property and casualty insurer.
Extract structured facts from the customer's claim description.

Rules:
- Only use facts stated in the description. Never invent amounts, dates or locations.
- Resolve relative dates ("yesterday", "last week") using the submission date: {submitted_on}.
  If the date is vague (e.g. "last week"), give your best estimate AND add "exact incident date" to missing_info.
- List in missing_info anything an adjuster would need but is absent
  (e.g. cost estimate, location, police report number for theft, photos).
- The summary must be one neutral sentence with no judgement about fraud or coverage."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Policy: {policy_number}\nClaim description:\n{description}"),
])


def run_intake(claim: ClaimSubmission) -> ExtractedClaim:
    llm = get_llm().with_structured_output(ExtractedClaim)
    chain = prompt | llm
    return chain.invoke({
        "submitted_on": claim.submitted_on.isoformat(),
        "policy_number": claim.policy_number,
        "description": claim.description,
    })