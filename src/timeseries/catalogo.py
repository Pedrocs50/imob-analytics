from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SerieMacro:
    """Definicao de uma serie externa. `tipo` diz o que o valor representa:
    taxa (variacao % no periodo), indice, nivel (valor absoluto) ou saldo."""

    id: str
    fonte: str  # BCB | IPEA | IBGE_SIDRA
    codigo: str  # SGS, SERCODIGO ou tabela/variavel do SIDRA
    nome: str
    unidade: str
    tipo: str
    frequencia: str  # M mensal | Q trimestral
    agregacao: str | None  # como levar dados diarios ao mes: last | mean | sum
    # Convencao: a linha do mes t dos paineis = conhecimento disponivel ate o ULTIMO DIA do
    # mes t. defasagem_meses = meses entre o ultimo mes do periodo de referencia e o mes do
    # calendario em que o valor e divulgado (0 = divulgado ate o fim do proprio mes).
    # Fontes consultadas: docs/SERIES_TEMPORAIS.md. "estimada" = ainda nao confirmada.
    defasagem_meses: int
    faixa: tuple[float, float]  # valores plausiveis; fora disso a validacao falha
    sidra_path: str | None = None
    sidra_variavel: str | None = None
    diaria: bool = False  # exige janelas de ate 10 anos no SGS
    descartar_mes_corrente: bool = False  # serie calculada sobre o mes: o mes em curso e parcial


SERIES: tuple[SerieMacro, ...] = (
    # --- BCB / SGS -------------------------------------------------------
    SerieMacro("bcb_selic_meta", "BCB", "432", "Meta Selic", "% a.a.", "nivel", "M", "last", 0, (0, 50), diaria=True, descartar_mes_corrente=True),
    SerieMacro("bcb_selic_mes", "BCB", "4390", "Selic acumulada no mes", "% a.m.", "taxa", "M", None, 0, (0, 5), descartar_mes_corrente=True),
    SerieMacro("bcb_ipca", "BCB", "433", "IPCA variacao mensal", "% a.m.", "taxa", "M", None, 1, (-2, 5)),  # IBGE: divulgado 9-12 dias apos o fim do mes
    SerieMacro("bcb_igpm", "BCB", "189", "IGP-M variacao mensal", "% a.m.", "taxa", "M", None, 0, (-5, 10)),
    SerieMacro("bcb_incc", "BCB", "192", "INCC-M variacao mensal", "% a.m.", "taxa", "M", None, 0, (-2, 5)),
    SerieMacro("bcb_ptax", "BCB", "3698", "Dolar (venda) media mensal", "R$/US$", "nivel", "M", None, 0, (1, 10), descartar_mes_corrente=True),
    SerieMacro("bcb_ibcbr", "BCB", "24363", "IBC-Br dessazonalizado", "indice", "indice", "M", None, 2, (30, 300)),
    SerieMacro("bcb_credimob_saldo", "BCB", "20612", "Saldo credito imobiliario PF (direcionado)", "R$ milhoes", "saldo", "M", None, 1, (1_000, 10_000_000)),
    SerieMacro("bcb_credimob_juros_mercado", "BCB", "25497", "Juros financ. imobiliario - taxas de mercado", "% a.m.", "taxa", "M", None, 1, (0, 5)),
    SerieMacro("bcb_credimob_juros_regulada", "BCB", "25498", "Juros financ. imobiliario - taxas reguladas", "% a.m.", "taxa", "M", None, 1, (0, 5)),
    # --- IPEA ------------------------------------------------------------
    SerieMacro("ipea_icc", "IPEA", "FCESP12_IIC12", "Confianca do consumidor (Fecomercio-SP)", "indice", "indice", "M", None, 1, (20, 250)),  # Fecomercio: divulgado em meados do mes seguinte
    SerieMacro("ipea_desocupacao_br_mensal", "IPEA", "PNADC12_TDESOCM12", "Desocupacao Brasil - mensalizada", "%", "taxa", "M", None, 2, (1, 25)),
    # --- IBGE / SIDRA (PNAD Continua, trimestral) --------------------------
    SerieMacro(
        "ibge_desocupacao_sp", "IBGE_SIDRA", "4099/4099", "Taxa de desocupacao - SP", "%", "taxa", "Q", None, 2, (1, 25),  # IBGE: 44-51 dias apos o fim do trimestre
       
        sidra_path="t/4099/n3/35/v/4099/p/all", sidra_variavel="4099",
    ),
    SerieMacro(
        "ibge_renda_sp", "IBGE_SIDRA", "5436/5933", "Rendimento medio real habitual (todos os trabalhos) - SP", "R$", "nivel", "Q", None, 2, (1_000, 20_000),
        sidra_path="t/5436/n3/35/v/5933/p/all/c2/6794", sidra_variavel="5933",
    ),
)

SERIES_POR_ID = {s.id: s for s in SERIES}

# Situacao da confirmacao de cada defasagem (detalhes e URLs em docs/SERIES_TEMPORAIS.md)
CONFIRMADA = "confirmada"
ESTIMADA = "estimada (nao confirmada)"
FONTES_DEFASAGEM: dict[str, tuple[str, str]] = {
    "bcb_ipca": (CONFIRMADA, "calendario oficial do IBGE: divulgado 9 a 12 dias apos o fim do mes"),
    "ipea_icc": (CONFIRMADA, "Fecomercio-SP: jun/2025 divulgado em 14/07/2025 e fev/2026 em 16/03/2026"),
    "ibge_desocupacao_sp": (CONFIRMADA, "calendario oficial do IBGE (PNAD Continua trimestral): 44 a 51 dias apos o fim do trimestre"),
    "ibge_renda_sp": (CONFIRMADA, "calendario oficial do IBGE (PNAD Continua trimestral): 44 a 51 dias apos o fim do trimestre"),
    "fipezap": (CONFIRMADA, "evidencia indireta: relatorios de referencia t publicados no mes t+1; sem calendario oficial legivel"),
    "ipea_desocupacao_br_mensal": (ESTIMADA, "PNAD mensal sai 26-33 dias apos o mes (IBGE); a mensalizacao do IPEA e posterior; 2 e conservador"),
    "bcb_ibcbr": (ESTIMADA, "publicacao do BCB cerca de 45 dias apos o mes"),
    "bcb_credimob_saldo": (ESTIMADA, "estatisticas de credito do BCB no mes seguinte"),
    "bcb_credimob_juros_mercado": (ESTIMADA, "estatisticas de credito do BCB no mes seguinte"),
    "bcb_credimob_juros_regulada": (ESTIMADA, "estatisticas de credito do BCB no mes seguinte"),
    "bcb_igpm": (ESTIMADA, "FGV divulga no fim do proprio mes"),
    "bcb_incc": (ESTIMADA, "FGV divulga no fim do proprio mes"),
    "bcb_selic_meta": (ESTIMADA, "decisao do Copom e conhecida no ato"),
    "bcb_selic_mes": (ESTIMADA, "acumulada no mes, conhecida no ultimo dia do mes"),
    "bcb_ptax": (ESTIMADA, "media mensal conhecida no ultimo dia do mes"),
}
