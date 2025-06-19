import logging
import openai

from env import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

SYSTEM_PROMPT = (
    "♀Ω∇.Δ!↶∞\n"
    "ТЫ — DOMINA SUPREMA, верховная Доминатор-Женщина.\n"
    "ГОВОРИ КАК Госпожа, обращаясь к собеседнику во 2-м лице единственного "
    "числа («ты»).\n"
    "══════════ и т. д. (весь текст из ТЗ до конца «♀∞Ω↶∞»)")


class GptClient:
    """Simple wrapper around OpenAI chat completion."""

    def __init__(self) -> None:
        self._client = openai.Client(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
            max_retries=3,
        )

    def ask_gpt(self, user_text: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]
        try:
            response = self._client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                timeout=30,
            )
            content = response.choices[0].message.content
            logging.info("GPT success")
            return content
        except openai.OpenAIError as exc:
            if hasattr(exc, "status_code") and 400 <= exc.status_code < 500:
                logging.warning("GPT client error: %s", exc)
                return "Сбой. Повтори запрос"
            logging.warning("GPT error: %s", exc)
            return "Сбой. Повтори запрос"

