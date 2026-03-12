"""
Project MUSUBI — cogs/leaderboard.py
/callboard — top 7 servers by XP for the current 30-day cycle.
XP is awarded per relayed message during active calls.
Supabase cron snapshots + wipes XP monthly.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from datamanager import DataManager
from botprotocol import MusubiBot
from embeds import Embeds

log = logging.getLogger("musubi.leaderboard")


def _resolve_guild_info(
    bot: MusubiBot, guild_id: str
) -> tuple[str, str | None]:
    """
    Resolve (name, icon_url) for a guild_id.
    Falls back to a truncated ID if the bot isn't in that guild.
    """
    guild = bot.get_guild(int(guild_id))
    if guild:
        icon = str(guild.icon.url) if guild.icon else None
        return guild.name, icon
    return f"Server …{guild_id[-4:]}", None


class Leaderboard(commands.Cog):

    def __init__(self, bot: MusubiBot) -> None:
        self.bot  = bot
        self.data: DataManager = bot.data

    # ── /callboard ───────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="callboard",
        aliases=["cb", "lb"],
        description="View the monthly call activity leaderboard.",
    )
    async def callboard(self, ctx: commands.Context[MusubiBot]) -> None:
        """Show the current cycle's top 7 servers by XP."""
        rows = await self.data.get_leaderboard(limit=7)
        if not rows:
            await ctx.send(
                embed=Embeds.info("No XP earned yet this cycle. Start calling to get on the board!"),
            )
            return

        guilds      = [_resolve_guild_info(self.bot, r["guild_id"]) for r in rows]
        reset_at    = rows[0].get("xp_reset_at", "")
        cycle_start = reset_at[:10] if reset_at else "this cycle"

        await ctx.send(embed=Embeds.callboard(rows, guilds, cycle_start))
        log.info("Callboard viewed by guild:%s", ctx.guild.id if ctx.guild else "DM")


async def setup(bot: MusubiBot) -> None:
    await bot.add_cog(Leaderboard(bot))