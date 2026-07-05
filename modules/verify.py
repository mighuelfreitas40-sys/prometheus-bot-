"""Detecta qual obfuscador foi usado no código Lua."""
import re

OBF_PATTERNS = {
    "wearedevs": [
        r"wearedevs\.net",
        r"return\s*\(function\s*\(\.\.\.\)",
        r"local\s+\w+\s*=\s*\{[^}]*\"[^\"]*\"[^}]*\}",
        r"string\.sub|table\.concat|math\.floor",
    ],
    "moonsecv3": [
        r"\-\-\s*MoonSec\s*V3",
        r"\bMoonSec\b",
        r"\bEncode\b|\bDecode\b",
    ],
    "moonsecv2": [
        r"\-\-\s*MoonSec\s*V2",
        r"\bMoonSec\b",
        r"\bencrypt\b|\bdecrypt\b",
    ],
}


def detect_obfuscator(code: str) -> str:
    """Retorna o nome do obfuscador detectado ou 'unknown'."""
    scores = {}
    for name, patterns in OBF_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, code, re.IGNORECASE))
        scores[name] = score

    if not scores or max(scores.values()) == 0:
        return "unknown"

    return max(scores, key=scores.get)
