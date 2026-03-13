"""
Project MUSUBI — embeds.py
Centralised embed factory.

All embeds use BRAND_COLOR (0xC084FC) for visual consistency.

Usage:
    from embeds import Embeds
    await ctx.send(embed=Embeds.error("Something went wrong."))
"""

from __future__ import annotations

import traceback
from typing import Optional

import discord

BRAND_COLOR = 0xC084FC


class Embeds:

    # ── Call flow ────────────────────────────────────────────────────────────

    @staticmethod
    def searching() -> discord.Embed:
        return discord.Embed(
            description="> `📞` *Searching for a call...*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def connected() -> discord.Embed:
        return discord.Embed(
            description="> `🟢` *Call connected — say hello!*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def ended() -> discord.Embed:
        return discord.Embed(
            description="> `⭕` *Call ended.*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def ended_hangup() -> discord.Embed:
        return discord.Embed(
            description="> `⭕` *The other server hung up.*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def ended_idle() -> discord.Embed:
        return discord.Embed(
            description="> `⭕` *Call ended — line went idle.*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def ended_terminated() -> discord.Embed:
        return discord.Embed(
            description="> `⭕` *Call terminated by a network administrator.*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def no_answer() -> discord.Embed:
        return discord.Embed(
            description="> `🟡` *No answer — couldn't find another server. Try again soon!*",
            color=BRAND_COLOR,
        )

    # ── Feedback ─────────────────────────────────────────────────────────────

    @staticmethod
    def error(message: str) -> discord.Embed:
        return discord.Embed(
            description=f"> `❗` *{message}*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def info(message: str) -> discord.Embed:
        return discord.Embed(
            description=f"> `🔵` *{message}*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def success(message: str) -> discord.Embed:
        return discord.Embed(
            description=f"> `✅` *{message}*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def critical(error: BaseException | str) -> discord.Embed:
        if isinstance(error, BaseException):
            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        else:
            tb = str(error)
        return discord.Embed(
            description=f"> `‼️` *Critical Error:*\n```\n{tb[:1800]}\n```",
            color=BRAND_COLOR,
        )

    @staticmethod
    def action(message: str, requester: Optional[discord.User | discord.Member] = None) -> discord.Embed:
        embed = discord.Embed(
            description=f"> `✅` *{message}*",
            color=BRAND_COLOR,
        )
        if requester:
            embed.set_footer(text=f"Requested by {requester.display_name}")
        return embed

    # ── Premium ──────────────────────────────────────────────────────────────

    @staticmethod
    def premium_key(key: str, premium_type: str) -> discord.Embed:
        label = "Personal" if premium_type == "user" else "Server"
        embed = discord.Embed(
            description=(
                f"> `🗝️` *New Premium Key Generated*\n"
                f"```\n{key}\n```"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text=f"Type: {label} Premium — keep this key safe.")
        return embed

    # ── Relay ────────────────────────────────────────────────────────────────

    @staticmethod
    def reply(sender: str, reply_to_user: str, quoted: str, content: str = "") -> discord.Embed:
        desc = (
            f"> `↩️` *{sender} → **{reply_to_user}***\n"
            f"> *\"{quoted}\"*"
        )
        if content:
            desc += f"\n\n{content}"
        return discord.Embed(description=desc, color=BRAND_COLOR)

    @staticmethod
    def friendme(author: str) -> discord.Embed:
        embed = discord.Embed(
            description=(
                f"> `📬` *Someone on this call wants to connect!*\n"
                f"> `👤` **{author}**"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text="Add them on Discord to stay in touch.")
        return embed

    @staticmethod
    def sudo_list(lines: str) -> discord.Embed:
        return discord.Embed(
            description=f"> `🔑` *Sudo Users*\n\n{lines}",
            color=BRAND_COLOR,
        )

    @staticmethod
    def session_active(count: int, lines: str, total: int) -> discord.Embed:
        embed = discord.Embed(
            description=(
                f"> `📞` *{count} active call{'s' if count != 1 else ''}*\n\n"
                + lines
            ),
            color=BRAND_COLOR,
        )
        if total > 10:
            embed.set_footer(text=f"Showing 10 of {total}")
        return embed

    @staticmethod
    def reload_all(lines: list[str]) -> discord.Embed:
        return discord.Embed(
            description="\n".join(lines),
            color=BRAND_COLOR,
        )

    @staticmethod
    def me_status(
        author: str,
        icon_url: str,
        premium: str,
        anon: str,
        nickname: str,
        avatar: str,
    ) -> discord.Embed:
        embed = discord.Embed(
            description=(
                f"> `✨` *Premium:* {premium}\n"
                f"> `🎭` *Anonymous:* {anon}\n"
                f"> `✏️` *Nickname:* {nickname}\n"
                f"> `🖼️` *Avatar:* {avatar}"
            ),
            color=BRAND_COLOR,
        )
        embed.set_author(name=author, icon_url=icon_url)
        return embed

    @staticmethod
    def premium_status(lines: list[str]) -> discord.Embed:
        embed = discord.Embed(
            description="\n".join(lines),
            color=BRAND_COLOR,
        )
        embed.set_author(name="Premium Status")
        embed.set_footer(text="Contact a network admin to obtain premium.")
        return embed

    @staticmethod
    def blocklist(entries: str, count: int) -> discord.Embed:
        embed = discord.Embed(
            description=f"> `🚫` *Global Blocklist*\n\n{entries}",
            color=BRAND_COLOR,
        )
        embed.set_footer(text=f"{count} entr{'y' if count == 1 else 'ies'}")
        return embed

    @staticmethod
    def tip(text: str) -> discord.Embed:
        return discord.Embed(
            description=f"> `💡` *{text}*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def heart(text: str) -> discord.Embed:
        return discord.Embed(
            description=f"> `❣️` *{text}*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def tip_and_heart(tip: str, heart: str) -> discord.Embed:
        """Combined tip + heart — one embed, no spam."""
        return discord.Embed(
            description=(
                f"> `💡` *{tip}*\n"
                f"> `❣️` *{heart}*"
            ),
            color=BRAND_COLOR,
        )

    @staticmethod
    def callboard(
        rows: list[dict],
        guilds: list[tuple[str, str | None, str | None]],  # [(name, icon_url, invite_url), ...]
        cycle_started: str,
    ) -> discord.Embed:
        """
        Current-cycle callboard embed.
        rows: leaderboard rows [{guild_id, xp, xp_reset_at}, ...]
        guilds: resolved (name, icon_url, invite_url) per row, same order
        cycle_started: ISO date string of cycle start
        """
        MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
        lines: list[str] = []
        for i, (row, (name, icon_url, invite_url)) in enumerate(zip(rows, guilds)):
            medal      = MEDALS[i] if i < len(MEDALS) else f"`#{i+1}`"
            xp         = row.get("xp") or 0
            # Make server name a clickable hyperlink if we have an invite URL
            label      = f"[{name}]({invite_url})" if invite_url else f"**{name}**"
            lines.append(f"> {medal} {label} — `{xp:,} XP`")

        # Use the first guild icon as thumbnail if available
        first_icon = next((icon for _, icon, _ in guilds if icon), None)

        embed = discord.Embed(
            description="> `🏆` *Callboard — Current Cycle*\n\n" + "\n".join(lines),
            color=BRAND_COLOR,
        )
        embed.set_footer(text=f"Cycle started {cycle_started}  •  Resets monthly")
        if first_icon:
            embed.set_thumbnail(url=first_icon)
        return embed

    # ── Invite ───────────────────────────────────────────────────────────────

    @staticmethod
    def invite_sent(server_name: str, invite_url: str, used: int, total: int) -> discord.Embed:
        """Sent to the target side when /invite is used."""
        return discord.Embed(
            description=(
                f"> `📬` *You've been invited to join **{server_name}**!*\n"
                f"> `🔗` {invite_url}"
            ),
            color=BRAND_COLOR,
        )

    @staticmethod
    def invite_confirm(server_name: str, used: int, total: int) -> discord.Embed:
        """Ephemeral confirmation for the user who ran /invite."""
        return discord.Embed(
            description=(
                f"> `✅` *Invite sent to the other server!*\n"
                f"> `📊` *Server quota: `{used}/{total}` used today*"
            ),
            color=BRAND_COLOR,
        )

    @staticmethod
    def invite_status(used: int, total: int, bank: int, is_premium: bool, xp: int) -> discord.Embed:
        """Shows a guild's current invite quota status."""
        tier = "`✨ Premium`" if is_premium else "`Free`"
        lines = [
            f"> `📊` *Used today:* `{used} / {total}`",
            f"> `🏦` *Purchased quota:* `{bank}`",
            f"> `✨` *Tier:* {tier}",
            f"> `⚡` *Server XP:* `{xp:,}`",
            "",
            "> **Buy more invites with XP:**",
            "> `150 XP` → +5 invites",
            "> `200 XP` → +10 invites",
            "> `350 XP` → +20 invites",
        ]
        return discord.Embed(
            description="\n".join(lines),
            color=BRAND_COLOR,
        )

    @staticmethod
    def invite_bought(amount: int, xp_spent: int, bank: int, xp_remaining: int) -> discord.Embed:
        return discord.Embed(
            description=(
                f"> `✅` *Purchased **+{amount} invites** for `{xp_spent} XP`!*\n"
                f"> `🏦` *Total purchased quota: `{bank}`*\n"
                f"> `⚡` *Server XP remaining: `{xp_remaining:,}`*"
            ),
            color=BRAND_COLOR,
        )

    @staticmethod
    def panel(title: str, description: str, footer: Optional[str] = None) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=BRAND_COLOR,
        )
        if footer:
            embed.set_footer(text=footer)
        return embed