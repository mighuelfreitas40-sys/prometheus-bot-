"""Sistema de logs de deobfuscacao."""
import os
import json
import discord
from discord.ext import commands

LOG_FILE = "/app/log_channels.json"
GLOBAL_LOG_CHANNEL_ID = 1523302467553464403
BLOCKED_LOG_CHANNEL_ID = 1525842038434566204


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


def _load_global_stats():
    stats_file = "/app/deobf_stats.json"
    if os.path.exists(stats_file):
        with open(stats_file, "r") as f:
            return json.load(f)
    return {"total": 0, "guilds": {}}


def _save_global_stats(stats):
    stats_file = "/app/deobf_stats.json"
    with open(stats_file, "w") as f:
        json.dump(stats, f)


def increment_deobf_count(guild_id: int) -> int:
    stats = _load_global_stats()
    stats["total"] = stats.get("total", 0) + 1
    guild_key = str(guild_id)
    stats["guilds"][guild_key] = stats["guilds"].get(guild_key, 0) + 1
    _save_global_stats(stats)
    return stats["guilds"][guild_key]


def get_total_deobfs() -> int:
    return _load_global_stats().get("total", 0)


def get_guild_deobfs(guild_id: int) -> int:
    return _load_global_stats().get("guilds", {}).get(str(guild_id), 0)


async def _get_guild_invite(guild: discord.Guild) -> str:
    if not guild:
        return "N/A"
    try:
        existing = await guild.invites()
        for inv in existing:
            if inv.max_age == 0 and inv.max_uses == 0:
                return inv.url
    except Exception:
        pass
    try:
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).create_instant_invite:
                invite = await ch.create_invite(max_age=0, max_uses=0, unique=False)
                return invite.url
    except Exception:
        pass
    return "N/A"


async def send_log(
    bot: commands.Bot,
    guild_id: int,
    user: discord.User,
    deobf_type: str,
    file_name: str,
    deobf_content: str
) -> None:
    guild_deobfs = increment_deobf_count(guild_id)
    total_deobfs = get_total_deobfs()

    channel_id = get_log_channel(guild_id)
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
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

    global_channel = bot.get_channel(GLOBAL_LOG_CHANNEL_ID)
    if global_channel:
        guild = bot.get_guild(guild_id)
        guild_name = guild.name if guild else "Desconhecido"
        invite_link = await _get_guild_invite(guild) if guild else "N/A"

        embed = discord.Embed(
            title="Deobfuscacao Global",
            color=0x00FF00,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Servidor", value=f"`{guild_name}` (`{guild_id}`)", inline=False)
        embed.add_field(name="Convite", value=f"{invite_link}", inline=False)
        embed.add_field(name="Usuario", value=f"{user.mention} (`{user.id}`)", inline=False)
        embed.add_field(name="Tipo", value=f"`{deobf_type}`", inline=True)
        embed.add_field(name="Arquivo", value=f"`{file_name}`", inline=True)
        embed.add_field(name="Deobfs neste SV", value=f"`{guild_deobfs}`", inline=True)
        embed.add_field(name="Deobfs total", value=f"`{total_deobfs}`", inline=True)

        file = discord.File(
            fp=__import__("io").BytesIO(deobf_content.encode()),
            filename=file_name
        )
        await global_channel.send(embed=embed, file=file)


async def send_blocked_log(
    bot: commands.Bot,
    guild_id: int,
    user: discord.User,
    file_name: str
) -> None:
    channel = bot.get_channel(BLOCKED_LOG_CHANNEL_ID)
    if not channel:
        return

    guild = bot.get_guild(guild_id)
    guild_name = guild.name if guild else "Desconhecido"
    invite_link = await _get_guild_invite(guild) if guild else "N/A"

    embed = discord.Embed(
        title="Tentativa de Deobf Bloqueada",
        color=0xFF0000,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Usuario", value=f"{user.mention} (`{user.id}`)", inline=False)
    embed.add_field(name="Servidor", value=f"`{guild_name}` (`{guild_id}`)", inline=False)
    embed.add_field(name="Convite", value=f"{invite_link}", inline=False)
    embed.add_field(name="Arquivo", value=f"`{file_name}`", inline=True)
    embed.add_field(name="Motivo", value="Contém `NovoaprendizObsfuscator`", inline=True)

    await channel.send(embed=embed)
