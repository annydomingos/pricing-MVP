import requests
from datetime import date, timedelta

# ── Mapeamento região → cidade → coordenadas Open-Meteo ───────────────────────
REGIAO_COORDS = {
    "Sudeste":      {"cidade": "São Paulo",    "lat": -23.55, "lon": -46.63},
    "Sul":          {"cidade": "Curitiba",     "lat": -25.43, "lon": -49.27},
    "Nordeste":     {"cidade": "Recife",       "lat": -8.05,  "lon": -34.88},
    "Centro-Oeste": {"cidade": "Brasília",     "lat": -15.78, "lon": -47.93},
    "Norte":        {"cidade": "Manaus",       "lat": -3.10,  "lon": -60.02},
}

# ── Jogos hardcoded (Brasileirão, Copa do Brasil, Libertadores) ────────────────
JOGOS = {
    date(2025, 3, 20), date(2025, 3, 22), date(2025, 3, 26),
    date(2025, 3, 29), date(2025, 4, 2),  date(2025, 4, 5),
    date(2025, 4, 9),  date(2025, 4, 12), date(2025, 4, 16),
    date(2025, 4, 19), date(2025, 4, 23), date(2025, 4, 26),
    date(2025, 4, 30), date(2025, 5, 3),  date(2025, 5, 7),
    date(2025, 5, 10), date(2025, 5, 14), date(2025, 5, 17),
}


def buscar_feriados(ano: int) -> set:
    """Busca feriados nacionais via BrasilAPI."""
    try:
        url = f"https://brasilapi.com.br/api/feriados/v1/{ano}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return {date.fromisoformat(f["date"]) for f in resp.json()}
    except Exception as e:
        print(f"⚠️ Erro ao buscar feriados: {e}")
        return set()


def buscar_clima(regiao: str, datas: list[date]) -> dict:
    """Busca previsão de temperatura máxima via Open-Meteo para os próximos dias."""
    coords = REGIAO_COORDS.get(regiao, REGIAO_COORDS["Sudeste"])
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={coords['lat']}&longitude={coords['lon']}"
            f"&daily=temperature_2m_max&timezone=America/Sao_Paulo"
            f"&forecast_days=16"
        )
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()["daily"]
        clima = {}
        for d_str, temp in zip(data["time"], data["temperature_2m_max"]):
            d = date.fromisoformat(d_str)
            if d in datas:
                clima[d] = {"temp_max": temp, "cidade": coords["cidade"]}
        return clima
    except Exception as e:
        print(f"⚠️ Erro ao buscar clima: {e}")
        return {d: {"temp_max": None, "cidade": coords["cidade"]} for d in datas}


def montar_contexto(regiao: str, proximos_7: list[date]) -> list[dict]:
    """Monta o contexto completo de cada dia para o agente."""
    anos = {d.year for d in proximos_7}
    feriados = set()
    for ano in anos:
        feriados |= buscar_feriados(ano)

    clima = buscar_clima(regiao, proximos_7)

    contexto = []
    for d in proximos_7:
        temp = clima.get(d, {}).get("temp_max")
        contexto.append({
            "data": str(d),
            "jogo": d in JOGOS,
            "feriado": d in feriados,
            "temp_max": temp,
            "clima_quente": temp is not None and temp >= 28,
        })

    return contexto