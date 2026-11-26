import re
import chromadb
from chromadb.utils import embedding_functions
from claim_pilot.config import CHROMA_DIR, DATA_DIR

COLLECTION = "policy_clauses"


def _collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.DefaultEmbeddingFunction()  # local MiniLM, no API key
    return client.get_or_create_collection(COLLECTION, embedding_function=ef)


def split_clauses(text: str) -> list[tuple[str, str]]:
    """Split a policy doc into (clause_id, clause_text) on '### ' headings."""
    parts = re.split(r"^### ", text, flags=re.MULTILINE)[1:]
    clauses = []
    for part in parts:
        header, _, body = part.partition("\n")
        clause_id = header.split()[0]          # "A2 Comprehensive" -> "A2"
        clauses.append((clause_id, f"{header.strip()}: {body.strip()}"))
    return clauses


def ingest_policies() -> int:
    col = _collection()
    count = 0
    for path in (DATA_DIR / "policies").glob("*.md"):
        product = path.stem                      # auto_standard / home_standard
        for clause_id, text in split_clauses(path.read_text(encoding="utf-8")):
            col.upsert(
                ids=[f"{product}:{clause_id}"],
                documents=[text],
                metadatas=[{"product": product, "clause_id": clause_id}],
            )
            count += 1
    return count


def search_clauses(query: str, product: str, k: int = 5) -> list[dict]:
    res = _collection().query(query_texts=[query], n_results=k, where={"product": product})
    return [
        {"clause_id": m["clause_id"], "text": d}
        for m, d in zip(res["metadatas"][0], res["documents"][0])
    ]