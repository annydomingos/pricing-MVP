import pandas as pd
import numpy as np
from datetime import date, timedelta

np.random.seed(42)

SKUS     = ["Guaraná", "Original", "Skol", "Stella Pure Gold"]
REGIOES  = ["Sul", "Sudeste", "Nordeste", "Centro-Oeste", "Norte"]
REDES    = ["Atacadão", "Assaí", "Carrefour", "Extra", "Mercadão"]

FERIADOS = {
    date(2024, 11, 2), date(2024, 11, 15), date(2024, 11, 20),
    date(2024, 12, 25), date(2025, 1, 1), date(2025, 2, 28), date(2025, 3, 1),
}

REGIOES_QUENTES = ["Nordeste", "Sudeste"]

VOLUME_BASE = {
    "Guaraná": 300,
    "Original": 250,
    "Skol": 400,
    "Stella Pure Gold": 150,
}

def tem_jogo(d: date) -> bool:
    return d.weekday() in [2, 5, 6]

def fator_clima(regiao: str, d: date) -> float:
    if regiao in REGIOES_QUENTES and d.month in [12, 1, 2, 3]:
        return np.random.uniform(1.10, 1.25)
    return 1.0

def gerar_historico():
    inicio = date(2024, 11, 1)
    registros = []

    for dias in range(90):
        d = inicio + timedelta(days=dias)
        for sku in SKUS:
            for regiao in REGIOES:
                for rede in REDES:
                    volume = VOLUME_BASE[sku]
                    if tem_jogo(d):
                        volume *= np.random.uniform(1.15, 1.35)
                    if d in FERIADOS:
                        volume *= np.random.uniform(1.20, 1.40)
                    volume *= fator_clima(regiao, d)
                    perc_promocao = np.random.choice(
                        [0, 0, 0, 10, 20, 30, 40],
                        p=[0.4, 0.2, 0.1, 0.1, 0.1, 0.05, 0.05]
                    )
                    volume *= 1 + (perc_promocao / 100)
                    volume *= np.random.uniform(0.90, 1.10)
                    registros.append({
                        "data": d,
                        "sku": sku,
                        "regiao": regiao,
                        "rede": rede,
                        "quantidade_vendida": int(volume),
                        "perc_promocao": perc_promocao,
                    })

    df = pd.DataFrame(registros)
    df.to_excel("historico_vendas.xlsx", index=False)
    print(f"✅ historico_vendas.xlsx gerado com {len(df)} registros")
    return df

def gerar_imc():
    inicio = date(2024, 11, 1)
    registros = []

    for dias in range(90 + 7):  # histórico + próximos 7 dias
        d = inicio + timedelta(days=dias)
        for sku in SKUS:
            # IMC = 1 em períodos específicos por marca (simula campanhas)
            imc = 0
            if sku == "Guaraná" and d.month in [12, 1]:
                imc = 1
            elif sku == "Skol" and d.month in [2, 3]:
                imc = 1
            elif sku == "Original" and d.month == 11:
                imc = 1
            elif sku == "Stella Pure Gold" and d.month in [12, 2]:
                imc = 1
            registros.append({
                "data": d,
                "marca": sku,
                "imc": imc,
            })

    df = pd.DataFrame(registros)
    df.to_excel("imc.xlsx", index=False)
    print(f"✅ imc.xlsx gerado com {len(df)} registros")
    return df


if __name__ == "__main__":
    gerar_historico()
    gerar_imc()