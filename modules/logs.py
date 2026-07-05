"""Sistema de logs de deobfuscação."""
import io
import discord
from discord.ext import commands

LOG_CHANNELS = {}  # {guild_id: channel_id}


def set_log_channel(guild_id: int, channel_id: int) -> None:
    LOG_CHANNELS[guild_id] = channel_id


def get_log_channel(guild_id: int) -> int | None:
    return LOG_CHANNELS.get(guild_id)


async def send_log(
    bot: commands.Bot,
    guild_id: int,
    user: discord.User,
    deobf_type: str,
    file_name: str,
    deobf_content: str
) -> None:
    """Envia log de deobfuscação pro canal configurado."""
    channel_id = get_log_channel(guild_id)
    if not channel_id:
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        return

    embed = discord.Embed(
        title="Deobfuscação Realizada",
        color=0x00FF00,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Usuário", value=f"{user.mention} (`{user.id}`)", inline=False)
    embed.add_field(name="Tipo", value=f"`{deobf_type}`", inline=True)
    embed.add_field(name="Arquivo", value=f"`{file_name}`", inline=True)

    file = discord.File(
        fp=io.BytesIO(deobf_content.encode()),
        filename=file_name
    )
    await channel.send(embed=embed, file=file)
