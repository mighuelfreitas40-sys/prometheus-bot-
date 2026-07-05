"""Sistema de logs de deobfuscacao."""
import os
import json
import discord
from discord.ext import commands

LOG_FILE = "/app/log_channels.json"


def _load_channels():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_channels(channels):
    with open(LOG_FILE, "w") as f:
        json.dump(channels, f)


def set_log_channel(guild_id: int, channel_id: int) -> None:
    channels = _load_channels()
    channels[str(guild_id)] = channel_id
    _save_channels(channels)


def get_log_channel(guild_id: int) -> int | None:
    channels = _load_channels()
    return channels.get(str(guild_id))


def remove_log_channel(guild_id: int) -> None:
    channels = _load_channels()
    channels.pop(str(guild_id), None)
    _save_channels(channels)


async def send_log(
    bot: commands.Bot,
    guild_id: int,
    user: discord.User,
    deobf_type: str,
    file_name: str,
    deobf_content: str
) -> None:
    """Envia log de deobfuscacao pro canal configurado."""
    channel_id = get_log_channel(guild_id)
    if not channel_id:
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        return

    embed = discord.Embed(
        title="Deobfuscacao Realizada",
        color=0x00FF00,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Usuario", value=f"{user.mention} (`{user.id}`)", inline=False)
    embed.add_field(name="Tipo", value=f"`{deobf_type}`", inline=True)
    embed.add_field(name="Arquivo", value=f"`{file_name}`", inline=True)

    file = discord.File(
        fp=__import__("io").BytesIO(deobf_content.encode()),
        filename=file_name
    )
    await channel.send(embed=embed, file=file)
