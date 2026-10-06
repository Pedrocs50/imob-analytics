from __future__ import annotations

import argparse
import re
import unicodedata
import warnings

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

from src.pricing.linear_regression import carregar
from src.pricing.modelos_avancados import ajustar_e_prever, construir, matrizes, preparar, REPORT as RELATORIO_AVANCADOS
from src.pricing.projecao import DATA_SNAPSHOT, HORIZONTES, MODELOS, carregar_params, cenarios_de_tendencia
from src.vivareal.cleaning import _limpar_texto

SEGMENTOS = ("apartamento", "casa")
TIPOS = {"apartamento": ("APARTMENT", "PENTHOUSE", "FLAT"), "casa": ("HOME", "CONDOMINIUM")}


def _normalizar(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def _intervalos(segmento: str) -> dict[float, float]:
    """Erro relativo dos intervalos conformais (teste temporal do conjunto) lidos de `modelos_avancados.md`."""
    texto = open(RELATORIO_AVANCADOS, encoding="utf-8").read()
    bloco = [b for b in re.split(r"\n## ", texto)[1:] if b.split("\n")[0].strip() == segmento][0]
    return {float(m.group(1)): float(m.group(2)) for m in re.finditer(r"^\| (0\.\d+) \| [\d.]+ \| [\d.]+ \| ([\d.]+) \|", bloco, flags=re.M)}


def _indicadores_texto(df: pd.DataFrame, texto: str) -> dict[str, int]:
    """Colunas `txt_*` do novo anuncio, pelo mesmo vocabulario e limpeza (sem digitos nem precos) do treino."""
    colunas = [c for c in df.columns if c.startswith("txt_")]
    termos = [c[4:].replace("_", " ") for c in colunas]
    vec = CountVectorizer(vocabulary=termos, binary=True, ngram_range=(1, 2), token_pattern=r"(?u)\b[a-zA-ZÀ-ú]{4,}\b")
    valores = vec.transform([_limpar_texto(texto)]).toarray()[0]
    return dict(zip(colunas, valores.tolist()))


def novo_anuncio(df: pd.DataFrame, segmento: str, dados: dict) -> pd.DataFrame:
    """Uma linha com as colunas do dataset limpo. Campos nao informados ficam ausentes (como nos anuncios reais)."""
    linha = {c: np.nan for c in df.columns}
    tipo = dados.get("tipo") or ("APARTMENT" if segmento == "apartamento" else ("CONDOMINIUM" if dados.get("em_condominio") else "HOME"))
    em_cond = int(tipo == "CONDOMINIUM")
    linha.update({
        "external_id": "NOVO", "segmento": segmento, "property_type": tipo, "em_condominio": em_cond,
        "neighborhood": dados["bairro"], "street": dados.get("rua"), "lat": dados.get("lat", np.nan), "lon": dados.get("lon", np.nan),
        "usable_area_m2": dados["area"], "total_area_m2": dados.get("terreno", np.nan),
        "bedrooms": dados.get("quartos", np.nan), "bathrooms": dados.get("banheiros", np.nan),
        "suites": dados.get("suites", np.nan), "parking_spaces": dados.get("vagas", np.nan),
        "monthly_condo": dados.get("condominio", np.nan), "condominio_informado": int(dados.get("condominio") is not None),
        "amenities_count": dados.get("amenidades", 0), "iptu_informado": 0,
        "created_at": df["created_at"].max(), "scraped_at": df["scraped_at"].iloc[0] if "scraped_at" in df.columns else np.nan,
    })
    linha.update(_indicadores_texto(df, dados.get("texto", "")))
    return pd.DataFrame([linha])


def prever(segmento: str, dados: dict) -> dict:
    """Valor estimado (R$/m2 e R$) de um imovel novo com o conjunto LightGBM + HistGradientBoosting treinado em todo o segmento,
    intervalos conformais e projecao pela tendencia do FipeZAP de SJC."""
    warnings.filterwarnings("ignore")
    df = carregar(segmento)
    nomes = {_normalizar(b): b for b in df["neighborhood"].dropna().unique()}
    if _normalizar(dados["bairro"]) in nomes:
        dados = {**dados, "bairro": nomes[_normalizar(dados["bairro"])]}  # nome como esta no dataset (acentos e caixa)
    else:
        print(f"[PREVER] aviso: o bairro '{dados['bairro']}' nao existe no segmento; o modelo usa so as demais informacoes.")
    params = carregar_params()[segmento]
    base = pd.concat([df, novo_anuncio(df, segmento, dados)], ignore_index=True)
    # o novo anuncio entra na montagem das variaveis (imputacao de coordenada pela rua/bairro), mas nunca no treino
    x, prep, cat_idx = preparar(base, segmento)
    y = base["preco_m2"]
    treino, teste = base.index[:-1], base.index[-1:]
    Xa, Xb = matrizes(prep, x, y, treino, teste)
    previsoes = []
    for nome in MODELOS:
        modelo, _ = construir(nome, None, params[nome], cat_idx)
        previsoes.append(float(ajustar_e_prever(nome, modelo, Xa, y.loc[treino].to_numpy(), Xb, cat_idx)[0]))
    estimado = float(np.mean(previsoes))
    tend, observado, ultimo = cenarios_de_tendencia()
    hoje = estimado * float(np.exp(observado["SJC"]))
    central = tend[tend["cenario"] == "ARIMA SJC"].set_index("h")["variacao"]
    q = _intervalos(segmento)
    area = dados["area"]
    return {"estimado_mar2026": estimado, "estimado_hoje": hoje, "ultimo_indice": ultimo, "area": area, "intervalos": q,
            "projecao": {h: hoje * float(np.exp(central[h])) for h in HORIZONTES}, "previsoes_modelos": dict(zip(MODELOS, previsoes)),
            "origem_coordenada": int(x["coord_origem"].iloc[-1]), "setor": x["setor"].iloc[-1]}


def _formatar(segmento: str, r: dict, pedido: float | None) -> str:
    brl = lambda v: f"R$ {v:,.0f}".replace(",", ".")
    a = r["area"]
    L = [f"\nAvaliacao ({segmento}, {a:g} m2, setor {r['setor']}):",
         f"  Valor estimado hoje ({r['ultimo_indice']:%m/%Y}): {brl(r['estimado_hoje'])}/m2 = {brl(r['estimado_hoje'] * a)}"]
    for n, nivel in ((0.8, "80%"), (0.9, "90%")):
        e = r["intervalos"][n]
        L.append(f"  Intervalo de {nivel}: {brl(r['estimado_hoje'] * (1 - e))} a {brl(r['estimado_hoje'] * (1 + e))}/m2 "
                 f"({brl(r['estimado_hoje'] * (1 - e) * a)} a {brl(r['estimado_hoje'] * (1 + e) * a)})")
    L.append("  Projecao pela tendencia de SJC (ARIMA, cenario central; so o nivel central, sem incerteza da tendencia):")
    for h, v in r["projecao"].items():
        L.append(f"    em {h:>2} meses: {brl(v)}/m2 = {brl(v * a)}")
    if pedido:
        pm2 = pedido / a
        L.append(f"  Preco pedido informado: {brl(pedido)} = {brl(pm2)}/m2, {(pm2 / r['estimado_hoje'] - 1) * 100:+.1f}% em relacao ao estimado.")
    if r["origem_coordenada"] == -1:
        L.append("  Aviso: sem rua/bairro conhecido nem coordenadas; a localizacao fina nao foi usada.")
    L.append("  Lembrete: e um preco PEDIDO esperado (anuncios), nao de venda. Erro relativo tipico do modelo: 9% a 11% (mediana), com cauda maior.")
    return "\n".join(L)


def executar(argv: list[str]) -> dict:
    p = argparse.ArgumentParser(prog="python main.py prever", description="Avalia um imovel de Jacarei com os modelos finais.")
    p.add_argument("--segmento", choices=SEGMENTOS, required=True)
    p.add_argument("--bairro", required=True)
    p.add_argument("--area", type=float, required=True, help="area util em m2")
    p.add_argument("--rua")
    p.add_argument("--quartos", type=float)
    p.add_argument("--banheiros", type=float)
    p.add_argument("--suites", type=float)
    p.add_argument("--vagas", type=float)
    p.add_argument("--terreno", type=float, help="area total do terreno em m2 (casas)")
    p.add_argument("--condominio", type=float, help="taxa de condominio mensal em R$")
    p.add_argument("--amenidades", type=int, default=0, help="quantidade de comodidades listadas")
    p.add_argument("--tipo", help="APARTMENT, PENTHOUSE, FLAT, HOME ou CONDOMINIUM (casa em condominio)")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--texto", default="", help="titulo/descricao do anuncio (precos e numeros sao ignorados)")
    p.add_argument("--preco-pedido", type=float, help="preco pedido total em R$, para comparar com o estimado")
    a = p.parse_args(argv)
    if a.tipo and a.tipo not in TIPOS[a.segmento]:
        p.error(f"--tipo deve ser um de {TIPOS[a.segmento]} para {a.segmento}")
    dados = {k: v for k, v in dict(bairro=a.bairro, area=a.area, rua=a.rua, quartos=a.quartos, banheiros=a.banheiros, suites=a.suites,
                                   vagas=a.vagas, terreno=a.terreno, condominio=a.condominio, amenidades=a.amenidades, tipo=a.tipo,
                                   lat=a.lat, lon=a.lon, texto=a.texto).items() if v is not None}
    resultado = prever(a.segmento, dados)
    print(_formatar(a.segmento, resultado, a.preco_pedido))
    return resultado
