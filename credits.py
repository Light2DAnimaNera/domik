from __future__ import annotations

import sqlite3
import time
from datetime import datetime, date

from database import get_connection


class InsufficientCreditsError(Exception):
    pass


_cache: dict[str, tuple[float, float]] = {}

# Token prices per 1 unit (before applying coefficient)
# Cost of a request token
REQUEST_TOKEN_PRICE = 0.0020
# Cost of a response token
RESPONSE_TOKEN_PRICE = 0.0005

def _get_setting(key: str) -> str:
    now = time.time()
    if key in _cache:
        value, ts = _cache[key]
        if now - ts < 60:
            return value
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cursor.fetchone()
        if row:
            value = row[0]
            _cache[key] = (float(value), now)
            return value
        return "0"
    finally:
        conn.close()

def _set_setting(key: str, value: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()
        _cache[key] = (float(value), time.time())
    finally:
        conn.close()

def get_token_coeff() -> float:
    return float(_get_setting("token_cost_coeff"))


def set_token_coeff(val: float) -> None:
    if val <= 0:
        raise ValueError("Coefficient must be positive")
    _set_setting("token_cost_coeff", str(val))


def add_credits(user_id: int, amount: float, source: str) -> None:
    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO recharge(user_id, amount, source, timestamp) VALUES(?, ?, ?, ?)",
            (user_id, amount, source, now),
        )
        conn.execute(
            "UPDATE users SET credits = credits + ?, updated_at=? WHERE telegram_id=?",
            (amount, now, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def _update_daily_usage(conn: sqlite3.Connection, user_id: int, cost: float) -> None:
    today = date.today().isoformat()
    conn.execute(
        "INSERT INTO usage_daily(user_id, date, spent) VALUES(?, ?, ?) "
        "ON CONFLICT(user_id, date) DO UPDATE SET spent = spent + excluded.spent",
        (user_id, today, cost),
    )


def charge_user(user_id: int, prompt_tokens: int, completion_tokens: int) -> None:
    """Charge user for used tokens and log separate values."""
    coeff = get_token_coeff()
    cost_per_prompt = REQUEST_TOKEN_PRICE * prompt_tokens
    cost_per_completion = RESPONSE_TOKEN_PRICE * completion_tokens
    cost = (cost_per_prompt + cost_per_completion) * coeff
    total_tokens = prompt_tokens + completion_tokens
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM users WHERE telegram_id=?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            raise InsufficientCreditsError()
        balance = float(row[0])
        new_balance = balance - cost
        if new_balance < 0:
            raise InsufficientCreditsError()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE users SET credits=?, updated_at=? WHERE telegram_id=?",
            (new_balance, now, user_id),
        )
        _update_daily_usage(conn, user_id, cost)
        conn.commit()
    except InsufficientCreditsError:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(
        f"User {user_id} spent {prompt_tokens} prompt and {completion_tokens} "
        f"completion tokens ({total_tokens} total, {cost:.4f} \u20A1). "
        f"New balance: {new_balance:.4f} \u20A1"
    )


def get_balance(user_id: int) -> float:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM users WHERE telegram_id=?", (user_id,))
        row = cursor.fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()


def get_today_spent(user_id: int) -> float:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT spent FROM usage_daily WHERE user_id=? AND date=?",
            (user_id, date.today().isoformat()),
        )
        row = cursor.fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()
