from __future__ import annotations

from yookassa import Configuration, Payment

from env import PAYMENT_TOKEN

Configuration.access_token = PAYMENT_TOKEN


def create_payment_link(user_id: int, amount: float) -> str:
    """Create payment and return confirmation URL."""
    payment = Payment.create(
        {
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me"},
            "capture": True,
            "description": f"User {user_id} recharge",
        }
    )
    return payment.confirmation.confirmation_url
