"""
Project MUSUBI — cogs/config.py
Server setup and configuration.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from datamanager import DataManager
from botprotocol import MusubiBot
from embeds import Embeds

log = logging.getLogger("musubi.config")

_pending_unregister: set[int] = set()


def is_manager():
    async def predicate(ctx: commands.Context[MusubiBot]) -> bool:
        if not ctx.guild:
            await ctx.send(
                embed=Embeds.error("This command can only be used inside a server."),
                ephemeral=True,
            )
            return False
        if isinstance(ctx.author, discord.Member):
            if ctx.author.guild_permissions.manage_guild:
                return True
            await ctx.send(
                embed=Embeds.error("You need the **Manage Server** permission to use this command."),
                ephemeral=True,
            )
        return False
    return commands.check(predicate)


async def _get_or_create_webhook(channel: discord.TextChannel) -> discord.Webhook:
    """Reuse the existing Musubi Bridge webhook or create one if missing."""
    webhooks = await channel.webhooks()
    existing = next((w for w in webhooks if w.name == "Musubi Bridge"), None)
    if existing:
        return existing
    return await channel.create_webhook(name="Musubi Bridge")


class Config(commands.Cog):

    def __init__(self, bot: MusubiBot) -> None:
        self.bot  = bot
        self.data: DataManager = bot.data

    # ── /setup ───────────────────────────────────────────────────────────

    @commands.hybrid_command(name="setup", description="Register this server and choose a booth channel.")
    @is_manager()
    async def setup(
        self,
        ctx: commands.Context[MusubiBot],
        channel: discord.TextChannel,
    ) -> None:
        """
        Register this server with Musubi and designate a booth channel.
        The booth channel is the only channel from which calls can be placed and received.

        Parameters
        ----------
        channel: discord.TextChannel
            The channel to use as the call booth.
        """
        assert ctx.guild is not None

        if self.data.is_guild_registered(ctx.guild.id):
            g     = self.data.get_guild(ctx.guild.id)
            booth = g["booth_channel"] if g else "unknown"
            await ctx.send(
                embed=Embeds.info(
                    f"This server is already set up. Booth channel: <#{booth}>.\n"
                    "Use `/setbooth` to change it."
                ),
                ephemeral=True,
            )
            return

        try:
            wh = await _get_or_create_webhook(channel)
        except discord.Forbidden:
            await ctx.send(
                embed=Embeds.error("I need the **Manage Webhooks** permission in that channel."),
                ephemeral=True,
            )
            return

        await self.data.register_guild(ctx.guild.id, channel.id, wh.url)
        self.data.webhook_cache[str(ctx.guild.id)] = discord.Webhook.from_url(
            wh.url, session=self.bot.session
        )

        log.info("Guild registered — id:%d booth:%d", ctx.guild.id, channel.id)
        await ctx.send(
            embed=Embeds.action(
                f"Setup complete! Booth channel set to <#{channel.id}>.\n"
                "Users can now use `/call` to connect with other servers.",
                ctx.author,
            ),
            ephemeral=True,
        )

    # ── /setbooth ────────────────────────────────────────────────────────

    @commands.hybrid_command(name="setbooth", description="Change the booth channel for this server.")
    @is_manager()
    async def setbooth(
        self,
        ctx: commands.Context[MusubiBot],
        channel: discord.TextChannel,
    ) -> None:
        """
        Change the designated booth channel for this server.

        Parameters
        ----------
        channel: discord.TextChannel
            The new booth channel.
        """
        assert ctx.guild is not None
        if not self.data.is_guild_registered(ctx.guild.id):
            await ctx.send(
                embed=Embeds.error("This server isn't registered yet. Run `/setup` first."),
                ephemeral=True,
            )
            return

        try:
            wh = await _get_or_create_webhook(channel)
        except discord.Forbidden:
            await ctx.send(
                embed=Embeds.error("I need the **Manage Webhooks** permission in that channel."),
                ephemeral=True,
            )
            return

        gid = str(ctx.guild.id)
        self.data.guilds[gid]["booth_channel"] = str(channel.id)
        self.data.guilds[gid]["webhook"]       = wh.url
        self.data.webhook_cache.pop(gid, None)

        try:
            await self.data._patch("Guilds", {"guild_id": f"eq.{gid}"}, {
                "booth_channel": str(channel.id),
                "webhook":       wh.url,
            })
        except Exception as e:
            log.error("setbooth patch failed: %s", e)

        await ctx.send(
            embed=Embeds.action(f"Booth channel updated to <#{channel.id}>.", ctx.author),
            ephemeral=True,
        )

    # ── /prefix ──────────────────────────────────────────────────────────

    @commands.hybrid_group(name="prefix", description="Manage command prefixes.")
    async def prefix(self, ctx: commands.Context[MusubiBot]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send(
                embed=Embeds.info("Available subcommands: `server <prefix>`, `self <prefix>`"),
                ephemeral=True,
            )

    @prefix.command(name="server", description="Set a custom prefix for this server. (Manage Server required)")
    @is_manager()
    async def prefix_server(
        self,
        ctx: commands.Context[MusubiBot],
        new_prefix: str,
    ) -> None:
        """
        Set a custom command prefix for this server.

        Parameters
        ----------
        new_prefix: str
            The prefix to use (e.g. !, ?, m!) — max 5 characters.
        """
        assert ctx.guild is not None
        if len(new_prefix) > 5:
            await ctx.send(
                embed=Embeds.error("Prefix must be 5 characters or fewer."),
                ephemeral=True,
            )
            return
        await self.data.set_guild_prefix(ctx.guild.id, new_prefix)
        await ctx.send(
            embed=Embeds.action(f"Server prefix set to `{new_prefix}`.", ctx.author),
            ephemeral=True,
        )

    @prefix.command(name="self", description="Set your personal prefix across all servers. (User premium required)")
    async def prefix_self(
        self,
        ctx: commands.Context[MusubiBot],
        new_prefix: str,
    ) -> None:
        """
        Set a personal command prefix that works across all servers. Requires user premium.

        Parameters
        ----------
        new_prefix: str
            Your personal prefix — max 5 characters.
        """
        if not await self.data.is_premium_user(ctx.author.id):
            await ctx.send(
                embed=Embeds.error(
                    "Personal prefixes require **User Premium**.\n"
                    "Use `/redeem` if you have a key, or contact a network admin."
                ),
                ephemeral=True,
            )
            return
        if len(new_prefix) > 5:
            await ctx.send(
                embed=Embeds.error("Prefix must be 5 characters or fewer."),
                ephemeral=True,
            )
            return
        u = self.data.get_user(ctx.author.id)
        u["prefix"] = new_prefix
        await self.data.upsert_user(ctx.author.id)
        await ctx.send(
            embed=Embeds.action(f"Personal prefix set to `{new_prefix}`.", ctx.author),
            ephemeral=True,
        )

    # ── /unregister ───────────────────────────────────────────────────────

    @commands.hybrid_command(name="unregister", description="Remove this server from Musubi.")
    @is_manager()
    async def unregister(
        self,
        ctx: commands.Context[MusubiBot],
        confirm: bool = False,
    ) -> None:
        """
        Unregister this server from Musubi, removing all server data.
        Run with confirm:True to skip the confirmation prompt.

        Parameters
        ----------
        confirm: bool
            Set to True to confirm removal. Defaults to False (shows warning).
        """
        assert ctx.guild is not None
        if not self.data.is_guild_registered(ctx.guild.id):
            await ctx.send(
                embed=Embeds.error("This server is not registered with Musubi."),
                ephemeral=True,
            )
            return

        if not confirm:
            _pending_unregister.add(ctx.guild.id)
            await ctx.send(
                embed=Embeds.info(
                    "⚠️ This will permanently remove **all data** for this server, "
                    "including the booth channel, XP, and premium.\n\n"
                    "Run `/unregister confirm:True` to confirm."
                ),
                ephemeral=True,
            )
            return

        if ctx.guild.id not in _pending_unregister:
            await ctx.send(
                embed=Embeds.info(
                    "Please run `/unregister` first to see the warning, "
                    "then confirm with `/unregister confirm:True`."
                ),
                ephemeral=True,
            )
            return

        await self.data.unregister_guild(ctx.guild.id)
        _pending_unregister.discard(ctx.guild.id)
        log.info("Guild unregistered — id:%d", ctx.guild.id)
        await ctx.send(
            embed=Embeds.action("This server has been removed from Musubi. Goodbye!", ctx.author),
            ephemeral=True,
        )


async def setup(bot: MusubiBot) -> None:
    await bot.add_cog(Config(bot))