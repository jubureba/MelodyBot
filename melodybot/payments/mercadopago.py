"""Provider Mercado Pago (Checkout Pro / Pix).

O SDK 'mercadopago' e importado de forma lazy para nao ser dependencia
obrigatoria de quem roda o bot sem pagamentos.
"""

from __future__ import annotations

import asyncio
import logging

from .base import CheckoutResult, PaymentProvider, WebhookEvent

log = logging.getLogger("melodybot.payments.mercadopago")


class MercadoPagoProvider(PaymentProvider):
    name = "mercadopago"

    def __init__(self, access_token: str, webhook_base_url: str) -> None:
        if not access_token:
            raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN nao configurado.")
        try:
            import mercadopago  # noqa: PLC0415 - import lazy proposital
        except ImportError as exc:
            raise RuntimeError(
                "Pacote 'mercadopago' nao instalado. Rode: pip install mercadopago"
            ) from exc
        self._sdk = mercadopago.SDK(access_token)
        self._webhook_base = webhook_base_url.rstrip("/")

    async def create_checkout(
        self, guild_id: int, amount: float, description: str
    ) -> CheckoutResult:
        notification_url = (
            f"{self._webhook_base}/webhook/mercadopago" if self._webhook_base else None
        )
        preference = {
            "items": [
                {
                    "title": description,
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": float(amount),
                }
            ],
            # external_reference liga o pagamento ao servidor Discord.
            "external_reference": str(guild_id),
            "metadata": {"guild_id": guild_id},
        }
        if notification_url:
            preference["notification_url"] = notification_url

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: self._sdk.preference().create(preference)
        )
        response = result.get("response", {})
        init_point = response.get("init_point") or response.get("sandbox_init_point")
        pref_id = response.get("id", "")
        if not init_point:
            raise RuntimeError(f"Falha ao criar preferencia: {result}")
        return CheckoutResult(url=init_point, external_id=str(pref_id))

    async def parse_webhook(self, payload: dict, query: dict) -> WebhookEvent | None:
        # Mercado Pago envia notificacoes de "payment". Buscamos o pagamento
        # pelo id para descobrir status e external_reference (guild_id).
        payment_id = None
        if query.get("type") == "payment" and query.get("data.id"):
            payment_id = query["data.id"]
        elif isinstance(payload.get("data"), dict):
            payment_id = payload["data"].get("id")

        if not payment_id:
            return None

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: self._sdk.payment().get(payment_id)
        )
        response = result.get("response", {})
        status = response.get("status", "unknown")
        external_ref = response.get("external_reference")
        amount = response.get("transaction_amount")
        guild_id = int(external_ref) if external_ref and external_ref.isdigit() else None

        return WebhookEvent(
            external_id=str(payment_id),
            status=status,
            guild_id=guild_id,
            amount=amount,
        )
