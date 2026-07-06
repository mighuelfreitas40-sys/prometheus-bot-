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
    "hercules": [
        r"\-\-\s*Hercules",
        r"\bHercules\b",
        r"\bHerc\b",
    ],
    "ironveil": [
        r"\-\-\s*IronVeil",
        r"\bIronVeil\b",
        r"\bIron\b.*\bVeil\b",
    ],
    "luraph": [
        r"\-\-\s*Luraph",
        r"\bLuraph\b",
        r"\bLPH\w+\b",
        r"Luraph",
        r"\.\s*Luraph",
    ],
    "synapsexen": [
        r"\-\-\s*Synapse\s*XEN",
        r"\bSynapse\s*XEN\b",
        r"\bSynapseXen\b",
        r"\bXEN\b",
    ],
    "psu": [
        r"\-\-\s*PSU",
        r"\bPSU\b",
        r"\bProtect\b.*\bSource\b|\bSource\b.*\bProtect\b",
    ],
    "turtle": [
        r"\-\-\s*Turtle",
        r"\bTurtle\b",
        r"\bTurtle\s*Obfuscator\b",
    ],
    "astrial": [
        r"\-\-\s*Astrial",
        r"\bAstrial\b",
        r"\bAstrial\s*Obfuscator\b",
    ],
    "prometheus": [
        r"\-\-\s*Prometheus",
        r"\bPrometheus\b",
        r"\bPrometheus\s*Obfuscator\b",
    ],
    "fii": [
        r"\-\-\s*FII",
        r"\bFII\b",
        r"\bFII\s*Obfuscator\b",
    ],
    "oxygen": [
        r"\-\-\s*Oxygen",
        r"\bOxygen\b",
        r"\bOxygen\s*Obfuscator\b",
    ],
    "swbf": [
        r"\-\-\s*SWBF",
        r"\bSWBF\b",
    ],
    "hydroxide": [
        r"\-\-\s*Hydroxide",
        r"\bHydroxide\b",
    ],
    "sulphur": [
        r"\-\-\s*Sulphur",
        r"\bSulphur\b",
    ],
    "ironbrew": [
        r"\-\-\s*IronBrew",
        r"\bIronBrew\b",
        r"\bIron\b.*\bBrew\b",
    ],
    "moonsecv2": [
        r"\-\-\s*MoonSec\s*V2",
        r"\bMoonSec\s*V2\b",
    ],
    "encrypt": [
        r"\-\-\s*Encrypt",
        r"\bEncrypt\b.*\bObfuscator\b",
    ],
    "aztupbrew": [
        r"\-\-\s*AztupBrew",
        r"\bAztupBrew\b",
        r"\bAztup\b",
    ],
    "rofuscator": [
        r"\-\-\s*RoFuscator",
        r"\bRoFuscator\b",
    ],
    "seal": [
        r"\-\-\s*Seal",
        r"\bSeal\b.*\bObfuscator\b",
    ],
    "vexobfuscator": [
        r"\-\-\s*Vex",
        r"\bVex\b.*\bObfuscator\b",
    ],
    "shield": [
        r"\-\-\s*Shield",
        r"\bShield\b.*\bObfuscator\b",
    ],
    "bubfuscator": [
        r"\-\-\s*Bubfuscator",
        r"\bBubfuscator\b",
    ],
    "cryptic": [
        r"\-\-\s*Cryptic",
        r"\bCryptic\b.*\bObfuscator\b",
    ],
    "darkness": [
        r"\-\-\s*Darkness",
        r"\bDarkness\b.*\bObfuscator\b",
    ],
    "obfuscatorplus": [
        r"\-\-\s*Obfuscator\s*Plus",
        r"\bObfuscator\s*Plus\b",
    ],
    "luaobfuscator": [
        r"\-\-\s*Lua\s*Obfuscator",
        r"\bLua\s*Obfuscator\b",
    ],
    "custom": [
        r"\-\-\s*Custom\s*Obfuscator",
        r"\bCustom\b.*\bObfuscator\b",
    ],
}


def detect_obfuscator(code: str) -> str:
    scores = {}
    for name, patterns in OBF_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, code, re.IGNORECASE))
        scores[name] = score

    if not scores or max(scores.values()) == 0:
        return "unknown"

    return max(scores, key=scores.get)


# Teste com codigo de exemplo
test_code = (
    "-- Luraph v12.4\n"
    "local LPH_JIT = true\n"
    "local LPH_ENCSTR = \"hello\"\n"
    "return (function(...)\n"
    "    local a = \"test\"\n"
    "end)\n"
)

print(detect_obfuscator(test_code))
