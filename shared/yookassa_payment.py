from __future__ import annotations

from yookassa import Configuration, Payment
from typing import Iterable, Optional
import uuid
from datetime import datetime
import logging

from .database import get_connection

from .env import PAYMENT_TOKEN, SHOP_ID

Configuration.account_id = SHOP_ID
Configuration.secret_key = PAYMENT_TOKEN


def log_payment(
    payment_id: str,
    user_id: int,
    amount: float,
    status: str,
    credits: Optional[float] = None,
) -> None:
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
                "INSERT INTO payments(payment_id, user_id, amount, credits, status, timestamp) VALUES(?, ?, ?, ?, ?, ?)",
                (payment_id, user_id, amount, credits or 0, status, ts),
            )
        else:
            if row[0] == status and credits is None:
                return
            if credits is None:
                cur.execute(
                    "UPDATE payments SET status=?, timestamp=? WHERE payment_id=?",
                    (status, ts, payment_id),
                )
            else:
                cur.execute(
                    "UPDATE payments SET status=?, credits=?, timestamp=? WHERE payment_id=?",
                    (status, credits, ts, payment_id),
                )
        conn.commit()
    finally:
        conn.close()


def create_payment(
    user_id: int,
    amount: float,
    user_email: str,
    credits: Optional[float] = None,
) -> Payment:
    """Create payment and return the Payment object."""
    idempotence_key = str(uuid.uuid4())
    payment = Payment.create(
        {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/DominaSupremaBot",
            },
            "capture": True,
            "description": "Пополнение баланса DominaSupremaBot",
            "receipt": {
                "customer": {"email": user_email},
                "items": [
                    {
                        "description": "Пополнение баланса DominaSupremaBot",
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": "RUB",
                        },
                        "vat_code": 1,
                        "payment_mode": "full_prepayment",
                        "payment_subject": "service",
                    }
                ],
            },
        },
        idempotence_key,
    )
    logging.info(
        "Created payment %s for user %s on amount %.2f",
        payment.id,
        user_id,
        amount,
    )
    log_payment(payment.id, user_id, amount, payment.status, credits)
    return payment


def payment_status(payment_id: str) -> str:
    """Return payment status."""
    payment = Payment.find_one(payment_id)
    logging.info("Payment %s status: %s", payment_id, payment.status)
    return payment.status


def add_pending(payment_id: str, user_id: int, amount: float, credits: float) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO pending_payments(payment_id, user_id, amount, credits) VALUES(?, ?, ?, ?)",
            (payment_id, user_id, amount, credits),
        )
        conn.commit()
        logging.info(
            "Pending payment %s registered for user %s amount %.2f credits %.0f",
            payment_id,
            user_id,
            amount,
            credits,
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
        logging.info("Pending payment %s removed", payment_id)
    finally:
        conn.close()
