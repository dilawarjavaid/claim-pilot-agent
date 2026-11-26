import os
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("MODEL", "groq:openai/gpt-oss-120b")