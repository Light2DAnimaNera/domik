import os

try:  # python-dotenv might be missing during tests
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = lambda: None

load_dotenv()

TELEGRAM_TOKEN_BOT1 = os.getenv("TELEGRAM_TOKEN_BOT1")
TELEGRAM_TOKEN_BOT2 = os.getenv("TELEGRAM_TOKEN_BOT2")
TELEGRAM_TOKEN_BOT3 = os.getenv("TELEGRAM_TOKEN_BOT3")

# Backward compatibility with single-bot setup
TELEGRAM_TOKEN = TELEGRAM_TOKEN_BOT1
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
SHOP_ID = os.getenv("SHOP_ID")
DSA_REPORT_CHAT_ID = os.getenv("DSA_REPORT_CHAT_ID")
