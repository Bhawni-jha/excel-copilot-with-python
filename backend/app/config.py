import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MOCK_LLM = os.getenv("MOCK_LLM", "0") == "1"
MODEL = "gpt-4o-mini"
MAX_FILE_MB = 10
MAX_ROWS = 10000
EXEC_TIMEOUT_SEC = 10
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
