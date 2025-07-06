from __future__ import annotations

from yookassa import Configuration, Payment
from typing import Iterable
from datetime import datetime

from database import get_connection

from env import PAYMENT_TOKEN, SHOP_ID

Configuration.account_id = SHOP_ID
Configuration.secret_key = PAYMENT_TOKEN


def log_payment(payment_id: str, user_id: int, amount: float, status: str) -> None:
    """Create or update a payment record with the latest status."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM payments WHERE payment_id=?",
            (payment_id,),
        )
        row = cur.fetchone()
        ts = datetime.now().strftime("%m-%d-%y %H-%M")
        if row is None:
            cur.execute(
                "INSERT INTO payments(payment_id, user_id, amount, status, timestamp) VALUES(?, ?, ?, ?, ?)",
                (payment_id, user_id, amount, status, ts),
            )
        else:
            if row[0] == status:
                return
            cur.execute(
                "UPDATE payments SET status=?, timestamp=? WHERE payment_id=?",
                (status, ts, payment_id),
            )
        conn.commit()
    finally:
        conn.close()


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
    log_payment(payment.id, user_id, amount, payment.status)
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
