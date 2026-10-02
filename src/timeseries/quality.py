from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from src.timeseries.catalogo import SERIES_POR_ID
from src.timeseries.config import DB_PATH, QUALITY_REPORT
from src.timeseries.storage import conectar

# lacunas que existem na propria fonte (ja verificadas); aparecem como aviso, nao como falha
LACUNAS_CONHECIDAS = {
    "ibge_renda_sp": "IBGE nao publica a tabela 5436 em 2020 (so 1o tri) e 2021 (nenhum trimestre)",
}


@dataclass
class ResultadoSerie:
    serie_id: str
    fonte: str
    frequencia: str
    n: int
    primeira: date
    ultima: date
    lacunas: int
    fora_da_faixa: int
    defasagem_meses: int  # meses entre a ultima data e hoje
    falhas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def _lacunas(datas: pd.DatetimeIndex, frequencia: str) -> int:
    freq = "MS" if frequencia == "M" else "QS"
    esperado = pd.date_range(datas.min(), datas.max(), freq=freq)
    return len(esperado.difference(datas))


def validar(db_path: str = DB_PATH) -> list[ResultadoSerie]:
    hoje = date.today()
    resultados: list[ResultadoSerie] = []

    with conectar(db_path) as conexao:
        series = pd.read_sql("SELECT * FROM series ORDER BY fonte, id", conexao)
        coletas = pd.read_sql(
            "SELECT serie_id, status, erro FROM coletas WHERE id IN "
            "(SELECT MAX(id) FROM coletas GROUP BY serie_id)",
            conexao,
        ).set_index("serie_id")

        for _, s in series.iterrows():
            obs = pd.read_sql(
                "SELECT data_ref, valor FROM observacoes WHERE serie_id = ? ORDER BY data_ref",
                conexao, params=(s["id"],),
            )
            if obs.empty:
                erro = coletas.loc[s["id"], "erro"] if s["id"] in coletas.index else "sem coleta"
                resultados.append(ResultadoSerie(
                    s["id"], s["fonte"], s["frequencia"], 0, hoje, hoje, 0, 0, 0,
                    falhas=[f"serie vazia ({erro})"],
                ))
                continue

            datas = pd.DatetimeIndex(pd.to_datetime(obs["data_ref"]))
            valores = obs["valor"]
            meses_atraso = (hoje.year - datas.max().year) * 12 + hoje.month - datas.max().month
            r = ResultadoSerie(
                s["id"], s["fonte"], s["frequencia"], len(obs), datas.min().date(), datas.max().date(),
                _lacunas(datas, s["frequencia"]), 0, meses_atraso,
            )

            definicao = SERIES_POR_ID.get(s["id"])
            if definicao is not None:
                baixo, alto = definicao.faixa
                r.fora_da_faixa = int(((valores < baixo) | (valores > alto)).sum())
                if r.fora_da_faixa:
                    r.falhas.append(f"{r.fora_da_faixa} valor(es) fora da faixa plausivel {definicao.faixa}")
                folga = definicao.defasagem_meses + (3 if s["frequencia"] == "Q" else 1)
                if meses_atraso > folga + 1:
                    r.avisos.append(
                        f"desatualizada: ultimo dado {r.ultima:%Y-%m}, {meses_atraso} meses atras "
                        f"(esperado ate ~{folga})"
                    )
            elif (valores <= 0).any():
                r.falhas.append("valores nao positivos em serie de preco/indice")

            if datas.year.min() < 1990 or datas.max().year > hoje.year + 1:
                r.falhas.append("datas implausiveis")
            if r.lacunas:
                aviso = f"{r.lacunas} periodo(s) ausente(s) no intervalo"
                if s["id"] in LACUNAS_CONHECIDAS:
                    aviso += f" - {LACUNAS_CONHECIDAS[s['id']]}"
                    r.avisos.append(aviso)
                else:
                    r.falhas.append(aviso)
            resultados.append(r)

    return resultados


def escrever_relatorio(resultados: list[ResultadoSerie], caminho: str = QUALITY_REPORT) -> None:
    falhas = [r for r in resultados if r.falhas]
    avisos = [r for r in resultados if r.avisos]
    linhas = [
        "# Qualidade das series temporais",
        "",
        "Gerado por `python main.py series-painel`. Nao editar manualmente.",
        "",
        f"- Series no banco: {len(resultados)}",
        f"- Com falha: {len(falhas)}",
        f"- Com aviso: {len(avisos)}",
        "",
        "| Serie | Fonte | Freq | N | Primeira | Ultima | Lacunas | Fora da faixa | Situacao |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in resultados:
        situacao = "FALHA" if r.falhas else "aviso" if r.avisos else "ok"
        linhas.append(
            f"| `{r.serie_id}` | {r.fonte} | {r.frequencia} | {r.n} | {r.primeira:%Y-%m} | "
            f"{r.ultima:%Y-%m} | {r.lacunas} | {r.fora_da_faixa} | {situacao} |"
        )
    if falhas or avisos:
        linhas += ["", "## Detalhes", ""]
        for r in resultados:
            for texto in r.falhas:
                linhas.append(f"- **FALHA** `{r.serie_id}`: {texto}")
            for texto in r.avisos:
                linhas.append(f"- aviso `{r.serie_id}`: {texto}")
    linhas.append("")

    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))
