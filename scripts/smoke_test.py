import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from claim_pilot.llm import get_llm

llm = get_llm()
reply = llm.invoke("In one sentence, what does an insurance claims adjuster do?")
print(reply.content)