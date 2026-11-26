import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from claim_pilot.rag import ingest_policies

print(f"Ingested {ingest_policies()} clauses")