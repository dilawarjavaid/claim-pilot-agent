from langchain.chat_models import init_chat_model
from claim_pilot.config import MODEL


def get_llm(temperature: float = 0):
    """One place to build the LLM so every agent uses the same model."""
    return init_chat_model(MODEL, temperature=temperature)