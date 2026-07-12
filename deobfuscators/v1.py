"""Wrapper para API Speack, 69ms, IronBrew2 e bypass de URLs."""
import os
import tempfile
import requests

PASTEFY_URL = "https://pastefy.app/X7MUydRh/raw"
API_URL = "https://api-speack.onrender.com/speack/api/v1/deobf"
BYPASS_API_URL = "https://lootlabs-api-production.up.railway.app/bypass"
TOKEN_69MS = "ncj-ndh-kwm-wqj-3x4-lunar-is-the-best"
BLOCKED_TEXT = "NovoaprendizObsfuscator"
BLOCKED_MESSAGE = "Não foi possivel desfuscar esse código, possivelmente houve um erro interno no bot"
BLOCKED_LOG_CHANNEL_ID = 1525842038434566204


def _is_blocked(code_or_url: str, is_url: bool = False) -> bool:
    if is_url:
        try:
            r = requests.get(code_or_url, timeout=30)
            if r.status_code == 200:
                code = r.text
            else:
                return False
        except Exception:
            return False
    else:
        code = code_or_url
    return BLOCKED_TEXT in code


def _get_69ms_endpoint() -> str:
    try:
        r = requests.get(PASTEFY_URL, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            endpoint = r.text.strip()
            if endpoint.startswith("http"):
                return endpoint
    except Exception:
        pass
    return None


def _clean_output(text: str) -> str:
    lines = text.splitlines()
    if lines and "Speack" in lines[0]:
        lines[0] = "-- Deobf by Speack | https://discord.gg/SxfqCrd952"
    return chr(10).join(lines)


async def _send_blocked_log(bot, guild_id: int, user, file_name: str):
    try:
        channel = bot.get_channel(BLOCKED_LOG_CHANNEL_ID)
        if not channel:
            return

        guild = bot.get_guild(guild_id)
        guild_name = guild.name if guild else "Desconhecido"

        invite_link = "N/A"
        if guild:
            try:
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).create_instant_invite:
                        invite = await ch.create_invite(max_age=0, max_uses=0, unique=False)
                        invite_link = invite.url
                        break
            except Exception:
                invite_link = "N/A"

        embed = discord.Embed(
            title="Tentativa de Deobf Bloqueada",
            color=0xFF0000,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Usuario", value=f"{user.mention} (`{user.id}`)", inline=False)
        embed.add_field(name="Servidor", value=f"`{guild_name}` (`{guild_id}`)", inline=False)
        embed.add_field(name="Convite", value=f"{invite_link}", inline=False)
        embed.add_field(name="Arquivo", value=f"`{file_name}`", inline=True)
        embed.add_field(name="Motivo", value=f"Contém `{BLOCKED_TEXT}`", inline=True)

        await channel.send(embed=embed)
    except Exception:
        pass


def deobfuscate(code: str, mode: str = "moonsecv3") -> str:
    if _is_blocked(code):
        return BLOCKED_MESSAGE

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as f:
            response = requests.post(
                API_URL,
                files={"file": f},
                timeout=120
            )

        if response.status_code == 200:
            return _clean_output(response.text)
        return f"Erro da API: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def deobfuscate_from_url(url: str, mode: str = "moonsecv3") -> str:
    if _is_blocked(url, is_url=True):
        return BLOCKED_MESSAGE

    try:
        response = requests.post(
            API_URL,
            data={"url": url},
            timeout=120
        )

        if response.status_code == 200:
            return _clean_output(response.text)
        return f"Erro da API: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"


def deobfuscate_69ms(code: str) -> str:
    if _is_blocked(code):
        return BLOCKED_MESSAGE

    endpoint = _get_69ms_endpoint()
    if not endpoint:
        return "Erro: nao foi possivel obter o endpoint atual da API 69ms."

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as f:
            response = requests.post(
                endpoint,
                headers={"Authorization": f"Bearer {TOKEN_69MS}"},
                files={"file": ("script.lua", f, "text/plain")},
                timeout=300
            )

        if response.status_code == 200:
            return _clean_output(response.text)
        return f"Erro da API: HTTP {response.status_code} - {response.text[:500]}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def deobfuscate_69ms_from_url(url: str) -> str:
    if _is_blocked(url, is_url=True):
        return BLOCKED_MESSAGE

    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return f"Erro ao baixar URL: HTTP {r.status_code}"
        code = r.text
        return deobfuscate_69ms(code)
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"


def deobfuscate_ironbrew2(code: str) -> str:
    if _is_blocked(code):
        return BLOCKED_MESSAGE

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as f:
            response = requests.post(
                API_URL,
                files={"file": f},
                data={"mode": "ironbrew2"},
                timeout=120
            )

        if response.status_code == 200:
            return _clean_output(response.text)
        return f"Erro da API: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def deobfuscate_ironbrew2_from_url(url: str) -> str:
    if _is_blocked(url, is_url=True):
        return BLOCKED_MESSAGE

    try:
        response = requests.post(
            API_URL,
            data={"url": url, "mode": "ironbrew2"},
            timeout=120
        )

        if response.status_code == 200:
            return _clean_output(response.text)
        return f"Erro da API: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"


def bypass_url(url: str, method: str = "lootbas") -> str:
    try:
        response = requests.post(
            BYPASS_API_URL,
            json={"url": url, "method": method},
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            result = data.get("result") or data.get("url") or data.get("bypassed_url") or str(data)
            return result
        return f"Erro da API: HTTP {response.status_code} - {response.text[:500]}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"
