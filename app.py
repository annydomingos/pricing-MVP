import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv
from agentes.previsor import agente_previsor
from apis.contexto import montar_contexto
import os

load_dotenv()

st.set_page_config(page_title="Previsão de Volume", page_icon="📦", layout="wide")

st.title("📦 MVP — Previsão de Volume de Vendas")
st.markdown("Selecione os filtros para receber a previsão dos **próximos 7 dias**.")

# ── Carrega Excels ─────────────────────────────────────────────────────────────
@st.cache_data
def carregar_dados():
    for f in ["historico_vendas.xlsx", "imc.xlsx"]:
        if not os.path.exists(f):
            st.error(f"Arquivo {f} não encontrado. Rode: python gerar_dados.py")
            st.stop()
    df = pd.read_excel("historico_vendas.xlsx", parse_dates=["data"])
    df_imc = pd.read_excel("imc.xlsx", parse_dates=["data"])
    df["data"] = df["data"].dt.date
    df_imc["data"] = df_imc["data"].dt.date
    return df, df_imc

df, df_imc = carregar_dados()

# ── Filtros multiselect ────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    skus = st.multiselect(
        "🍺 SKU",
        options=sorted(df["sku"].unique()),
        default=sorted(df["sku"].unique()),
        key="skus"
    )

with col2:
    regioes = st.multiselect(
        "📍 Região",
        options=sorted(df["regiao"].unique()),
        default=sorted(df["regiao"].unique()),
        key="regioes"
    )

with col3:
    redes = st.multiselect(
        "🏪 Rede",
        options=sorted(df["rede"].unique()),
        default=sorted(df["rede"].unique()),
        key="redes"
    )

if not skus or not regioes or not redes:
    st.warning("Selecione ao menos um valor em cada filtro.")
    st.stop()

# ── Botão de previsão ──────────────────────────────────────────────────────────
if st.button("🔮 Gerar Previsão", type="primary"):

    hoje = date.today()
    proximos_7 = [hoje + timedelta(days=i+1) for i in range(7)]

    # Busca contexto externo uma única vez por região
    contextos_por_regiao = {}
    with st.spinner("🌐 Buscando feriados e clima..."):
        for regiao in regioes:
            contextos_por_regiao[regiao] = montar_contexto(regiao, proximos_7)

    resultados = []
    total_combinacoes = len(skus) * len(regioes) * len(redes)
    progresso = st.progress(0, text="Gerando previsões...")
    i = 0

    for sku in skus:
        for regiao in regioes:
            for rede in redes:

                # Filtra histórico
                df_filtrado = df[
                    (df["sku"] == sku) &
                    (df["regiao"] == regiao) &
                    (df["rede"] == rede)
                ].sort_values("data")

                if df_filtrado.empty:
                    i += 1
                    continue

                # Estatísticas
                df_30 = df_filtrado.tail(30)
                media  = int(df_30["quantidade_vendida"].mean())
                pico   = int(df_30["quantidade_vendida"].max())
                minimo = int(df_30["quantidade_vendida"].min())

                # Histórico recente
                historico_recente = (
                    df_filtrado.tail(7)[["data", "quantidade_vendida"]]
                    .assign(data=lambda x: x["data"].astype(str))
                    .to_dict(orient="records")
                )

                # IMC
                contexto = contextos_por_regiao[regiao].copy()
                imc_periodo = df_imc[
                    (df_imc["marca"] == sku) &
                    (df_imc["data"].isin(proximos_7))
                ].set_index("data")["imc"].to_dict()
                for dia in contexto:
                    d = date.fromisoformat(dia["data"])
                    dia["imc"] = int(imc_periodo.get(d, 0))

                # Prompt
                prompt = f"""
SKU: {sku}
Região: {regiao}
Rede: {rede}

## Resumo dos últimos 30 dias
- Média diária: {media} unidades
- Pico: {pico} unidades
- Mínimo: {minimo} unidades

## Histórico recente (últimos 7 dias)
{historico_recente}

## Contexto dos próximos 7 dias
{contexto}
"""
                resposta = agente_previsor.run_sync(prompt)
                resultado = resposta.output

                resultados.append({
                    "sku": sku,
                    "regiao": regiao,
                    "rede": rede,
                    "previsao": resultado,
                })

                i += 1
                progresso.progress(i / total_combinacoes, text=f"Gerando previsão: {sku} | {regiao} | {rede}")

    progresso.empty()
    st.session_state.resultados = resultados

# ── Exibe resultados ───────────────────────────────────────────────────────────
if "resultados" in st.session_state and st.session_state.resultados:
    resultados = st.session_state.resultados

    st.divider()
    st.subheader(f"📊 {len(resultados)} combinações previstas")

    # Tabela consolidada
    linhas = []
    for r in resultados:
        for dia in r["previsao"].previsao_por_dia:
            linhas.append({
                "SKU": r["sku"],
                "Região": r["regiao"],
                "Rede": r["rede"],
                "Data": dia["data"],
                "Volume Previsto": dia["volume_previsto"],
            })

    df_consolidado = pd.DataFrame(linhas)

    st.subheader("📋 Tabela Consolidada")
    st.dataframe(df_consolidado, use_container_width=True)

    # Gráfico consolidado por data
    st.subheader("📈 Volume Total por Dia")
    df_por_data = df_consolidado.groupby("Data")["Volume Previsto"].sum().reset_index()
    st.bar_chart(df_por_data.set_index("Data"))

    # Detalhe por combinação
    st.divider()
    st.subheader("🔍 Detalhes por Combinação")
    for r in resultados:
        with st.expander(f"🍺 {r['sku']} | 📍 {r['regiao']} | 🏪 {r['rede']}"):
            st.info(r["previsao"].previsao_narrativa)
            for dia in r["previsao"].previsao_por_dia:
                imc_label = " 📣 IMC ativo" if dia.get("imc") == 1 else ""
                st.markdown(f"**{dia['data']}** — {dia['volume_previsto']} unidades{imc_label}")
                st.caption(dia["justificativa"])

