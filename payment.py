class PaymentProvider:
    """Abstract payment provider."""
    def create_payment(self, user_id: int, amount: float) -> str:
        raise NotImplementedError


_provider: PaymentProvider | None = None


def register_payment_provider(provider: PaymentProvider) -> None:
    """Register concrete payment provider."""
    global _provider
    _provider = provider


def create_payment_link(user_id: int, amount: float) -> str:
    """Return payment link using registered provider."""
    if _provider is None:
        raise RuntimeError("Payment provider not configured")
    return _provider.create_payment(user_id, amount)
