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
st.markdown("Selecione o produto, região e rede para receber a previsão dos **próximos 7 dias**.")

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

# ── Filtros ────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    sku = st.selectbox("🍺 SKU", sorted(df["sku"].unique()), key="sku")
with col2:
    regiao = st.selectbox("📍 Região", sorted(df["regiao"].unique()), key="regiao")
with col3:
    rede = st.selectbox("🏪 Rede", sorted(df["rede"].unique()), key="rede")

# ── Botão de previsão ──────────────────────────────────────────────────────────
if st.button("🔮 Gerar Previsão", type="primary"):

    # Filtra histórico
    df_filtrado = df[
        (df["sku"] == sku) &
        (df["regiao"] == regiao) &
        (df["rede"] == rede)
    ].sort_values("data")

    if df_filtrado.empty:
        st.error("Nenhum dado encontrado para essa combinação.")
        st.stop()

    # Estatísticas dos últimos 30 dias
    df_30 = df_filtrado.tail(30)
    media  = int(df_30["quantidade_vendida"].mean())
    pico   = int(df_30["quantidade_vendida"].max())
    minimo = int(df_30["quantidade_vendida"].min())

    # Histórico recente — últimos 7 dias
    historico_recente = (
        df_filtrado.tail(7)[["data", "quantidade_vendida"]]
        .assign(data=lambda x: x["data"].astype(str))
        .to_dict(orient="records")
    )

    # Próximos 7 dias
    hoje = date.today()
    proximos_7 = [hoje + timedelta(days=i+1) for i in range(7)]

    # Contexto externo (feriados API + clima API + jogos hardcoded)
    with st.spinner("🌐 Buscando feriados e clima..."):
        contexto = montar_contexto(regiao, proximos_7)

    # IMC dos próximos 7 dias para o SKU selecionado
    imc_periodo = df_imc[
        (df_imc["marca"] == sku) &
        (df_imc["data"].isin(proximos_7))
    ].set_index("data")["imc"].to_dict()

    # Adiciona IMC ao contexto
    for dia in contexto:
        d = date.fromisoformat(dia["data"])
        dia["imc"] = int(imc_periodo.get(d, 0))

    # Monta prompt
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

    with st.spinner("🤖 Agente gerando previsão..."):
        resposta = agente_previsor.run_sync(prompt)
        resultado = resposta.output

    # ── Resultados ─────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Análise Geral")
    st.info(resultado.previsao_narrativa)

    st.subheader("📅 Previsão Dia a Dia")
    for dia in resultado.previsao_por_dia:
        imc_label = " 📣 IMC ativo" if dia.get("imc") == 1 else ""
        with st.expander(f"📆 {dia['data']} — {dia['volume_previsto']} unidades{imc_label}"):
            st.write(dia["justificativa"])

    st.subheader("📊 Resumo em Tabela")
    df_prev = pd.DataFrame(resultado.previsao_por_dia)
    df_prev.columns = ["Data", "Volume Previsto", "Justificativa"]
    st.dataframe(df_prev[["Data", "Volume Previsto"]], use_container_width=True)

    st.subheader("📈 Volume Previsto — Próximos 7 dias")
    st.bar_chart(df_prev.set_index("Data")["Volume Previsto"])

