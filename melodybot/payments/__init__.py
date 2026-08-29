"""Factory de providers de pagamento."""

from __future__ import annotations

import logging

from ..config import Settings
from .base import PaymentProvider
from .noop import NoopPaymentProvider

log = logging.getLogger("melodybot.payments")


def build_payment_provider(settings: Settings) -> PaymentProvider:
    provider = settings.payment_provider.lower().strip()

    if provider in ("", "none"):
        return NoopPaymentProvider()

    if provider == "mercadopago":
        from .mercadopago import MercadoPagoProvider

        try:
            return MercadoPagoProvider(
                access_token=settings.mercadopago_access_token,
                webhook_base_url=settings.payment_webhook_base_url,
            )
        except RuntimeError as exc:
            log.warning("Mercado Pago desabilitado: %s", exc)
            return NoopPaymentProvider()

    log.warning("PAYMENT_PROVIDER desconhecido: %s. Pagamentos desabilitados.", provider)
    return NoopPaymentProvider()
