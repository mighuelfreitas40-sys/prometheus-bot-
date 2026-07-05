"""Wrapper para API Speack de deobfuscacao."""
import os
import requests
import tempfile

API_URL = "https://proving-staining-monitor.ngrok-free.dev/speack/api/v1/deobf"


def _clean_output(text: str) -> str:
    """Remove o header da API Speack e substitui por header proprio."""
    lines = text.splitlines()
    if lines and "Speack" in lines[0]:
        lines[0] = "-- Deobf by Speack | https://discord.gg/SxfqCrd952"
    return "\n".join(lines)


def deobfuscate(code: str, mode: str = "moonsecv3") -> str:
    """Envia codigo para a API Speack e retorna o deobfuscado.

    Args:
        code: Codigo Lua ofuscado.
        mode: 'moonsecv3', 'moonsecv2', 'wearedevs', 'prometheus'.

    Returns:
        Codigo deobfuscado.
    """
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
        else:
            return f"Erro da API: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def deobfuscate_from_url(url: str, mode: str = "moonsecv3") -> str:
    """Envia URL para a API Speack e retorna o deobfuscado."""
    try:
        response = requests.post(
            API_URL,
            data={"url": url},
            timeout=120
        )

        if response.status_code == 200:
            return _clean_output(response.text)
        else:
            return f"Erro da API: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"
