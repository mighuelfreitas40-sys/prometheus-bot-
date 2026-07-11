import os
import io
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from deobfuscators import v1
from modules import verify, logs

TOKEN = os.getenv("DISCORD_TOKEN")

SUPPORTED_METHODS = {"moonsecv3", "wearedevs", "hercules", "ironveil", "ironbrew2", "69ms"}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 1252758938693144696


def make_error_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=0xE74C3C,
        timestamp=discord.utils.utcnow()
    )


async def fetch_url(url: str) -> str:
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


def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_ID


class DeobfSelect(discord.ui.Select):
    def __init__(self, code_or_url: str, is_url: bool, file_name: str):
        self.code_or_url = code_or_url
        self.is_url = is_url
        self.file_name = file_name

        options = [
            discord.SelectOption(label="Moonsec V3", value="moonsecv3", description="Scripts ofuscados com Moonsec V3", emoji="🌙"),
            discord.SelectOption(label="WeAreDevs", value="wearedevs", description="Scripts ofuscados com WeAreDevs", emoji="⚡"),
            discord.SelectOption(label="Hercules", value="hercules", description="Scripts ofuscados com Hercules", emoji="🏛️"),
            discord.SelectOption(label="IronVeil", value="ironveil", description="Scripts ofuscados com IronVeil", emoji="🛡️"),
            discord.SelectOption(label="IronBrew2", value="ironbrew2", description="Scripts ofuscados com IronBrew2", emoji="⚙️"),
            discord.SelectOption(label="69ms", value="69ms", description="Scripts ofuscados com 69ms", emoji="⏱️"),
        ]
        super().__init__(placeholder="Selecione um metodo", options=options)

    async def callback(self, interaction: discord.Interaction):
        mode = self.values[0]
        label = mode.upper()

        await interaction.response.send_message(
            f"Deobfuscando com **{label}**...",
            ephemeral=False
        )
        msg = await interaction.original_response()

        try:
            if self.is_url:
                if mode == "69ms":
                    result = v1.deobfuscate_69ms_from_url(self.code_or_url)
                elif mode == "ironbrew2":
                    result = v1.deobfuscate_ironbrew2_from_url(self.code_or_url)
                else:
                    result = v1.deobfuscate_from_url(self.code_or_url, mode=mode)
            else:
                if mode == "69ms":
                    result = v1.deobfuscate_69ms(self.code_or_url)
                elif mode == "ironbrew2":
                    result = v1.deobfuscate_ironbrew2(self.code_or_url)
                else:
                    result = v1.deobfuscate(self.code_or_url, mode=mode)

            if result.startswith("Erro"):
                embed = make_error_embed(
                    "Falha na Deobfuscacao",
                    f"Deobfuscacao **{label}** falhou: {result}"
                )
                await msg.edit(content="", embed=embed)
                return

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

            if dm_sent:
                await msg.edit(
                    content=f"Script desfuscado e enviado na DM de {interaction.user.mention}!"
                )
            else:
                buffer = io.BytesIO(result.encode())
                file = discord.File(fp=buffer, filename=self.file_name)
                await msg.edit(
                    content=f"Deobfuscacao **{label}** concluida para {interaction.user.mention}! (DM bloqueada, enviado aqui)",
                    attachments=[file]
                )

            await logs.send_log(
                bot, interaction.guild_id, interaction.user,
                mode, self.file_name, result
            )

        except Exception as e:
            embed = make_error_embed("Erro Inesperado", str(e))
            await msg.edit(content="", embed=embed)


class DeobfView(discord.ui.View):
    def __init__(self, code_or_url: str, is_url: bool, file_name: str):
        super().__init__(timeout=60)
        self.add_item(DeobfSelect(code_or_url, is_url, file_name))


