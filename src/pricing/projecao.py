from __future__ import annotations

import ast
import json
import os
import re
import warnings

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
from sklearn.model_selection import KFold

from src.analysis.utils import md, salvar_fig, salvar_tab
from src.pricing.geo import CAIXA_LAT, CAIXA_LON, SETORES, imputar_coordenadas, atribuir_setor
from src.pricing.linear_regression import SEMENTE, carregar
from src.pricing.modelos_avancados import CFG, ajustar_e_prever, construir, matrizes, preparar
from src.timeseries.arima_plus import _arima_log
from src.timeseries.panel import carregar_wide, montar_paineis

REPORT = os.path.join("reports", "results", "projecao_jacarei.md")
PARAMS_JSON = os.path.join("reports", "results", "modelos_avancados", "params.json")
PARAMS_MD = os.path.join("reports", "results", "modelos_avancados.md")
SAIDA_ANUNCIOS = os.path.join("data", "processed", "vivareal", "projecao_anuncios.csv")
SEGMENTOS = ("apartamento", "casa")
MODELOS = ("LightGBM", "HistGradientBoosting")  # CatBoost fica de fora: muito mais lento e sem ganho claro
HORIZONTES = (3, 6, 12)
DATA_SNAPSHOT = pd.Timestamp("2026-03-01")  # coleta do VivaReal (20-21/03/2026)
COL_SJC, COL_NAC = "fipezap_sjc_res_venda_preco_m2", "fipezap_nacional_res_venda_preco_m2"


# ----------------------------------------------------------------------------- parametros do ajuste
def carregar_params() -> dict[str, dict[str, dict]]:
    """Melhores parametros por segmento e modelo (JSON; se nao houver, le do relatorio do ajuste)."""
    if os.path.exists(PARAMS_JSON):
        with open(PARAMS_JSON, encoding="utf-8") as f:
            return json.load(f)
    texto = open(PARAMS_MD, encoding="utf-8").read()
    saida: dict[str, dict[str, dict]] = {}
    for bloco in re.split(r"\n## ", texto)[1:]:
        seg = bloco.split("\n")[0].strip()
        saida[seg] = {}
        for m in re.finditer(r"^- (HistGradientBoosting|LightGBM|CatBoost): (\{.*?\}) \(MAE", bloco, flags=re.M):
            saida[seg][m.group(1)] = ast.literal_eval(m.group(2))
    return saida


# ----------------------------------------------------------------------------- valor estimado
def valor_estimado(df: pd.DataFrame, segmento: str, params: dict) -> tuple[pd.Series, np.ndarray]:
    """R$/m2 estimado de cada anuncio por previsoes FORA DA AMOSTRA (5 particoes): o modelo nunca ve o
    proprio anuncio que esta avaliando. Retorna a serie estimada e os erros relativos |real - est| / est."""
    x, prep, cat_idx = preparar(df, segmento)
    y = df["preco_m2"]
    estimado = pd.Series(np.nan, index=df.index)
    for tr, te in KFold(5, shuffle=True, random_state=SEMENTE).split(df):
        Xa, Xb = matrizes(prep, x, y, df.index[tr], df.index[te])
        previsoes = []
        for nome in MODELOS:
            modelo, _ = construir(nome, None, params[nome], cat_idx)
            previsoes.append(ajustar_e_prever(nome, modelo, Xa, y.iloc[tr].to_numpy(), Xb, cat_idx))
        estimado.iloc[te] = np.mean(previsoes, axis=0)
    rel = (np.abs(y - estimado) / estimado).to_numpy()
    return estimado, rel


# ----------------------------------------------------------------------------- tendencia do indice
def cenarios_de_tendencia() -> tuple[pd.DataFrame, dict[str, float], pd.Timestamp]:
    """Variacao (em log) do indice a partir da ultima observacao, para cada cenario e horizonte, e a variacao
    OBSERVADA do indice entre a coleta (mar/2026) e o ultimo mes disponivel."""
    wide, meta = carregar_wide()
    ref = montar_paineis(wide, meta).mensal_referencia
    linhas, observado = [], {}
    ultimo = None
    for nome, col in (("SJC", COL_SJC), ("Nacional", COL_NAC)):
        y = np.log(ref[col].dropna())
        y.index = pd.DatetimeIndex(y.index, freq="MS")
        ultimo = y.index[-1]
        observado[nome] = float(y.iloc[-1] - y.loc[DATA_SNAPSHOT])
        media, inf, sup = _arima_log(y)
        c12 = float(y.diff().iloc[-12:].mean())
        for h in HORIZONTES:
            linhas.append({"cenario": f"ARIMA {nome}", "indice": nome, "h": h, "variacao": media[h - 1] - y.iloc[-1],
                           "inf": inf[h - 1] - y.iloc[-1], "sup": sup[h - 1] - y.iloc[-1]})
        if nome == "SJC":
            for h in HORIZONTES:
                linhas.append({"cenario": "Tendencia de 12 meses SJC", "indice": nome, "h": h, "variacao": h * c12, "inf": np.nan, "sup": np.nan})
    return pd.DataFrame(linhas), observado, ultimo


