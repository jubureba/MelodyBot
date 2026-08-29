"""Comandos de plano/assinatura (monetizacao)."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ..bot import MelodyBot
from ..plans import PLAN_LABELS, Plan

log = logging.getLogger("melodybot.cogs.premium")

ACCENT = 0x22D3EE
GOLD = 0xFACC15


class PremiumCog(commands.Cog):
    def __init__(self, bot: MelodyBot) -> None:
        self.bot = bot

    @app_commands.command(name="plan", description="Mostra o plano atual do servidor.")
    async def plan(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        plan = await self.bot.get_plan(interaction.guild.id)
        limits = self.bot.limits_for(plan)

        queue = "ilimitada" if limits.queue_limit == 0 else f"{limits.queue_limit} faixas"
        track_len = (
            "sem limite"
            if limits.max_track_seconds == 0
            else f"{limits.max_track_seconds // 60} min"
        )
        emb = discord.Embed(
            title=f"📦 Plano: {PLAN_LABELS[plan]}",
            color=GOLD if plan == Plan.PREMIUM else ACCENT,
        )
        emb.add_field(name="Fila", value=queue, inline=True)
        emb.add_field(name="Duracao/faixa", value=track_len, inline=True)
        emb.add_field(
            name="Filtros de audio",
            value="✅" if limits.audio_filters else "❌",
            inline=True,
        )
        if plan == Plan.FREE:
            emb.set_footer(text="Use /premium para desbloquear tudo.")
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="premium", description="Assine o Premium e libere tudo.")
    async def premium(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        price = self.bot.settings.premium_price_brl
        emb = discord.Embed(
            title="✨ MelodyBot Premium",
            description=(
                "Libere o melhor do MelodyBot pro seu servidor:\n\n"
                "🎶 Fila **ilimitada**\n"
                "⏱️ Faixas **sem limite** de duracao\n"
                "🎛️ **Filtros de audio** (bass boost, nightcore)\n"
                "💾 **Playlists salvas**\n"
                "⚡ Suporte prioritario\n\n"
                f"**R$ {price:.2f}/mes**"
            ),
            color=GOLD,
        )

        if not self.bot.payments.enabled:
            emb.set_footer(text="Pagamentos ainda nao configurados neste bot.")
            return await interaction.response.send_message(embed=emb, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            checkout = await self.bot.payments.create_checkout(
                guild_id=interaction.guild.id,
                amount=price,
                description="MelodyBot Premium (mensal)",
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("Falha ao criar checkout: %s", exc)
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Nao consegui gerar o pagamento",
                    description="Tente novamente mais tarde.",
                    color=0xEF4444,
                ),
                ephemeral=True,
            )

        await self.bot.db.record_payment(
            guild_id=interaction.guild.id,
            provider=self.bot.payments.name,
            external_id=checkout.external_id,
            status="pending",
            amount=price,
        )

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(label="Pagar agora", url=checkout.url, style=discord.ButtonStyle.link)
        )
        await interaction.followup.send(embed=emb, view=view, ephemeral=True)


async def setup(bot: MelodyBot) -> None:
    await bot.add_cog(PremiumCog(bot))
