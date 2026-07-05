"""Wrapper pro Prometheus Deobfuscator V2 (Lua) com pós-processamento de escapes."""
import os
import re
import subprocess
import tempfile

V2_PATH = "/app/deob-v2"


def _decode_all_escapes(code: str) -> str:
    """Decodifica todos os tipos de escapes numéricos em strings Lua."""
    code = re.sub(r'\\\\(\\d{1,3})', lambda m: chr(int(m.group(1))), code)
    code = re.sub(r'\\\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), code)
    return code


def deobfuscate(code: str, trace: str = "off") -> str:
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
                raw = f.read()
            return _decode_all_escapes(raw)

        if result.stdout:
            return _decode_all_escapes(result.stdout)
        if result.stderr:
            return f"Erro: {result.stderr}"

        return "Não foi possível deobfuscar."
    finally:
        for p in (tmp_path, out_path):
            if os.path.exists(p):
                os.unlink(p)
