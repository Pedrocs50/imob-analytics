from __future__ import annotations

# ---------------------------------------------------------------------------
# Codigos territoriais IBGE
# ---------------------------------------------------------------------------
JACAREI_IBGE = "3524402"
SP_UF_IBGE   = "35"

# ---------------------------------------------------------------------------
# Series BCB/SGS  (sem token)
#
#  432  – Meta Selic                     (diária  → last do mês)
#  433  – IPCA variação mensal            (mensal)
# 3698  – Dólar PTAX venda média mensal   (mensal)
# 24363 – IBC-Br índice de atividade      (mensal, com ajuste sazonal)
# ---------------------------------------------------------------------------
SERIES_BCB = [
    {
        "ativo": True,
        "fonte": "BCB",
        "codigo_serie": "432",
        "nome_serie": "Meta Selic (% a.a.)",
        "unidade": "% a.a.",
        "frequencia_origem": "D",
        "agregacao_mensal": "last",
        "data_inicial": "2008-01-01",
    },
    {
        "ativo": True,
        "fonte": "BCB",
        "codigo_serie": "433",
        "nome_serie": "IPCA variacao mensal (%)",
        "unidade": "% m/m",
        "frequencia_origem": "M",
        "agregacao_mensal": "last",
        "data_inicial": "2008-01-01",
    },
    # ── NOVO ──────────────────────────────────────────────────────────────
    {
        "ativo": True,
        "fonte": "BCB",
        "codigo_serie": "3698",
        "nome_serie": "Dolar PTAX venda - media mensal (R$/US$)",
        "unidade": "R$/US$",
        "frequencia_origem": "M",
        "agregacao_mensal": "last",
        "data_inicial": "2008-01-01",
    },
    {
        "ativo": True,
        "fonte": "BCB",
        "codigo_serie": "24363",
        "nome_serie": "IBC-Br - Indice de Atividade Economica do BCB",
        "unidade": "indice",
        "frequencia_origem": "M",
        "agregacao_mensal": "last",
        "data_inicial": "2008-01-01",
    },
]

# ---------------------------------------------------------------------------
# Series IBGE via SIDRA  (sem token)
# ---------------------------------------------------------------------------
SERIES_IBGE = [
    {
        "ativo": True,
        "fonte": "IBGE_SIDRA",
        "codigo_serie": "PNADC_DESOCUPACAO_SP",
        "nome_serie": "Taxa de desocupacao (14+) - SP",
        "sidra_paths": [
            "t/4099/n3/35/v/4099/p/all",
            "t/6468/n3/35/v/4099/p/all",
        ],
        "value_key": "V",
        "period_key": None,
        "unidade": "%",
        "frequencia_origem": "Q",
        "filtro_texto": ["taxa", "desocupacao"],
    },
    {
        "ativo": True,
        "fonte": "IBGE_SIDRA",
        "codigo_serie": "PNADC_RENDA_MEDIA_HABITUAL_SP",
        "nome_serie": "Rendimento medio real habitual - todos os trabalhos - SP",
        "sidra_paths": [
            "t/5436/n3/35/v/allxp/p/all/c2/6794",
            "t/5436/n6/3524402/v/allxp/p/all/c2/6794",
        ],
        "value_key": "V",
        "period_key": None,
        "unidade": "R$",
        "frequencia_origem": "Q",
        "filtro_texto": ["rendimento", "medio", "habitualmente", "todos os trabalhos"],
    },
]

# ---------------------------------------------------------------------------
# Series IpeaData  (sem token – OData4)
#
# IGP12_IGPM12   – IGP-M variação mensal (%)       FGV
# IGP12_INCCDI12 – INCC-DI variação mensal (%)     FGV
# FGV_ICCBR      – ICC - Índice de Confiança do Consumidor (FGV, mensal)
# ---------------------------------------------------------------------------
SERIES_IPEA = [
    {
        "ativo": True,
        "fonte": "IPEA",
        "codigo_serie": "IGP12_IGPM12",
        "nome_serie": "IGP-M variacao mensal (%)",
        "unidade": "% m/m",
        "frequencia_origem": "M",
    },
    {
        "ativo": True,
        "fonte": "IPEA",
        "codigo_serie": "IGP12_INCCDI12",
        "nome_serie": "INCC-DI variacao mensal (%)",
        "unidade": "% m/m",
        "frequencia_origem": "M",
        # Código alternativo caso o principal falhe:
        "codigos_fallback": ["BM12_INCC12", "IGP12_INCC12"],
    },
    {
        "ativo": True,
        "fonte": "IPEA",
        "codigo_serie": "FGV12_ICC12",
        "nome_serie": "ICC - Indice de Confianca do Consumidor FGV",
        "unidade": "pontos",
        "frequencia_origem": "M",
        # Código alternativo caso o principal falhe:
        "codigos_fallback": ["FGV_ICCBR", "FGV12_ICCBR12"],
    },
]