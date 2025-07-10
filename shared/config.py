from pathlib import Path
import os

MODEL_NAME = "gpt-4.1-mini"
CONTEXT_LIMIT = 15000

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "users.db"))
DSS_DB_PATH = os.getenv("DSS_DB_PATH", str(BASE_DIR / "dss_topics.db"))
INITIAL_CREDITS = 100
CURRENCY_SYMBOL = "\U0001F763"
