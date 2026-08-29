"""Provider nulo: usado quando pagamentos estao desabilitados."""

from __future__ import annotations

from .base import CheckoutResult, PaymentProvider, WebhookEvent


class NoopPaymentProvider(PaymentProvider):
    name = "none"

    @property
    def enabled(self) -> bool:
        return False

    async def create_checkout(
        self, guild_id: int, amount: float, description: str
    ) -> CheckoutResult:
        raise RuntimeError("Pagamentos desabilitados. Configure PAYMENT_PROVIDER.")

    async def parse_webhook(self, payload: dict, query: dict) -> WebhookEvent | None:
        return None
