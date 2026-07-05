"""Wrapper pro Prometheus Deobfuscator V2 (Lua)."""
import os
import subprocess
import tempfile

V2_PATH = "/app/deob-v2"


def deobfuscate(code: str, trace: str = "off") -> str:
    """Roda o cli.lua do V2 no código fornecido.

    Args:
        code: Código Lua ofuscado.
        trace: Modo de trace ('off', 'prints', 'calls', 'api', 'debug').

    Returns:
        Código deobfuscado.
    """
    if not os.path.exists(V2_PATH):
        raise FileNotFoundError(f"V2 não encontrado em {V2_PATH}")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    out_path = tmp_path.replace(".lua", ".deob.lua")

    try:
        result = subprocess.run(
            [
                "lua5.1",
                os.path.join(V2_PATH, "src", "deob", "cli.lua"),
                tmp_path,
                "--trace", trace,
                "--out", out_path,
                "--pretty"
            ],
            capture_output=True,
            text=True,
            cwd=V2_PATH,
            timeout=60
        )

        if os.path.exists(out_path):
            with open(out_path, "r") as f:
                return f.read()

        if result.stdout:
            return result.stdout
        if result.stderr:
            return f"Erro: {result.stderr}"

        return "Não foi possível deobfuscar."
    finally:
        for p in (tmp_path, out_path):
            if os.path.exists(p):
                os.unlink(p)