# ----------------------------------------------------------------------------- execucao
def executar() -> dict:
    warnings.filterwarnings("ignore")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    params = carregar_params()
    tend, observado, ultimo = cenarios_de_tendencia()
    central = "ARIMA SJC"

    anuncios, intervalos = [], {}
    for seg in SEGMENTOS:
        df = carregar(seg)
        est, rel = valor_estimado(df, seg, params[seg])
        q = {n: float(np.nanquantile(rel, n)) for n in (0.8, 0.9)}
        intervalos[seg] = q
        imp = imputar_coordenadas(df)
        setor = atribuir_setor(imp["lat_i"], imp["lon_i"])
        base = np.exp(observado["SJC"])  # leva o valor de mar/2026 ate o ultimo indice observado
        out = pd.DataFrame({"external_id": df["external_id"], "segmento": seg, "setor": setor, "neighborhood": df["neighborhood"],
                            "area_m2": df["usable_area_m2"], "preco_m2_pedido": df["preco_m2"], "preco_m2_estimado_mar2026": est,
                            "preco_m2_estimado_hoje": est * base, "origem_coordenada": imp["coord_origem"]})
        for _, c in tend[tend["cenario"] == central].iterrows():
            out[f"preco_m2_proj_{int(c['h'])}m"] = out["preco_m2_estimado_hoje"] * np.exp(c["variacao"])
        anuncios.append(out)
        print(f"[PROJECAO] {seg}: {len(df)} anuncios, erro relativo mediano {np.nanmedian(rel):.1%}", flush=True)
    todos = pd.concat(anuncios, ignore_index=True)
    os.makedirs(os.path.dirname(SAIDA_ANUNCIOS), exist_ok=True)
    todos.to_csv(SAIDA_ANUNCIOS, index=False)

    resumo = []
    for seg in SEGMENTOS:
        d = todos[todos["segmento"] == seg]
        linha = {"segmento": seg, "anuncios": len(d), "R$/m2 pedido (mediana)": d["preco_m2_pedido"].median(),
                 "R$/m2 estimado, mar/2026": d["preco_m2_estimado_mar2026"].median(), "R$/m2 estimado, hoje": d["preco_m2_estimado_hoje"].median()}
        for h in HORIZONTES:
            linha[f"R$/m2 projetado em {h} meses"] = d[f"preco_m2_proj_{h}m"].median()
        linha["intervalo 80% (+-)"] = intervalos[seg][0.8]
        linha["intervalo 90% (+-)"] = intervalos[seg][0.9]
        resumo.append(linha)
    resumo = pd.DataFrame(resumo)

    por_setor = (todos.assign(premio=todos["preco_m2_pedido"] / todos["preco_m2_estimado_mar2026"] - 1)
                 .groupby(["segmento", "setor"]).agg(anuncios=("external_id", "size"), pedido_mediana=("preco_m2_pedido", "median"),
                                                     estimado_mediana=("preco_m2_estimado_mar2026", "median"), premio_mediano=("premio", "median"))
                 .reset_index())
    salvar_tab(por_setor, "projecao_por_setor.csv")
    salvar_tab(tend, "projecao_cenarios_tendencia.csv")
    figuras = [figura_cenarios(tend, observado), figura_premio(por_setor)]
    escrever_relatorio(resumo, tend, observado, ultimo, intervalos, figuras)
    return {"resumo": resumo, "tendencia": tend}


def figura_cenarios(tend: pd.DataFrame, observado: dict) -> str:
    fig, eixo = plt.subplots(figsize=(8, 4.6))
    for cen, g in tend.groupby("cenario"):
        eixo.plot(g["h"], (np.exp(g["variacao"]) - 1) * 100, marker="o", label=cen)
    eixo.set_xlabel("meses apos o ultimo indice publicado")
    eixo.set_ylabel("variacao projetada do R$/m2 (%)")
    eixo.set_title("Cenarios de tendencia do FipeZAP aplicados aos precos de Jacarei")
    eixo.grid(alpha=0.3)
    eixo.legend(fontsize=8)
    fig.tight_layout()
    return salvar_fig(fig, "projecao_cenarios.png")


