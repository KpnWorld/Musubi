"""
Project MUSUBI — cogs/premium.py
User and guild premium management.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from discord.ext import commands

from datamanager import DataManager
from botprotocol import MusubiBot
from embeds import Embeds

log = logging.getLogger("musubi.premium")

# Basic URL validation for avatar — must be http/https and end with an image extension
_AVATAR_URL_RE = re.compile(
    r"^https?://.+\.(png|jpg|jpeg|gif|webp)(\?.*)?$",
    re.IGNORECASE,
)


class Premium(commands.Cog):

    def __init__(self, bot: MusubiBot) -> None:
        self.bot  = bot
        self.data: DataManager = bot.data

    # ── /me ──────────────────────────────────────────────────────────────

    @commands.hybrid_group(name="me", description="Manage your personal Musubi settings.")
    async def me(self, ctx: commands.Context[MusubiBot]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send(
                embed=Embeds.info("Available subcommands: `status`, `name`, `avatar`, `reset`"),
                ephemeral=True,
            )

    @me.command(name="status", description="View your premium status and personal settings.")
    async def me_status(self, ctx: commands.Context[MusubiBot]) -> None:
        """View your current premium status and personal profile settings."""
        u          = self.data.get_user(ctx.author.id)
        is_premium = await self.data.is_premium_user(ctx.author.id)

        anon     = "`Yes`" if u.get("is_anonymous") else "`No`"
        nickname = f"`{u['nickname']}`" if u.get("nickname") else "`—`"
        avatar   = "`Custom`" if u.get("avatar") else "`Default`"
        premium  = "`✅ Active`" if is_premium else "`❌ None`"

        await ctx.send(
            embed=Embeds.me_status(
                author=str(ctx.author),
                icon_url=str(ctx.author.display_avatar.url),
                premium=premium,
                anon=anon,
                nickname=nickname,
                avatar=avatar,
            ),
            ephemeral=True,
        )

    @me.command(name="name", description="Set your display name during calls. (User premium required)")
    async def me_name(
        self,
        ctx: commands.Context[MusubiBot],
        nickname: str,
    ) -> None:
        """
        Set a custom display name shown on your relayed messages.
        Requires user premium.

        Parameters
        ----------
        nickname: str
            Your display name — max 32 characters.
        """
        if not await self.data.is_premium_user(ctx.author.id):
            await ctx.send(
                embed=Embeds.error(
                    "Custom nicknames require **User Premium**.\n"
                    "Use `/redeem` if you have a key, or contact a network admin."
                ),
                ephemeral=True,
            )
            return
        if len(nickname) > 32:
            await ctx.send(
                embed=Embeds.error("Nickname must be 32 characters or fewer."),
                ephemeral=True,
            )
            return
        u = self.data.get_user(ctx.author.id)
        u["nickname"] = nickname
        await self.data.upsert_user(ctx.author.id)
        await ctx.send(
            embed=Embeds.action(f"Display name set to `{nickname}`.", ctx.author),
            ephemeral=True,
        )

    @me.command(name="avatar", description="Set a custom avatar for calls. (User premium required)")
    async def me_avatar(
        self,
        ctx: commands.Context[MusubiBot],
        url: str,
    ) -> None:
        """
        Set a custom avatar URL shown on your relayed messages.
        Must be a direct image link (png, jpg, jpeg, gif, or webp).
        Requires user premium.

        Parameters
        ----------
        url: str
            A direct image URL ending in .png, .jpg, .jpeg, .gif, or .webp.
        """
        if not await self.data.is_premium_user(ctx.author.id):
            await ctx.send(
                embed=Embeds.error(
                    "Custom avatars require **User Premium**.\n"
                    "Use `/redeem` if you have a key, or contact a network admin."
                ),
                ephemeral=True,
            )
            return
        if not _AVATAR_URL_RE.match(url):
            await ctx.send(
                embed=Embeds.error(
                    "Invalid URL. Please provide a direct image link ending in "
                    "`.png`, `.jpg`, `.jpeg`, `.gif`, or `.webp`."
                ),
                ephemeral=True,
            )
            return
        u = self.data.get_user(ctx.author.id)
        u["avatar"] = url
        await self.data.upsert_user(ctx.author.id)
        await ctx.send(
            embed=Embeds.action("Custom avatar set successfully.", ctx.author),
            ephemeral=True,
        )

    @me.command(name="reset", description="Reset your display name and avatar back to Discord defaults.")
    async def me_reset(self, ctx: commands.Context[MusubiBot]) -> None:
        """Clear your custom display name and avatar, reverting to your real Discord identity."""
        u = self.data.get_user(ctx.author.id)
        u["nickname"] = None
        u["avatar"]   = None
        await self.data.upsert_user(ctx.author.id)
        await ctx.send(
            embed=Embeds.action("Display name and avatar reset to your Discord defaults.", ctx.author),
            ephemeral=True,
        )

    # ── /premium ──────────────────────────────────────────────────────────

    @commands.hybrid_group(name="premium", description="View premium status and information.")
    async def premium(self, ctx: commands.Context[MusubiBot]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send(
                embed=Embeds.info(
                    "Use `/premium status` to view active subscriptions.\n"
                    "Use `/redeem <key>` to activate a premium key."
                ),
                ephemeral=True,
            )

    @premium.command(name="status", description="Check premium status for yourself and this server.")
    async def premium_status(self, ctx: commands.Context[MusubiBot]) -> None:
        """Check active premium subscriptions for this server and your personal account."""
        now = datetime.now(timezone.utc).isoformat()

        guild_premium = None
        if ctx.guild:
            try:
                rows = await self.data._get("Premium", {
                    "select":     "tier,expires_at",
                    "guild_id":   f"eq.{ctx.guild.id}",
                    "expires_at": f"gt.{now}",
                    "order":      "expires_at.desc",
                    "limit":      "1",
                })
                guild_premium = rows[0] if rows else None
            except Exception:
                pass

        user_premium = None
        try:
            rows = await self.data._get("Premium", {
                "select":     "tier,expires_at",
                "user_id":    f"eq.{ctx.author.id}",
                "expires_at": f"gt.{now}",
                "order":      "expires_at.desc",
                "limit":      "1",
            })
            user_premium = rows[0] if rows else None
        except Exception:
            pass

        lines: list[str] = []

        if ctx.guild:
            if guild_premium:
                expiry = guild_premium["expires_at"][:10]
                lines.append(f"> `✨` *Server Premium:* `Active` — expires `{expiry}`")
            else:
                lines.append("> `✨` *Server Premium:* `Inactive`")

        if user_premium:
            expiry = user_premium["expires_at"][:10]
            lines.append(f"> `✨` *Personal Premium:* `Active` — expires `{expiry}`")
        else:
            lines.append("> `✨` *Personal Premium:* `Inactive`")

        await ctx.send(embed=Embeds.premium_status(lines), ephemeral=True)

    # ── /redeem ───────────────────────────────────────────────────────────

    @commands.hybrid_command(name="redeem", description="Redeem a premium key for yourself or this server.")
    async def redeem(
        self,
        ctx: commands.Context[MusubiBot],
        key: str,
    ) -> None:
        """
        Redeem a premium key.
        User keys grant personal premium. Guild keys grant server premium and must be
        redeemed inside a registered server.

        Parameters
        ----------
        key: str
            Your premium key (format: MSBY-XXXX-XXXX-XXXX).
        """
        rows = await self.data._get("PremiumKeys", {
            "select": "type,redeemed",
            "key":    f"eq.{key.upper()}",
        })

        if not rows:
            await ctx.send(embed=Embeds.error("Invalid key."), ephemeral=True)
            return

        row      = rows[0]
        key_type = row["type"]

        if row["redeemed"]:
            await ctx.send(embed=Embeds.error("This key has already been redeemed."), ephemeral=True)
            return

        if key_type == "guild":
            if not ctx.guild:
                await ctx.send(
                    embed=Embeds.error("Guild keys must be redeemed inside a server."),
                    ephemeral=True,
                )
                return
            if not self.data.is_guild_registered(ctx.guild.id):
                await ctx.send(
                    embed=Embeds.error(
                        "This server isn't registered with Musubi yet. Run `/setup` first."
                    ),
                    ephemeral=True,
                )
                return
            ok, msg = await self.data.redeem_key(key, guild_id=ctx.guild.id)
        else:
            ok, msg = await self.data.redeem_key(key, user_id=ctx.author.id)

        if ok:
            log.info(
                "Key redeemed — key:%s type:%s by:%d guild:%s",
                key.upper(), key_type, ctx.author.id,
                str(ctx.guild.id) if ctx.guild else "DM",
            )
            await ctx.send(embed=Embeds.action(msg, ctx.author), ephemeral=True)
        else:
            await ctx.send(embed=Embeds.error(msg), ephemeral=True)


async def setup(bot: MusubiBot) -> None:
    await bot.add_cog(Premium(bot))