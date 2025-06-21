import sqlite3

import openai

from config import MODEL_NAME
from database import get_connection
from env import OPENAI_API_KEY, OPENAI_BASE_URL

client = openai.Client(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)


def make_summary(session_id: int) -> str:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content FROM messages WHERE session_id=? ORDER BY id",
            (session_id,),
        )
        rows = cursor.fetchall()
        full_text = "\n".join(row[0] for row in rows)
    except sqlite3.Error:
        conn.close()
        return ""
    conn.close()
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "Сделай краткий конспект (3-5 предложений)",
                },
                {"role": "user", "content": full_text},
            ],
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except openai.OpenAIError:
        return ""