def figura_premio(por_setor: pd.DataFrame) -> str:
    setores = gpd.read_file(SETORES)
    fig, eixos = plt.subplots(1, 2, figsize=(15, 6.5))
    todos_dados = por_setor[por_setor["anuncios"] >= 5]
    geo = setores.merge(todos_dados[["segmento", "setor"]].drop_duplicates(), left_on="CD_SETOR", right_on="setor")
    x0, y0, x1, y1 = geo.total_bounds
    for eixo, seg in zip(eixos, SEGMENTOS):
        setores.plot(ax=eixo, color="#eeeeee", edgecolor="#cccccc", linewidth=0.3)
        d = por_setor[(por_setor["segmento"] == seg) & (por_setor["anuncios"] >= 5)]
        g = setores.merge(d, left_on="CD_SETOR", right_on="setor")
        g["premio_mediano"] *= 100
        g.plot(ax=eixo, column="premio_mediano", cmap="RdBu_r", vmin=-30, vmax=30, edgecolor="white", linewidth=0.3, legend=True,
               legend_kwds={"label": "preco pedido acima (+) ou abaixo (-) do estimado (%)", "shrink": 0.7})
        eixo.set_xlim(x0 - 0.01, x1 + 0.01); eixo.set_ylim(y0 - 0.01, y1 + 0.01)
        eixo.set_title(f"{seg}: premio mediano do preco pedido sobre o valor estimado, por setor (5+ anuncios)", fontsize=9)
        eixo.set_aspect("equal"); eixo.set_axis_off()
    fig.tight_layout()
    return salvar_fig(fig, "projecao_premio_por_setor.png")


def escrever_relatorio(resumo, tend, observado, ultimo, intervalos, figuras) -> None:
    t = tend.copy()
    t["variacao (%)"] = (np.exp(t["variacao"]) - 1) * 100
    t["IC95 inf (%)"] = (np.exp(t["inf"]) - 1) * 100
    t["IC95 sup (%)"] = (np.exp(t["sup"]) - 1) * 100
    L = ["# Projecao de preco de Jacarei (precificacao x tendencia do FipeZAP)", "",
         "Gerado por `python main.py projecao`. Nao editar manualmente. Leitura em `docs/PROJECAO_JACAREI.md`.", "",
         "**Metodo.** (1) Valor estimado de cada anuncio do VivaReal de Jacarei (apartamento e casa) com um conjunto de LightGBM e HistGradientBoosting "
         "ajustados (Optuna), por **previsoes fora da amostra** (5 particoes). (2) Esse valor e de **mar/2026** (coleta do VivaReal); leva-se ate "
         f"{ultimo:%b/%Y} com a variacao **observada** do indice de Sao Jose dos Campos ({(np.exp(observado['SJC']) - 1) * 100:+.1f}%; nacional "
         f"{(np.exp(observado['Nacional']) - 1) * 100:+.1f}%). (3) A partir dai aplica-se a **previsao** do indice (cenario central: ARIMA de SJC) "
         "ao R$/m2 de cada anuncio.", "",
         "**Premissa central:** Jacarei acompanha a tendencia do indice de SJC (o FipeZAP nao tem Jacarei) e todos os imoveis variam igual. "
         "A incerteza do valor de **cada imovel** (erro de avaliacao, abaixo) e muito maior que a da tendencia.", "",
         "## Resumo por segmento (R$/m2, medianas)", "", md(resumo.round(3), 3), "",
         "## Cenarios de tendencia (variacao do R$/m2 apos o ultimo indice publicado)", "",
         md(t[["cenario", "h", "variacao (%)", "IC95 inf (%)", "IC95 sup (%)"]].round(2), 2), "",
         "## Incerteza do valor de cada imovel", "",
         "Intervalo conformal pelo erro relativo fora da amostra: " + "; ".join(f"{s}: +-{q[0.8]:.0%} (80%), +-{q[0.9]:.0%} (90%)" for s, q in intervalos.items()) + ".", "",
         "## Arquivos", "", "- `data/processed/vivareal/projecao_anuncios.csv`: valor estimado e projecoes por anuncio (nao versionado)",
         "- `reports/results/eda/projecao_por_setor.csv`: pedido x estimado por setor", "- `reports/results/eda/projecao_cenarios_tendencia.csv`", ""] + [f"- `{f}`" for f in figuras]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(L) + "\n")
