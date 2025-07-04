from __future__ import annotations

from yookassa import Configuration, Payment
from typing import Iterable

from database import get_connection

from env import PAYMENT_TOKEN, SHOP_ID

Configuration.account_id = SHOP_ID
Configuration.secret_key = PAYMENT_TOKEN


def create_payment(user_id: int, amount: float) -> Payment:
    """Create payment and return the Payment object."""
    payment = Payment.create(
        {
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me"},
            "capture": True,
            "description": f"User {user_id} recharge",
        }
    )
    print(
        f"Created payment {payment.id} for user {user_id} "
        f"on amount {amount:.2f}"
    )
    return payment


def payment_status(payment_id: str) -> str:
    """Return payment status."""
    payment = Payment.find_one(payment_id)
    print(f"Payment {payment_id} status: {payment.status}")
    return payment.status


def add_pending(payment_id: str, user_id: int, amount: float, credits: float) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO pending_payments(payment_id, user_id, amount, credits) VALUES(?, ?, ?, ?)",
            (payment_id, user_id, amount, credits),
        )
        conn.commit()
        print(
            f"Pending payment {payment_id} registered for user {user_id} "
            f"amount {amount:.2f} credits {credits:.0f}"
        )
    finally:
        conn.close()


def list_pending() -> Iterable[tuple[str, int, float, float]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT payment_id, user_id, amount, credits FROM pending_payments")
        return cur.fetchall()
    finally:
        conn.close()


def remove_pending(payment_id: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM pending_payments WHERE payment_id=?", (payment_id,))
        conn.commit()
        print(f"Pending payment {payment_id} removed")
    finally:
        conn.close()
