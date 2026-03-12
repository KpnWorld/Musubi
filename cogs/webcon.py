"""
Project MUSUBI — cogs/webcon.py
Pushes callboard + basic network counts to the KpnWorld website every 60s.
Read-only — the website cannot control the bot.

POST {WEBSITE_URL}/api/musubi/stats
  Auth: X-API-Secret: <API_SECRET>

Payload:
  {
    "active_calls":      int,
    "registered_guilds": int,
    "total_users":       int,
    "callboard": [
      { "rank": int, "guild_name": str, "xp": int,
        "icon_url": str|null, "cycle_started": str }
    ]
  }

Env vars:
  WEBSITE_URL  — base URL, no trailing slash
  API_SECRET   — shared secret header value
"""

from __future__ import annotations

import asyncio
import logging
import os

import aiohttp
from discord.ext import commands, tasks

from botprotocol import MusubiBot
from datamanager import DataManager

log = logging.getLogger("musubi.web")

STATS_INTERVAL = 60  # seconds between pushes
HTTP_TIMEOUT   = aiohttp.ClientTimeout(total=8)


def _base_url() -> str:
    return os.environ.get("WEBSITE_URL", "").rstrip("/")


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "X-API-Secret": os.environ.get("API_SECRET", ""),
    }


class WebConnector(commands.Cog, name="WebConnector"):

    def __init__(self, bot: MusubiBot) -> None:
        self.bot  = bot
        self.data: DataManager = bot.data
        self.stats_push.start()

    async def cog_unload(self) -> None:
        self.stats_push.cancel()

    def _ready(self) -> bool:
        return bool(_base_url() and os.environ.get("API_SECRET"))

    async def _post(self, payload: dict) -> bool:
        if not self._ready():
            return False
        url = f"{_base_url()}/api/musubi/stats"
        try:
            async with self.bot.session.post(
                url, json=payload, headers=_headers(), timeout=HTTP_TIMEOUT,
            ) as r:
                if r.status == 200:
                    return True
                log.warning("POST /api/musubi/stats → %d", r.status)
        except asyncio.TimeoutError:
            log.warning("POST /api/musubi/stats timed out")
        except Exception as e:
            log.warning("POST /api/musubi/stats failed: %s", e)
        return False

    async def _build_stats(self) -> dict:
        active_calls    = await self.data.count_active_calls()
        leaderboard_rows = await self.data.get_leaderboard(limit=7)

        callboard = []
        for i, row in enumerate(leaderboard_rows):
            guild = self.bot.get_guild(int(row["guild_id"]))
            callboard.append({
                "rank":          i + 1,
                "guild_name":    guild.name if guild else f"Server …{row['guild_id'][-4:]}",
                "xp":            row.get("xp") or 0,
                "icon_url":      str(guild.icon.url) if guild and guild.icon else None,
                "cycle_started": (row.get("xp_reset_at") or "")[:10],
            })

        return {
            "active_calls":      active_calls,
            "registered_guilds": len(self.data.guilds),
            "total_users":       len(self.data.users),
            "callboard":         callboard,
        }

    @tasks.loop(seconds=STATS_INTERVAL)
    async def stats_push(self) -> None:
        try:
            payload = await self._build_stats()
            ok      = await self._post(payload)
            if ok:
                log.debug(
                    "Stats pushed — active_calls:%d guilds:%d callboard:%d",
                    payload["active_calls"],
                    payload["registered_guilds"],
                    len(payload["callboard"]),
                )
        except Exception as e:
            log.warning("stats_push error: %s", e)

    @stats_push.before_loop
    async def before_stats_push(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: MusubiBot) -> None:
    if not os.environ.get("WEBSITE_URL"):
        log.warning("WEBSITE_URL not set — WebConnector loaded but inactive.")
    await bot.add_cog(WebConnector(bot))