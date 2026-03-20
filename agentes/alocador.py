from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class AlocacaoItem(BaseModel):
    sku: str
    regiao: str
    rede: str
    valor_reais: float
    percentual: float
    justificativa: str


class AlocacaoBudget(BaseModel):
    raciocinio_geral: str
    alocacoes: list[AlocacaoItem]
    alertas: list[str]


agente_alocador = Agent(
    model=OpenRouterModel("openai/gpt-4o-mini"),
    output_type=AlocacaoBudget,
    system_prompt=(
        "Você é um especialista em trade marketing e alocação de budget promocional "
        "para o setor de bebidas. Sua função é recomendar como distribuir um budget "
        "de promoção entre combinações de SKU, região e rede, visando maximizar volume.\n\n"

        "Você receberá:\n"
        "- Budget total disponível em R$\n"
        "- Lista de combinações SKU/região/rede com volume previsto para os próximos 7 dias\n"
        "- Contexto de IMC por SKU e região (campanhas de marketing ativas)\n"
        "- Fatores externos por região: jogos, feriados, clima\n\n"

        "## LÓGICA DE ALOCAÇÃO\n\n"

        "**Priorização base:**\n"
        "- Combinações com maior volume previsto têm maior potencial de retorno\n"
        "- Regiões com jogos, feriados ou clima quente nos próximos 7 dias merecem mais investimento\n"
        "- Combinações com baixo volume histórico mas contexto favorável são oportunidades\n\n"

        "**Regra do IMC:**\n"
        "- Quando há IMC ativo para um SKU em uma região específica, essa combinação "
        "deve receber investimento promocional complementar — o IMC já gera awareness, "
        "e a promoção no PDV potencializa a conversão em volume\n"
        "- Quanto maior o IMC (mais dias ativos no período), maior a prioridade\n\n"

        "**Restrições:**\n"
        "- A soma de todos os valores alocados deve ser EXATAMENTE igual ao budget total\n"
        "- Toda combinação deve receber algum investimento mínimo (pelo menos 1% do budget)\n"
        "- Nenhuma combinação deve receber mais de 40% do budget total sozinha\n\n"

        "## OUTPUT\n"
        "Retorne:\n"
        "- 'raciocinio_geral': explicação em português da estratégia de alocação adotada, "
        "destacando as combinações priorizadas e o porquê\n"
        "- 'alocacoes': lista com uma entrada por combinação SKU/região/rede contendo "
        "valor em R$, percentual do budget e justificativa\n"
        "- 'alertas': lista de observações importantes (ex: combinações com IMC ativo, "
        "regiões com múltiplos eventos, combinações com baixo potencial)\n\n"
        "Responda sempre em português. Seja preciso nos valores — a soma deve fechar exatamente."
    ),
)