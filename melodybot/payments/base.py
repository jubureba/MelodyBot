"""Interface de provider de pagamento (plugavel)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CheckoutResult:
    """Resultado da criacao de uma cobranca."""

    url: str
    external_id: str


@dataclass
class WebhookEvent:
    """Evento de pagamento normalizado, vindo do webhook do provedor."""

    external_id: str
    status: str  # "approved", "pending", "rejected", ...
    guild_id: int | None
    amount: float | None


class PaymentProvider(ABC):
    """Contrato que todo gateway de pagamento deve implementar."""

    name: str = "base"

    @property
    def enabled(self) -> bool:
        return True

    @abstractmethod
    async def create_checkout(
        self, guild_id: int, amount: float, description: str
    ) -> CheckoutResult:
        """Cria uma cobranca e retorna a URL de pagamento."""

    @abstractmethod
    async def parse_webhook(self, payload: dict, query: dict) -> WebhookEvent | None:
        """Interpreta o payload do webhook em um evento normalizado."""
