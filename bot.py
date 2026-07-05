"""Deobfuscator Bot - Discord (API Speack)."""
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
    """Baixa conteudo de uma URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            return await resp.text()


def has_manage_guild(interaction: discord.Interaction) -> bool:
    return (
        interaction.user.guild_permissions.manage_guild
        or interaction.user.guild_permissions.administrator
    )


# ========== DELOBF COMMAND COM SELECT MENU ==========

class DeobfSelect(discord.ui.Select):
    def __init__(self, code_or_url: str, is_url: bool, file_name: str):
        self.code_or_url = code_or_url
        self.is_url = is_url
        self.file_name = file_name

        options = [
            discord.SelectOption(label="Moonsec V3", value="moonsecv3", description="Para scripts ofuscados com Moonsec V3"),
            discord.SelectOption(label="WeAreDevs", value="wearedevs", description="Para scripts ofuscados com WeAreDevs"),
            discord.SelectOption(label="Hercules", value="hercules", description="Para scripts ofuscados com Hercules"),
            discord.SelectOption(label="IronVeil", value="ironveil", description="Para scripts ofuscados com IronVeil"),
        ]
        super().__init__(placeholder="Selecione o desfuscador", options=options)

    async def callback(self, interaction: discord.Interaction):
        mode = self.values[0]
        label = mode.upper()

        await interaction.response.defer(ephemeral=False)

        try:
            if self.is_url:
                result = v1.deobfuscate_from_url(self.code_or_url, mode=mode)
            else:
                result = v1.deobfuscate(self.code_or_url, mode=mode)

            if result.startswith("Erro"):
                await interaction.followup.send(f"Deobfuscacao **{label}** falhou: {result}", ephemeral=True)
                return

            # Envia na DM
            dm_sent = False
            try:
                dm = await interaction.user.create_dm()
                buffer = io.BytesIO(result.encode())
                file = discord.File(fp=buffer, filename=self.file_name)
                await dm.send(
                    f"Deobfuscacao **{label}** concluida! Aqui esta o seu script:",
                    file=file
                )
                dm_sent = True
            except discord.Forbidden:
                pass

            # Confirma no canal publico
            if dm_sent:
                await interaction.followup.send(
                    f"Script desfuscado e enviado na DM de {interaction.user.mention}!",
                    ephemeral=False
                )
            else:
                # Se nao conseguiu DM, envia no canal
                buffer = io.BytesIO(result.encode())
                file = discord.File(fp=buffer, filename=self.file_name)
                await interaction.followup.send(
                    f"Deobfuscacao **{label}** concluida para {interaction.user.mention}! (DM bloqueada, enviado aqui)",
                    file=file,
                    ephemeral=False
                )

            # Log
            await logs.send_log(
                bot, interaction.guild_id, interaction.user,
                mode, self.file_name, result
            )

        except Exception as e:
            await interaction.followup.send(f"Erro: {e}", ephemeral=True)


class DeobfView(discord.ui.View):
    def __init__(self, code_or_url: str, is_url: bool, file_name: str):
        super().__init__(timeout=60)
        self.add_item(DeobfSelect(code_or_url, is_url, file_name))


@bot.tree.command(name="deobf", description="Deobfusca codigo Lua")
@app_commands.describe(
    url="URL do codigo ofuscado",
    arquivo="Arquivo .lua ofuscado"
)
async def deobf(
    interaction: discord.Interaction,
    url: str = None,
    arquivo: discord.Attachment = None
):
    await interaction.response.defer(ephemeral=False)

    if not url and not arquivo:
        await interaction.followup.send("Envie uma URL ou um arquivo.", ephemeral=True)
        return
    if url and arquivo:
        await interaction.followup.send("Escolha apenas uma opcao: URL ou arquivo.", ephemeral=True)
        return

    try:
        if url:
            code = await fetch_url(url)
            detected = verify.detect_obfuscator(code)
            code_or_url = url
            is_url = True
            file_name = "deobfuscated.lua"
        else:
            code = (await arquivo.read()).decode("utf-8", errors="replace")
            detected = verify.detect_obfuscator(code)
            code_or_url = code
            is_url = False
            file_name = arquivo.filename.replace(".lua", "_deobf.lua")

        suggestion = detected if detected != "unknown" else "moonsecv3"
        suggestion_label = suggestion.upper()

        embed = discord.Embed(
            title="Selecione o desfuscador",
            description=f"Obfuscador detectado: `{detected.upper() if detected != 'unknown' else 'Nao detectado'}`\n\n"
                        f"Desfuscador recomendado: **{suggestion_label}**",
            color=0x9B59B6,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Solicitado por {interaction.user}")

        view = DeobfView(code_or_url, is_url, file_name)
        await interaction.followup.send(embed=embed, view=view, ephemeral=False)

    except Exception as e:
        await interaction.followup.send(f"Erro: {e}", ephemeral=True)


# ========== VERIFY COMMAND ==========

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

    if not url and not arquivo:
        await interaction.followup.send("Envie uma URL ou um arquivo.", ephemeral=True)
        return
    if url and arquivo:
        await interaction.followup.send("Escolha apenas uma opcao: URL ou arquivo.", ephemeral=True)
        return

    try:
        if url:
            code = await fetch_url(url)
        else:
            code = (await arquivo.read()).decode("utf-8", errors="replace")

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


# ========== HELP COMMAND ==========

@bot.tree.command(name="help", description="Mostra os comandos disponiveis")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Deobfuscator Bot",
        description="Bot de deobfuscacao de scripts Lua via API Speack.",
        color=0x9B59B6,
        timestamp=discord.utils.utcnow()
    )

    deobf_text = (
        "`/deobf <url|arquivo>` — Deobfusca com menu de selecao (Moonsec V3, WeAreDevs, Hercules, IronVeil)\n"
        "*Envie URL ou arquivo, apenas um dos dois.*"
    )
    embed.add_field(name="Deobfuscacao", value=deobf_text, inline=False)

    util_text = (
        "`/verify <url|arquivo>` — Detecta qual obfuscador foi usado\n"
        "`/help` — Mostra esta mensagem"
    )
    embed.add_field(name="Utilitarios", value=util_text, inline=False)

    admin_text = (
        "`/logs <canal>` — Define canal de logs *(requer Gerenciar Servidor)*\n"
        "`/servidores` — Rank de servidores por membros *(requer Gerenciar Servidor)*\n"
        "`/bot <true|false>` — Ativa/desativa o bot *(requer Gerenciar Servidor)*"
    )
    embed.add_field(name="Administracao", value=admin_text, inline=False)

    embed.set_footer(text=f"Solicitado por {interaction.user}")
    await interaction.response.send_message(embed=embed, ephemeral=False)


# ========== ADMIN COMMANDS ==========

@bot.tree.command(name="logs", description="Define o canal de logs")
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
            "Voce precisa ter permissao de Gerenciar Servidor ou Administrador.",
            ephemeral=True
        )
    else:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Erro: {error}", ephemeral=True)
        else:
            await interaction.followup.send(f"Erro: {error}", ephemeral=True)


async def bot_enabled_check(interaction: discord.Interaction) -> bool:
    return BOT_ENABLED.get(interaction.guild_id, True)


for cmd_name in ("deobf", "verify", "help"):
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
