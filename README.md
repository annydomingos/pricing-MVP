# 📦 MVP — Previsão de Volume de Vendas

Sistema inteligente de previsão de demanda e alocação de budget promocional para o setor de bebidas, desenvolvido com agentes de IA usando `pydantic-ai` e interface em `Streamlit`. Desenvolvido em 3h.

---

## 🎯 Objetivo

Apoiar Gerentes de Negócio na tomada de decisão sobre **onde e quanto investir em promoção**, com base em:
- Histórico de vendas por SKU, região e rede
- Variáveis externas (jogos de futebol, feriados, clima)
- Campanhas de marketing ativas (IMC)

---

## 🏗️ Arquitetura

O projeto é composto por dois agentes de IA especializados:

**Agente Previsor**
Analisa o histórico de vendas e o contexto dos próximos 7 dias para gerar uma previsão de volume dia a dia, com justificativa para cada estimativa.

**Agente Alocador**
Recebe o budget total informado pelo usuário e distribui entre as combinações de SKU/região/rede, priorizando oportunidades com base no volume previsto, eventos externos e campanhas ativas.

---

## 📊 Variáveis Consideradas

| Variável | Fonte | Impacto estimado |
|---|---|---|
| Histórico de vendas | Excel (baseline) | Volume base |
| Jogos de futebol | Hardcoded (Brasileirão, Copa do Brasil, Libertadores) | +15% a +35% |
| Feriados nacionais | BrasilAPI (gratuita) | +20% a +40% |
| Clima (temperatura) | Open-Meteo (gratuita) | +10% a +25% |
| IMC ativo | Excel imc.xlsx | +25% |
| Promoção histórica | Excel baseline | Considerado na média |

---

## 🗂️ Estrutura do Projeto
```
pricing-MVP/
├── agentes/
│   ├── __init__.py
│   ├── previsor.py        # Agente de previsão de volume
│   └── alocador.py        # Agente de alocação de budget
├── apis/
│   ├── __init__.py
│   └── contexto.py        # Integração BrasilAPI + Open-Meteo + jogos
├── gerar_dados.py         # Gerador de dados fake (rode uma vez)
├── app.py                 # Interface Streamlit
├── historico_vendas.xlsx  # Gerado por gerar_dados.py
├── imc.xlsx               # Gerado por gerar_dados.py
├── requirements.txt
└── .env                   # Não versionado
```

---

## ⚙️ Instalação

**1. Clone o repositório**
```bash
git clone https://github.com/seu-usuario/pricing-MVP.git
cd pricing-MVP
```

**2. Instale as dependências**
```bash
pip install -r requirements.txt
```

**3. Configure o `.env`**
```bash
OPENROUTER_API_KEY=sua_chave_aqui
```
Obtenha sua chave gratuita em [openrouter.ai](https://openrouter.ai)

**4. Gere os dados fake**
```bash
python gerar_dados.py
```

**5. Rode o app**
```bash
streamlit run app.py
```

---

## 🚀 Como Usar

**Step 1 — Filtros**
Selecione os SKUs, regiões e redes que deseja analisar. É possível selecionar múltiplos valores em cada filtro.

**Step 2 — Previsão**
Clique em `🔮 Gerar Previsão`. O sistema irá:
- Buscar feriados via BrasilAPI
- Buscar previsão climática via Open-Meteo
- Gerar a previsão de volume para cada combinação selecionada

**Step 3 — Resultados**
Visualize a tabela consolidada, o gráfico comparativo entre histórico real e previsão, e os detalhes por combinação. Faça o download em Excel.

**Step 4 — Alocação de Budget**
Clique em `💰 Ir para Alocação de Budget`, informe o valor total disponível e clique em `🚀 Gerar Alocação`. O agente distribui o budget entre as combinações e gera um relatório completo para download.

---

## 🍺 SKUs Disponíveis

- Guaraná
- Original
- Skol
- Stella Pure Gold

---

## 📍 Regiões e Cidades de Referência para Clima

| Região | Cidade |
|---|---|
| Sudeste | São Paulo |
| Sul | Curitiba |
| Nordeste | Recife |
| Centro-Oeste | Brasília |
| Norte | Manaus |

---

## 🔮 Próximos Passos

- Conectar a dados reais de histórico de vendas
- Validação da previsão vs realizado
- Integração com API de futebol para calendário automático
- Histórico de alocações para comparação entre períodos
- Autenticação para acesso multi-usuário

---

## 🛠️ Tecnologias

- [pydantic-ai](https://ai.pydantic.dev/) — framework de agentes de IA
- [Streamlit](https://streamlit.io/) — interface web
- [OpenRouter](https://openrouter.ai/) — acesso ao modelo GPT-4o-mini
- [BrasilAPI](https://brasilapi.com.br/) — feriados nacionais
- [Open-Meteo](https://open-meteo.com/) — previsão climática gratuita
- [Pandas](https://pandas.pydata.org/) — manipulação de dados
- [openpyxl](https://openpyxl.readthedocs.io/) — geração de Excel