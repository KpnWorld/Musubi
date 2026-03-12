"""
Project MUSUBI — cogs/bridge.py
Message relay between connected guilds.

Supabase call budget per message (free tier protection):
  - Premium checks: cached per session on first message, zero DB hits after
  - bump_activity:  debounced — one write per ACTIVITY_DEBOUNCE_SECS per session
  - add_xp:         batched — flushed every XP_FLUSH_EVERY messages or on hangup
  - get_active_session: one call per message (unavoidable, tombstone fast-paths it)
"""

from __future__ import annotations

import logging
import time
from typing import Optional, cast

import discord
from discord.ext import commands

from datamanager import DataManager, XP_PER_MESSAGE, XP_PREMIUM_MULTIPLIER
from embeds import Embeds
from botprotocol import MusubiBot

log = logging.getLogger("musubi.bridge")

RELAY_MAP_LIMIT        = 500
ACTIVITY_DEBOUNCE_SECS = 30   # minimum seconds between bump_activity DB writes per session
XP_FLUSH_EVERY         = 5    # flush accumulated XP to DB every N messages per guild


class Bridge(commands.Cog):

    def __init__(self, bot: MusubiBot) -> None:
        self.bot = bot
        self.data: DataManager = bot.data

        # orig_msg_id → (relayed_webhook_msg_id, target_channel_id)
        self.relay_map: dict[int, tuple[int, int]] = {}

        # session_id → last bump_activity wall-clock time
        self._last_bump: dict[str, float] = {}

        # guild_id → pending XP not yet flushed to DB
        self._xp_pending: dict[str, int] = {}

        # guild_id → message count since last XP flush
        self._msg_count: dict[str, int] = {}

        # session_id → (is_premium_user_caller, is_premium_guild) cached on first relay
        self._premium_cache: dict[str, tuple[bool, bool]] = {}

    # ── Public flush (called by phone.py on hangup/idle end) ─────────────

    async def flush_xp(self, guild_id: str) -> None:
        """Flush any pending XP for a guild immediately — call on session end."""
        pending = self._xp_pending.pop(str(guild_id), 0)
        self._msg_count.pop(str(guild_id), None)
        if pending > 0:
            try:
                await self.data.add_xp_bulk(guild_id, pending)
            except Exception as e:
                log.error("flush_xp failed for %s: %s", guild_id, e)

    def clear_session_cache(self, session_id: str) -> None:
        """Clear per-session caches — call on session end."""
        self._last_bump.pop(session_id, None)
        self._premium_cache.pop(session_id, None)

    # ── Webhook ───────────────────────────────────────────────────────────

    async def _get_webhook(self, channel: discord.TextChannel, guild_id: str) -> Optional[discord.Webhook]:
        cached = self.data.webhook_cache.get(guild_id)
        if cached:
            return cached

        g = self.data.get_guild(guild_id)
        if g and g.get("webhook"):
            try:
                wh = discord.Webhook.from_url(g["webhook"], session=self.bot.session)
                self.data.webhook_cache[guild_id] = wh
                return wh
            except Exception:
                pass

        try:
            webhooks = await channel.webhooks()
            wh       = next((w for w in webhooks if w.name == "Musubi Bridge"), None)
            if not wh:
                wh = await channel.create_webhook(name="Musubi Bridge")
            self.data.webhook_cache[guild_id] = wh
            return wh
        except discord.Forbidden:
            log.warning("Missing webhook permissions in channel %d", channel.id)
            return None

    # ── Session helpers ────────────────────────────────────────────────────

    async def _get_session_and_target(
        self, guild_id: str
    ) -> Optional[tuple[dict, str, str]]:
        """
        Returns (session, target_guild_id, target_channel_id) or None.
        Handles both sides of the single session row correctly.
        """
        session = await self.data.get_active_session(guild_id)
        if not session:
            return None

        if session["caller_guild"] == guild_id:
            target_guild_id   = session["target_guild"]
            target_channel_id = session["target_channel"]
        else:
            target_guild_id   = session["caller_guild"]
            target_channel_id = session["caller_channel"]

        if not target_guild_id or not target_channel_id:
            return None

        return session, target_guild_id, target_channel_id

    async def _get_premium(self, session_id: str, user_id: int, guild_id: str) -> tuple[bool, bool]:
        """
        Return (is_premium_user, is_premium_guild) — cached per session.
        First call hits Supabase, all subsequent calls are free.
        """
        cached = self._premium_cache.get(session_id)
        if cached is not None:
            return cached
        is_premium_user  = await self.data.is_premium_user(user_id)
        is_premium_guild = await self.data.is_premium_guild(guild_id)
        self._premium_cache[session_id] = (is_premium_user, is_premium_guild)
        return is_premium_user, is_premium_guild

    def _should_bump(self, session_id: str) -> bool:
        """True if enough time has passed to justify a bump_activity DB write."""
        last = self._last_bump.get(session_id, 0.0)
        if time.monotonic() - last >= ACTIVITY_DEBOUNCE_SECS:
            self._last_bump[session_id] = time.monotonic()
            return True
        return False

    def _accumulate_xp(self, guild_id: str, amount: int, premium_guild: bool) -> bool:
        """
        Accumulate XP in memory. Returns True when it's time to flush to DB.
        """
        actual = amount * XP_PREMIUM_MULTIPLIER if premium_guild else amount
        self._xp_pending[guild_id]  = self._xp_pending.get(guild_id, 0) + actual
        self._msg_count[guild_id]   = self._msg_count.get(guild_id, 0) + 1
        # Also update the in-memory cache immediately so leaderboard reads are fresh
        g = self.data.get_guild(guild_id)
        if g:
            g["xp"] = (g.get("xp") or 0) + actual
        return self._msg_count[guild_id] >= XP_FLUSH_EVERY

    # ── Relay ──────────────────────────────────────────────────────────────

    async def _relay(
        self,
        channel: discord.TextChannel,
        guild_id: str,
        content: str,
        username: str,
        avatar_url: Optional[str],
        files: list[discord.File],
        reply_quote:  Optional[str] = None,
        reply_author: Optional[str] = None,
    ) -> Optional[discord.WebhookMessage]:
        wh = await self._get_webhook(channel, guild_id)
        if not wh:
            return None

        try:
            if reply_quote:
                sent = await wh.send(
                    embed=Embeds.reply(username, reply_author or "?", reply_quote, content or ""),
                    username=username,
                    avatar_url=avatar_url,
                    allowed_mentions=discord.AllowedMentions.none(),
                    wait=True,
                )
                if files:
                    await wh.send(
                        content="\u200b",
                        files=files,
                        username=username,
                        avatar_url=avatar_url,
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                return sent
            else:
                return await wh.send(
                    content=content or "\u200b",
                    username=username,
                    avatar_url=avatar_url,
                    files=files,
                    allowed_mentions=discord.AllowedMentions.none(),
                    wait=True,
                )
        except discord.HTTPException as e:
            log.error("Relay failed to guild %s: %s", guild_id, e)
            return None

    # ── on_message ─────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)

        if not self.data.is_guild_registered(guild_id):
            return
        if self.data.is_guild_banned(guild_id):
            return

        g = self.data.get_guild(guild_id)
        if not g or str(message.channel.id) != g["booth_channel"]:
            return

        result = await self._get_session_and_target(guild_id)
        if not result:
            return
        session, target_guild_id, target_channel_id = result

        if session["id"] in self.data._ended_sessions:
            return

        target_channel = self.bot.get_channel(int(target_channel_id))
        if not target_channel or not isinstance(target_channel, discord.TextChannel):
            return

        # ── Filter ─────────────────────────────────────────────────────────
        _fc = self.bot.cogs.get("Filter")
        if _fc and hasattr(_fc, "should_block"):
            from cogs.filter import FilterCog as _FilterCog
            filter_cog = cast(_FilterCog, _fc)
            if filter_cog.should_block(message):
                return

        # ── Premium — cached per session, zero extra DB calls after first ──
        is_premium_user, is_premium_guild = await self._get_premium(
            session["id"], message.author.id, guild_id
        )
        is_premium = is_premium_user or is_premium_guild

        # ── Identity ────────────────────────────────────────────────────────
        bot_avatar = str(self.bot.user.display_avatar.url) if self.bot.user else None
        name, avatar = self.data.resolve_identity(
            message.author.id, message.author.display_name, bot_avatar=bot_avatar
        )
        if not avatar:
            avatar = str(message.author.display_avatar.url)

        # ── Attachments — premium only ──────────────────────────────────────
        files: list[discord.File] = []
        skipped_attachments = 0
        if is_premium and message.attachments:
            for att in message.attachments:
                try:
                    files.append(await att.to_file())
                except discord.HTTPException:
                    skipped_attachments += 1

        # ── Stickers — guild premium only ───────────────────────────────────
        sticker_text = ""
        if is_premium_guild and message.stickers:
            sticker_text = ", ".join(f"[sticker: {s.name}]" for s in message.stickers)

        content = message.content or ""
        if sticker_text:
            content = f"{content} {sticker_text}".strip()

        if not content and not files:
            return

        # ── Reply detection ─────────────────────────────────────────────────
        reply_quote:  Optional[str] = None
        reply_author: Optional[str] = None

        if message.reference and message.reference.message_id:
            ref_msg = message.reference.resolved
            if isinstance(ref_msg, discord.Message):
                ref_content = ref_msg.content or ""
                if len(ref_content) > 80:
                    ref_content = ref_content[:80] + "\u2026"
                reply_quote  = ref_content or "(attachment)"
                reply_author = ref_msg.author.display_name

        # Late tombstone check before the actual send
        if session["id"] in self.data._ended_sessions:
            return

        relayed = await self._relay(
            target_channel, target_guild_id, content, name, avatar, files,
            reply_quote=reply_quote,
            reply_author=reply_author,
        )

        if relayed:
            self.relay_map[message.id] = (relayed.id, int(target_channel_id))
            if len(self.relay_map) > RELAY_MAP_LIMIT:
                oldest = next(iter(self.relay_map))
                del self.relay_map[oldest]

        if skipped_attachments:
            try:
                await message.channel.send(
                    embed=Embeds.error(
                        f"{skipped_attachments} attachment{'s' if skipped_attachments > 1 else ''} "
                        "couldn't be sent — file too large for the other server."
                    ),
                    delete_after=8,
                )
            except discord.HTTPException:
                pass

        # ── XP — batched, flush every XP_FLUSH_EVERY messages ──────────────
        should_flush = self._accumulate_xp(guild_id, XP_PER_MESSAGE, is_premium_guild)
        if should_flush:
            pending = self._xp_pending.pop(guild_id, 0)
            self._msg_count.pop(guild_id, None)
            if pending > 0:
                await self.data.add_xp_bulk(guild_id, pending)

        # ── bump_activity — debounced, max 1 DB write per 30s per session ───
        if self._should_bump(session["id"]):
            await self.data.bump_activity(session["id"])

    # ── on_message_delete ──────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        entry = self.relay_map.pop(message.id, None)
        if not entry:
            return

        relayed_msg_id, target_channel_id = entry

        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel or not isinstance(target_channel, discord.TextChannel):
            return

        result = await self._get_session_and_target(str(message.guild.id))
        target_guild_id = result[1] if result else None
        if not target_guild_id:
            return

        wh = await self._get_webhook(target_channel, target_guild_id)
        if not wh:
            return

        try:
            await wh.delete_message(relayed_msg_id)
            log.info("Delete relayed — orig:%d relayed:%d", message.id, relayed_msg_id)
        except discord.NotFound:
            pass
        except discord.HTTPException as e:
            log.error("Delete relay failed: %s", e)


async def setup(bot: MusubiBot) -> None:
    await bot.add_cog(Bridge(bot))