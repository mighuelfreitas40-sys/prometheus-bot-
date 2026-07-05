"""Moonsec Deobfuscator Bot - Discord."""
import os
import io
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from deobfuscators import v1
from modules import verify, logs

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ========== HELPERS ==========

async def fetch_url(url: str) -> str:
    """Baixa conteudo de uma URL (pastebin, pastefy, etc)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            return await resp.text()


def has_manage_guild(interaction: discord.Interaction) -> bool:
    """Checa se o usuario tem permissao de Gerenciar Servidor."""
    return (
        interaction.user.guild_permissions.manage_guild
        or interaction.user.guild_permissions.administrator
    )


async def _get_code(interaction, url, arquivo):
    """Obtem o codigo de URL ou arquivo."""
    if not url and not arquivo:
        await interaction.followup.send("Envie uma URL ou um arquivo.", ephemeral=True)
        return None, None
    if url and arquivo:
        await interaction.followup.send("Escolha apenas uma opcao: URL ou arquivo.", ephemeral=True)
        return None, None

    if url:
        code = await fetch_url(url)
        file_name = "deobfuscated.lua"
    else:
        code = (await arquivo.read()).decode("utf-8", errors="replace")
        file_name = arquivo.filename.replace(".lua", "_deobf.lua")

    return code, file_name


async def _send_result(interaction, result, file_name, label, deobf_type):
    """Envia o resultado da deobfuscacao."""
    buffer = io.BytesIO(result.encode())
    file = discord.File(fp=buffer, filename=file_name)

    await interaction.followup.send(
        f"Deobfuscacao **{label}** concluida para {interaction.user.mention}!",
        file=file,
        ephemeral=False
    )

    await logs.send_log(
        bot, interaction.guild_id, interaction.user,
        deobf_type, file_name, result
    )


# ========== SLASH COMMANDS ==========

@bot.tree.command(name="deobf_moonsecv3", description="Deobfusca codigo Lua usando Moonsec V3")
@app_commands.describe(
    url="URL do codigo ofuscado",
    arquivo="Arquivo .lua ofuscado"
)
async def deobf_moonsecv3(
    interaction: discord.Interaction,
    url: str = None,
    arquivo: discord.Attachment = None
):
    await interaction.response.defer(ephemeral=True)
    code, file_name = await _get_code(interaction, url, arquivo)
    if code is None:
        return

    try:
        result = v1.deobfuscate(code, mode="moonsecv3")
        await _send_result(interaction, result, file_name, "Moonsec V3", "moonsecv3")
    except Exception as e:
        await interaction.followup.send(f"Erro: {e}", ephemeral=True)


@bot.tree.command(name="deobf_moonsecv2", description="Deobfusca codigo Lua usando Moonsec V2")
@app_commands.describe(
    url="URL do codigo ofuscado",
    arquivo="Arquivo .lua ofuscado"
)
async def deobf_moonsecv2(
    interaction: discord.Interaction,
    url: str = None,
    arquivo: discord.Attachment = None
):
    await interaction.response.defer(ephemeral=True)
    code, file_name = await _get_code(interaction, url, arquivo)
    if code is None:
        return

    try:
        result = v1.deobfuscate(code, mode="moonsecv2")
        await _send_result(interaction, result, file_name, "Moonsec V2", "moonsecv2")
    except Exception as e:
        await interaction.followup.send(f"Erro: {e}", ephemeral=True)


@bot.tree.command(name="verify", description="Verifica qual obfuscador foi usado no codigo")
@app_commands.describe(
    url="URL do codigo",
    arquivo="Arquivo .lua"
)
async def verify_cmd(
    interaction: discord.Interaction,
    url: str = None,
    arquivo: discord.Attachment = None
):
    await interaction.response.defer(ephemeral=True)
    code, _ = await _get_code(interaction, url, arquivo)
    if code is None:
        return

    try:
        detected = verify.detect_obfuscator(code)

        embed = discord.Embed(
            title="Verificacao de Obfuscador",
            color=0x3498DB,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="Detectado",
            value=f"`{detected.upper()}`" if detected != "unknown" else "Nao foi possivel detectar",
            inline=False
        )
        embed.set_footer(text=f"Solicitado por {interaction.user}")

        await interaction.followup.send(embed=embed, ephemeral=False)

    except Exception as e:
        await interaction.followup.send(f"Erro: {e}", ephemeral=True)


@bot.tree.command(name="help", description="Mostra os comandos disponiveis")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Moonsec Deobfuscator Bot",
        description="Bot de deobfuscacao de scripts Lua.",
        color=0x9B59B6,
        timestamp=discord.utils.utcnow()
    )

    deobf_text = (
        "`/deobf_moonsecv3 <url|arquivo>` — Deobfusca com Moonsec V3\n"
        "`/deobf_moonsecv2 <url|arquivo>` — Deobfusca com Moonsec V2\n"
        "*Envie URL ou arquivo, apenas um dos dois.*"
    )
    embed.add_field(name="Deobfuscacao", value=deobf_text, inline=False)

    util_text = (
        "`/verify <url|arquivo>` — Detecta qual obfuscador foi usado\n"
        "`/help` — Mostra esta mensagem"
    )
    embed.add_field(name="Utilitarios", value=util_text, inline=False)

    admin_text = (
        "`/logs <canal>` — Define canal de logs de deobfuscacao *(requer Gerenciar Servidor)*\n"
        "`/servidores` — Rank de servidores por membros *(requer Gerenciar Servidor)*\n"
        "`/bot <true|false>` — Ativa/desativa o bot no servidor *(requer Gerenciar Servidor)*"
    )
    embed.add_field(name="Administracao", value=admin_text, inline=False)

    embed.set_footer(text=f"Solicitado por {interaction.user}")
    await interaction.response.send_message(embed=embed, ephemeral=False)


# ========== ADMIN COMMANDS ==========

@bot.tree.command(name="logs", description="Define o canal de logs de deobfuscacao")
@app_commands.describe(canal="Canal onde os logs serao enviados")
@app_commands.check(has_manage_guild)
async def logs_cmd(interaction: discord.Interaction, canal: discord.TextChannel):
    logs.set_log_channel(interaction.guild_id, canal.id)
    await interaction.response.send_message(
        f"Canal de logs definido para {canal.mention}",
        ephemeral=True
    )


@bot.tree.command(name="servidores", description="Mostra rank de servidores por membros")
@app_commands.check(has_manage_guild)
async def servidores_cmd(interaction: discord.Interaction):
    guilds = sorted(bot.guilds, key=lambda g: g.member_count or 0, reverse=True)

    lines = []
    for i, guild in enumerate(guilds[:20], 1):
        count = guild.member_count or 0
        lines.append(f"**{i}.** {guild.name} — `{count:,}` membros")

    embed = discord.Embed(
        title="Rank de Servidores",
        description="\n".join(lines) if lines else "Bot nao esta em nenhum servidor.",
        color=0xF39C12,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Total: {len(bot.guilds)} servidores")
    await interaction.response.send_message(embed=embed, ephemeral=False)


BOT_ENABLED = {}


@bot.tree.command(name="bot", description="Ativa ou desativa o bot no servidor")
@app_commands.describe(ativo="true para ativar, false para desativar")
@app_commands.check(has_manage_guild)
async def bot_cmd(interaction: discord.Interaction, ativo: bool):
    BOT_ENABLED[interaction.guild_id] = ativo
    status = "ativado" if ativo else "desativado"
    await interaction.response.send_message(
        f"Bot {status} neste servidor.",
        ephemeral=True
    )


# ========== CHECKS ==========

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "Voce precisa ter permissao de Gerenciar Servidor ou Administrador para usar este comando.",
            ephemeral=True
        )
    else:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Erro: {error}", ephemeral=True)
        else:
            await interaction.followup.send(f"Erro: {error}", ephemeral=True)


async def bot_enabled_check(interaction: discord.Interaction) -> bool:
    return BOT_ENABLED.get(interaction.guild_id, True)


for cmd_name in ("deobf_moonsecv3", "deobf_moonsecv2", "verify", "help"):
    cmd = bot.tree.get_command(cmd_name)
    if cmd:
        cmd.add_check(bot_enabled_check)


# ========== EVENTS ==========

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"Em {len(bot.guilds)} servidores")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/help para comandos"
        )
    )


@bot.event
async def on_guild_join(guild: discord.Guild):
    BOT_ENABLED[guild.id] = True


@bot.event
async def on_guild_remove(guild: discord.Guild):
    BOT_ENABLED.pop(guild.id, None)
    logs.LOG_CHANNELS.pop(guild.id, None)


# ========== RUN ==========

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN nao configurado nas variaveis de ambiente")
    bot.run(TOKEN)
