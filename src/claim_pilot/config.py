import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
CHROMA_DIR = ROOT / "chroma_db"

MODEL = os.getenv("MODEL", "groq:openai/gpt-oss-120b")