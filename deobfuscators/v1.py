"""Wrapper pro Prometheus Deobfuscator V1 (Python)."""
import os
import re
import subprocess
import tempfile

V1_PATH = "/app/deob-v1"


def deobfuscate(code: str, mode: str = "prometheus") -> str:
    """Roda o pol.py do V1 no código fornecido.

    Args:
        code: Código Lua ofuscado.
        mode: 'prometheus', 'moonsecv3', ou 'moonsecv2'.

    Returns:
        Código deobfuscado.
    """
    if not os.path.exists(V1_PATH):
        raise FileNotFoundError(f"V1 não encontrado em {V1_PATH}")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = V1_PATH

        result = subprocess.run(
            ["python", os.path.join(V1_PATH, "pol.py"), tmp_path],
            capture_output=True,
            text=True,
            cwd=V1_PATH,
            env=env,
            timeout=60
        )

        output_path = tmp_path.replace(".lua", "_deobf.lua")
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                return f.read()

        if result.stdout:
            return result.stdout
        if result.stderr:
            return f"Erro: {result.stderr}"

        return "Não foi possível deobfuscar."
    finally:
        for p in (tmp_path, tmp_path.replace(".lua", "_deobf.lua")):
            if os.path.exists(p):
                os.unlink(p)
