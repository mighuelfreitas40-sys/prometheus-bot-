REVEA_DUMP_URL = "https://web-production-eb197.up.railway.app/api/revea"

def deobfuscate_revea_dump(code: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        with open(tmp_path, "rb") as f:
            response = requests.post(
                REVEA_DUMP_URL,
                files={"file": f},
                timeout=120
            )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["code"]
            return f"Erro da API: {data.get('error', 'unknown')}"
        return f"Erro da API: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def deobfuscate_revea_dump_from_url(url: str) -> str:
    try:
        response = requests.post(
            REVEA_DUMP_URL,
            data={"url": url},
            timeout=120
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["code"]
            return f"Erro da API: {data.get('error', 'unknown')}"
        return f"Erro da API: HTTP {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Erro de conexao: {e}"