class BypassSelect(discord.ui.Select):
    def __init__(self, url: str):
        self.target_url = url
        options = [
            discord.SelectOption(label="Lootbas", value="lootbas", description="Bypass via Lootbas", emoji="🔗"),
        ]
        super().__init__(placeholder="Selecione um metodo", options=options)

    async def callback(self, interaction: discord.Interaction):
        method = self.values[0]
        label = method.upper()

        await interaction.response.send_message(
            f"Executando bypass com **{label}**...",
            ephemeral=False
        )
        msg = await interaction.original_response()

        try:
            result = v1.bypass_url(self.target_url, method=method)

            if result.startswith("Erro"):
                embed = make_error_embed(
                    "Falha no Bypass",
                    f"Bypass **{label}** falhou: {result}"
                )
                await msg.edit(content="", embed=embed)
                return

            dm_sent = False
            try:
                dm = await interaction.user.create_dm()
                await dm.send(f"Bypass **{label}** concluido! URL original: `{self.target_url}`
Resultado: {result}")
                dm_sent = True
            except discord.Forbidden:
                pass

            if dm_sent:
                await msg.edit(
                    content=f"Bypass concluido e enviado na DM de {interaction.user.mention}!"
                )
            else:
                await msg.edit(
                    content=f"Bypass **{label}** concluido para {interaction.user.mention}! (DM bloqueada, enviado aqui)
URL original: `{self.target_url}`
Resultado: {result}"
                )

            await logs.send_log(
                bot, interaction.guild_id, interaction.user,
                f"bypass-{method}", self.target_url, result
            )

        except Exception as e:
            embed = make_error_embed("Erro Inesperado", str(e))
            await msg.edit(content="", embed=embed)


class BypassView(discord.ui.View):
    def __init__(self, url: str):
        super().__init__(timeout=60)
        self.add_item(BypassSelect(url))


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
    await interaction.response.send_message("Processando...", ephemeral=False)
    msg = await interaction.original_response()

    if not url and not arquivo:
        embed = make_error_embed(
            "Argumentos Invalidos",
            "Envie uma URL ou um arquivo."
        )
        await msg.edit(content="", embed=embed)
        return
    if url and arquivo:
        embed = make_error_embed(
            "Argumentos Invalidos",
            "Escolha apenas uma opcao: URL ou arquivo."
        )
        await msg.edit(content="", embed=embed)
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

        if detected == "unknown":
            rec_text = "Nao detectamos o obfuscador. Nao temos um metodo para recomendar, se quiser tentar o 69ms, IronBrew2 ou outros fica da sua escolha"
            rec_color = 0xF59E0B
        elif detected not in SUPPORTED_METHODS:
            rec_text = f"Detectamos que o script usa **{suggestion_label}**, mas nao temos um metodo para esse obfuscador. Se quiser tentar o 69ms, IronBrew2 ou outros fica da sua escolha"
            rec_color = 0xEF4444
        else:
            rec_text = f"**{suggestion_label}**"
            rec_color = 0x7C3AED

        detected_display = detected.upper() if detected != "unknown" else "Nao detectado"
        embed = discord.Embed(
            title="Selecione um metodo",
            description=(
                f"**Obfuscador detectado:** `{detected_display}`\n\n"
                f"**Metodo recomendado:** {rec_text}"
            ),
            color=rec_color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Solicitado por {interaction.user}")

        view = DeobfView(code_or_url, is_url, file_name)
        await msg.edit(content="", embed=embed, view=view)

    except Exception as e:
        embed = make_error_embed("Erro", str(e))
        await msg.edit(content="", embed=embed)


@bot.tree.command(name="bypass", description="Bypass de URL protegida")
@app_commands.describe(url="URL para bypass")
async def bypass_cmd(interaction: discord.Interaction, url: str):
    await interaction.response.send_message("Processando...", ephemeral=False)
    msg = await interaction.original_response()

    embed = discord.Embed(
        title="Selecione um metodo",
        description=f"**URL alvo:** `{url}`",
        color=0x7C3AED,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Solicitado por {interaction.user}")

    view = BypassView(url)
    await msg.edit(content="", embed=embed, view=view)


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
    await interaction.response.send_message("Verificando...", ephemeral=True)
    msg = await interaction.original_response()

    if not url and not arquivo:
        embed = make_error_embed(
            "Argumentos Invalidos",
            "Envie uma URL ou um arquivo."
        )
        await msg.edit(content="", embed=embed)
        return
    if url and arquivo:
        embed = make_error_embed(
            "Argumentos Invalidos",
            "Escolha apenas uma opcao: URL ou arquivo."
        )
        await msg.edit(content="", embed=embed)
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

        await msg.edit(content="", embed=embed)

    except Exception as e:
        error_embed = make_error_embed("Erro na Verificacao", str(e))
        await msg.edit(content="", embed=error_embed)


@bot.tree.command(name="verifymembers", description="Lista todos os membros nao-bot de um servidor")
@app_commands.describe(servidor="Nome do servidor")
@app_commands.check(is_owner)
async def verifymembers_cmd(interaction: discord.Interaction, servidor: str):
    await interaction.response.send_message("Procurando servidor...", ephemeral=True)
    msg = await interaction.original_response()

    target = None
    for guild in bot.guilds:
        if guild.name.lower() == servidor.lower():
            target = guild
            break

    if not target:
        embed = make_error_embed(
            "Servidor nao encontrado",
            f"Nao encontrei nenhum servidor com o nome `{servidor}`."
        )
        await msg.edit(content="", embed=embed)
        return

    try:
        await target.chunk()
    except Exception:
        pass

    members = [m for m in target.members if not m.bot]

    if not members:
        embed = make_error_embed(
            "Sem membros",
            f"Nao encontrei membros humanos no servidor `{target.name}`."
        )
        await msg.edit(content="", embed=embed)
        return

    me = target.me
    perms = me.guild_permissions
    perm_lines = []
    for perm, value in perms:
        if value:
            perm_lines.append(f"`{perm}`")
    perm_text = ", ".join(perm_lines) if perm_lines else "Nenhuma permissao ativa"

    lines = []
    for i, member in enumerate(members, 1):
        lines.append(f"**{i}.** {member.mention} — `{member.id}` — {member.display_name}")

    chunks = []
    current = []
    current_len = 0
    for line in lines:
        if current_len + len(line) + 1 > 3900:
            chunks.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += len(line) + 1
    if current:
        chunks.append("\n".join(current))

    first = True
    for chunk in chunks:
        embed = discord.Embed(
            title=f"Membros de {target.name}" if first else None,
            description=chunk,
            color=0x7C3AED,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Permissoes do bot", value=perm_text, inline=False)
        embed.set_footer(text=f"Total: {len(members)} membros | Servidor: {target.name}")
        if first:
            await msg.edit(content="", embed=embed)
            first = False
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="kickbot", description="Kicka o bot de um servidor (owner only)")
@app_commands.describe(servidor_id="ID do servidor alvo")
@app_commands.check(is_owner)
async def kickbot_cmd(interaction: discord.Interaction, servidor_id: str):
    await interaction.response.defer(ephemeral=True)

    try:
        guild_id = int(servidor_id)
    except ValueError:
        await interaction.edit_original_response(content="ID do servidor invalido.")
        return

    target = bot.get_guild(guild_id)
    if not target:
        await interaction.edit_original_response(content="Bot nao esta nesse servidor ou ID invalido.")
        return

    guild_name = target.name
    try:
        await target.leave()
        await interaction.edit_original_response(content=f"Bot kickado do servidor **{guild_name}** (`{guild_id}`).")
    except discord.Forbidden:
        await interaction.edit_original_response(content="Sem permissao para sair desse servidor.")
    except discord.HTTPException as e:
        await interaction.edit_original_response(content=f"Erro HTTP ao tentar sair: {e.status}")
    except Exception as e:
        await interaction.edit_original_response(content=f"Erro inesperado: {type(e).__name__}: {str(e)[:100]}")


@bot.tree.command(name="help", description="Mostra os comandos disponiveis")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Deobfuscator Bot",
        description="Bot de deobfuscacao de scripts Lua via API Speack.",
        color=0x7C3AED,
        timestamp=discord.utils.utcnow()
    )

    deobf_text = (
        "`/deobf <url|arquivo>` — Deobfusca com menu de selecao (Moonsec V3, WeAreDevs, Hercules, IronVeil, IronBrew2, 69ms)\n"
        "*Envie URL ou arquivo, apenas um dos dois.*"
    )
    embed.add_field(name="Deobfuscacao", value=deobf_text, inline=False)

    bypass_text = (
        "`/bypass <url>` — Bypass de URL protegida (Lootbas)"
    )
    embed.add_field(name="Bypass", value=bypass_text, inline=False)

    util_text = (
        "`/verify <url|arquivo>` — Detecta qual obfuscador foi usado\n"
        "`/verifymembers <servidor>` — Lista membros de um servidor (owner only)\n"
        "`/kickbot <servidor_id>` — Kicka o bot de um servidor (owner only)\n"
        "`/perfil` — Mostra informacoes do bot\n"
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


@bot.tree.command(name="perfil", description="Mostra informacoes do bot NvDeobf2")
async def perfil_cmd(interaction: discord.Interaction):
    total_members = sum(g.member_count or 0 for g in bot.guilds)
    total_guilds = len(bot.guilds)

    embed = discord.Embed(
        title="NvDeobf2",
        description=(
            f"**Nome:** NvDeobf2\n"
            f"**Total de Membros:** `{total_members:,}`\n"
            f"**Total de Servidores:** `{total_guilds:,}`\n"
            f"**Dono:** <@{OWNER_ID}>"
        ),
        color=0x7C3AED,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Solicitado por {interaction.user}")
    await interaction.response.send_message(embed=embed, ephemeral=False)


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
    await interaction.response.send_message("Carregando...", ephemeral=False)
    msg = await interaction.original_response()

    guilds_data = []
    for guild in bot.guilds:
        try:
            await guild.chunk()
            count = guild.member_count or len(guild.members)
        except Exception:
            count = guild.member_count or 0

        invite_link = "N/A"
        try:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).create_instant_invite:
                    invite = await channel.create_invite(max_age=0, max_uses=0, unique=False)
                    invite_link = invite.url
                    break
        except Exception:
            invite_link = "N/A"

        guilds_data.append((guild.name, count, invite_link))

    guilds_data.sort(key=lambda x: x[1], reverse=True)

    lines = []
    for i, (name, count, link) in enumerate(guilds_data[:20], 1):
        lines.append(f"**{i}.** {name} — `{count:,}` membros — [Convite]({link})")

    embed = discord.Embed(
        title="Rank de Servidores",
        description="\n".join(lines) if lines else "Bot nao esta em nenhum servidor.",
        color=0xF39C12,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Total: {len(bot.guilds)} servidores")
    await msg.edit(content="", embed=embed)


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


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Voce precisa ter permissao de Gerenciar Servidor ou Administrador.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
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


for cmd_name in ("deobf", "verify", "help", "perfil", "verifymembers", "kickbot", "bypass"):
    cmd = bot.tree.get_command(cmd_name)
    if cmd:
        cmd.add_check(bot_enabled_check)


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


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN nao configurado nas variaveis de ambiente")
    bot.run(TOKEN)
