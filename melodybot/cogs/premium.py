"""Comandos de plano/assinatura (monetizacao)."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from .. import ui
from ..bot import MelodyBot
from ..plans import PLAN_LABELS, Plan

log = logging.getLogger("melodybot.cogs.premium")


class PremiumCog(commands.Cog):
    def __init__(self, bot: MelodyBot) -> None:
        self.bot = bot

    @app_commands.command(name="plan", description="Mostra o plano atual do servidor.")
    async def plan(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        plan = await self.bot.get_plan(interaction.guild.id)
        limits = self.bot.limits_for(plan)
        is_premium = plan == Plan.PREMIUM

        queue = "♾️ ilimitada" if limits.queue_limit == 0 else f"{limits.queue_limit} faixas"
        track_len = (
            "♾️ sem limite"
            if limits.max_track_seconds == 0
            else f"{limits.max_track_seconds // 60} min"
        )

        guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
        emb = ui.base_embed(ui.GOLD if is_premium else ui.ACCENT)
        emb.set_author(name=f"Plano do servidor · {PLAN_LABELS[plan]}", icon_url=guild_icon)
        emb.title = "✨ Premium ativo" if is_premium else "📦 Plano Free"
        emb.add_field(name="🎶 Fila", value=queue, inline=True)
        emb.add_field(name="⏱️ Duração/faixa", value=track_len, inline=True)
        emb.add_field(
            name="🎛️ Filtros de áudio",
            value="✅ liberado" if limits.audio_filters else "🔒 bloqueado",
            inline=True,
        )
        emb.add_field(
            name="💾 Playlists salvas",
            value="✅ liberado" if limits.saved_playlists else "🔒 bloqueado",
            inline=True,
        )
        emb.add_field(
            name="⚡ Suporte",
            value="prioritário" if limits.priority_support else "padrão",
            inline=True,
        )
        emb.add_field(name="\u200b", value="\u200b", inline=True)
        if not is_premium:
            emb.set_footer(text="Use /premium para desbloquear tudo · " + ui.FOOTER_TEXT)
        await interaction.response.send_message(embed=emb)

    @app_commands.command(name="premium", description="Assine o Premium e libere tudo.")
    async def premium(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return await interaction.response.send_message("Use em um servidor.", ephemeral=True)

        price = self.bot.settings.premium_price_brl
        emb = ui.base_embed(ui.GOLD)
        emb.set_author(name="MelodyBot Premium")
        emb.title = "✨ Desbloqueie tudo"
        emb.description = (
            "Leve o MelodyBot ao máximo no seu servidor:\n\n"
            "🎶 Fila **ilimitada**\n"
            "⏱️ Faixas **sem limite** de duração\n"
            "🎛️ **Filtros de áudio** (bass boost, nightcore)\n"
            "💾 **Playlists salvas**\n"
            "⚡ **Suporte prioritário**"
        )
        emb.add_field(name="💵 Preço", value=f"**R$ {price:.2f}** / mês", inline=True)
        emb.add_field(name="⏳ Duração", value="30 dias", inline=True)

        if not self.bot.payments.enabled:
            emb.set_footer(text="Pagamentos ainda não configurados neste bot. · " + ui.FOOTER_TEXT)
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
                embed=ui.simple(
                    "❌ Não consegui gerar o pagamento",
                    "Tente novamente mais tarde.",
                    color=ui.ERROR,
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
