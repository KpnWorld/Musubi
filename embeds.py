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

    # ── Welcome ──────────────────────────────────────────────────────────────

    @staticmethod
    def welcome(bot_avatar: Optional[str] = None) -> discord.Embed:
        embed = discord.Embed(
            title="👋 Thanks for adding Musubi!",
            description=(
                "> *Musubi connects your Discord server to other servers in real time "
                "— like a phone call between communities.*\n\n"

                "**⚙️ Getting Started**\n"
                "> `1.` Run `/setup <#channel>` to register your server and set a booth channel.\n"
                "> `2.` Head to your booth channel and run `/call` to connect with another server.\n"
                "> `3.` Use `/hangup` to end the call at any time.\n\n"

                "**🏆 Callboard**\n"
                "> Your server earns **XP** for every message sent during a call. "
                "Check the monthly leaderboard with `/callboard` to see how your server ranks "
                "against others on the network.\n\n"

                "**📬 Invite System**\n"
                "> During a call, use `/invite` to send your server's invite link to the other side. "
                "Free servers get **10 invites/day**. "
                "Spend XP for extra quota with `/invitebuy`, "
                "or upgrade to **Server Premium** for **30 invites/day**.\n\n"

                "**✨ Free Premium**\n"
                "> Want free premium for your server or yourself? "
                "DM <@895767962722660372> and ask — we're happy to hook you up.\n\n"

                "**📖 Need help?**\n"
                "> Run `/help cmds` for a full command list, or `/help <command>` for details."
            ),
            color=BRAND_COLOR,
        )
        if bot_avatar:
            embed.set_thumbnail(url=bot_avatar)
        embed.set_footer(text="❣️ Made by †spector  •  /help to get started")
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
        guilds: list[tuple[str, str | None, str | None]],
        cycle_started: str,
    ) -> discord.Embed:
        MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
        lines: list[str] = []
        for i, (row, (name, icon_url, invite_url)) in enumerate(zip(rows, guilds)):
            medal = MEDALS[i] if i < len(MEDALS) else f"`#{i+1}`"
            xp    = row.get("xp") or 0
            entry = f"> {medal} **{name}** — `{xp:,} XP`"
            if invite_url:
                entry += f" • [Join]({invite_url})"
            lines.append(entry)

        first_icon = next((icon for _, icon, _ in guilds if icon), None)

        embed = discord.Embed(
            description="> `🏆` *Callboard — Current Cycle*\n\n" + "\n".join(lines),
            color=BRAND_COLOR,
        )
        embed.set_footer(text=f"Cycle started {cycle_started}  •  Resets monthly")
        if first_icon:
            embed.set_thumbnail(url=first_icon)
        return embed

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

    # ── Invite ───────────────────────────────────────────────────────────────

    @staticmethod
    def invite_sent(guild_name: str, invite_url: str, used: int, total: int) -> discord.Embed:
        embed = discord.Embed(
            description=(
                f"> `📬` *Invite from **{guild_name}***\n"
                f"> {invite_url}"
            ),
            color=BRAND_COLOR,
        )
        embed.set_footer(text=f"Invite {used}/{total} used today")
        return embed

    @staticmethod
    def invite_confirm(guild_name: str, used: int, total: int) -> discord.Embed:
        return discord.Embed(
            description=f"> `✅` *Invite sent for **{guild_name}**. (`{used}/{total}` used today)*",
            color=BRAND_COLOR,
        )

    @staticmethod
    def invite_status(used: int, total: int, bank: int, is_premium: bool, xp: int) -> discord.Embed:
        tier   = "`✨ Premium`" if is_premium else "`Free`"
        base   = 30 if is_premium else 10
        embed  = discord.Embed(
            description=(
                f"> `📬` *Invite Quota Status*\n\n"
                f"> `📊` *Used today:* `{used}/{total}`\n"
                f"> `🎁` *Base quota:* `{base}` ({tier})\n"
                f"> `🏦` *Purchased bank:* `{bank}`\n"
                f"> `✨` *Server XP:* `{xp:,}`\n\n"
                "> **Buy more quota with `/invitebuy`:**\n"
                "> `5 invites` → 150 XP\n"
                "> `10 invites` → 200 XP\n"
                "> `20 invites` → 350 XP"
            ),
            color=BRAND_COLOR,
        )
        return embed

    @staticmethod
    def invite_bought(amount: int, xp_cost: int, new_bank: int, new_xp: int) -> discord.Embed:
        return discord.Embed(
            description=(
                f"> `✅` *Purchased **+{amount} invites** for `{xp_cost} XP`.*\n"
                f"> `🏦` *Purchased bank:* `{new_bank}`\n"
                f"> `✨` *Remaining XP:* `{new_xp:,}`"
            ),
            color=BRAND_COLOR,
        )