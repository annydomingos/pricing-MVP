import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv
from agentes.previsor import agente_previsor
from agentes.alocador import agente_alocador
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
    st.session_state.pop("resultados", None)
    st.session_state.pop("resultado_alocacao", None)

    hoje = date.today()
    proximos_7 = [hoje + timedelta(days=i+1) for i in range(7)]

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
                df_filtrado = df[
                    (df["sku"] == sku) &
                    (df["regiao"] == regiao) &
                    (df["rede"] == rede)
                ].sort_values("data")

                if df_filtrado.empty:
                    i += 1
                    continue

                df_30 = df_filtrado.tail(30)
                media  = int(df_30["quantidade_vendida"].mean())
                pico   = int(df_30["quantidade_vendida"].max())
                minimo = int(df_30["quantidade_vendida"].min())

                historico_recente = (
                    df_filtrado.tail(7)[["data", "quantidade_vendida"]]
                    .assign(data=lambda x: x["data"].astype(str))
                    .to_dict(orient="records")
                )

                contexto = contextos_por_regiao[regiao].copy()
                imc_periodo = df_imc[
                    (df_imc["marca"] == sku) &
                    (df_imc["data"].isin(proximos_7))
                ].set_index("data")["imc"].to_dict()
                for dia in contexto:
                    d = date.fromisoformat(dia["data"])
                    dia["imc"] = int(imc_periodo.get(d, 0))

                imc_ativo = sum(imc_periodo.values()) > 0

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
                    "media_historica": media,
                    "imc_ativo": imc_ativo,
                    "imc_dias": sum(imc_periodo.values()),
                    "contexto": contexto,
                    "previsao": resultado,
                })

                i += 1
                progresso.progress(i / total_combinacoes, text=f"{sku} | {regiao} | {rede}")

    progresso.empty()
    st.session_state.resultados = resultados
    st.session_state.contextos_por_regiao = contextos_por_regiao

# ── Exibe resultados da previsão ───────────────────────────────────────────────
if "resultados" in st.session_state and st.session_state.resultados:
    resultados = st.session_state.resultados

    st.divider()
    st.subheader(f"📊 {len(resultados)} combinações previstas")

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

    st.subheader("📈 Volume Total por Dia")
    df_por_data = df_consolidado.groupby("Data")["Volume Previsto"].sum().reset_index()
    st.bar_chart(df_por_data.set_index("Data"))

    st.divider()
    st.subheader("🔍 Detalhes por Combinação")
    for r in resultados:
        imc_badge = " 📣 IMC ativo" if r["imc_ativo"] else ""
        with st.expander(f"🍺 {r['sku']} | 📍 {r['regiao']} | 🏪 {r['rede']}{imc_badge}"):
            st.info(r["previsao"].previsao_narrativa)
            for dia in r["previsao"].previsao_por_dia:
                imc_label = " 📣" if dia.get("imc") == 1 else ""
                st.markdown(f"**{dia['data']}** — {dia['volume_previsto']} unidades{imc_label}")
                st.caption(dia["justificativa"])

    # ── Botão alocação de budget ───────────────────────────────────────────────
    st.divider()
    if st.button("💰 Ir para Alocação de Budget", type="primary"):
        st.session_state.mostrar_alocacao = True

# ── Step de alocação de budget ─────────────────────────────────────────────────
if st.session_state.get("mostrar_alocacao"):
    st.divider()
    st.subheader("💰 Alocação de Budget Promocional")
    st.markdown("Informe o budget total disponível para distribuir entre as combinações.")

    budget = st.number_input(
        "Budget total (R$)",
        min_value=1000.0,
        max_value=10_000_000.0,
        value=100_000.0,
        step=1000.0,
        format="%.2f",
        key="budget_input"
    )

    if st.button("🚀 Gerar Alocação", type="primary"):
        resultados = st.session_state.resultados

        # Monta resumo das combinações para o agente
        resumo_combinacoes = []
        for r in resultados:
            volume_total_previsto = sum(
                d["volume_previsto"] for d in r["previsao"].previsao_por_dia
            )
            resumo_combinacoes.append({
                "sku": r["sku"],
                "regiao": r["regiao"],
                "rede": r["rede"],
                "volume_previsto_7d": volume_total_previsto,
                "media_historica_diaria": r["media_historica"],
                "imc_ativo": r["imc_ativo"],
                "imc_dias_ativos": r["imc_dias"],
                "eventos": {
                    "jogos": sum(1 for d in r["contexto"] if d.get("jogo")),
                    "feriados": sum(1 for d in r["contexto"] if d.get("feriado")),
                    "dias_quentes": sum(1 for d in r["contexto"] if d.get("clima_quente")),
                }
            })

        prompt_alocacao = f"""
Budget total disponível: R$ {budget:,.2f}
Número de combinações: {len(resumo_combinacoes)}

## Combinações SKU/Região/Rede com contexto completo:
{resumo_combinacoes}

Distribua o budget de R$ {budget:,.2f} entre todas as {len(resumo_combinacoes)} combinações acima.
Lembre-se: a soma dos valores alocados deve ser EXATAMENTE R$ {budget:,.2f}.
"""

        with st.spinner("🤖 Agente alocando budget..."):
            resposta = agente_alocador.run_sync(prompt_alocacao)
            st.session_state.resultado_alocacao = resposta.output

# ── Exibe resultado da alocação ────────────────────────────────────────────────
if "resultado_alocacao" in st.session_state:
    alocacao = st.session_state.resultado_alocacao

    st.divider()
    st.subheader("📊 Resultado da Alocação")
    st.info(alocacao.raciocinio_geral)

    if alocacao.alertas:
        st.subheader("⚠️ Alertas")
        for alerta in alocacao.alertas:
            st.warning(alerta)

    # Tabela de alocação
    st.subheader("💵 Alocação por Combinação")
    df_alocacao = pd.DataFrame([
        {
            "SKU": a.sku,
            "Região": a.regiao,
            "Rede": a.rede,
            "Valor (R$)": f"R$ {a.valor_reais:,.2f}",
            "% do Budget": f"{a.percentual:.1f}%",
            "Justificativa": a.justificativa,
        }
        for a in alocacao.alocacoes
    ])
    st.dataframe(df_alocacao, use_container_width=True)

    # Gráfico por SKU
    st.subheader("📈 Budget por SKU")
    df_graf_sku = pd.DataFrame([
        {"SKU": a.sku, "Valor": a.valor_reais} for a in alocacao.alocacoes
    ]).groupby("SKU")["Valor"].sum()
    st.bar_chart(df_graf_sku)

    # Gráfico por Região
    st.subheader("📈 Budget por Região")
    df_graf_reg = pd.DataFrame([
        {"Região": a.regiao, "Valor": a.valor_reais} for a in alocacao.alocacoes
    ]).groupby("Região")["Valor"].sum()
    st.bar_chart(df_graf_reg)

    # Total alocado
    total = sum(a.valor_reais for a in alocacao.alocacoes)
    st.metric("💰 Total Alocado", f"R$ {total:,.2f}")

