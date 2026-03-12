"""
Project MUSUBI — botprotocol.py
Typed protocol for the Musubi bot instance.

Every cog receives a plain `commands.Bot` from discord.py, but the actual
runtime object is `Musubi` which has `.data` and `.session` attached in
__init__. Without this protocol, Pyright sees those attrs as unknown and
forces `# type: ignore[attr-defined]` everywhere.

Usage in cogs:
    from botprotocol import MusubiBot

    class MyCog(commands.Cog):
        def __init__(self, bot: MusubiBot) -> None:
            self.bot  = bot
            self.data = bot.data
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import ClientSession
from discord.ext import commands

if TYPE_CHECKING:
    from datamanager import DataManager


class MusubiBot(commands.Bot):
    """
    Typed subclass used only for annotation purposes.
    The real instance is created in main.py as `Musubi(commands.Bot)` —
    this class simply tells Pyright what extra attributes to expect.
    """
    data:    "DataManager"
    session: ClientSession