from __future__ import annotations

from datetime import date

from src.timeseries.catalogo import SERIES, SerieMacro
from src.timeseries.clients import INICIO_PADRAO, _sessao, coletar, salvar_bruto
from src.timeseries.config import DB_PATH
from src.timeseries.storage import conectar, gravar_observacoes, registrar_coleta, registrar_serie


def _descartar_mes_corrente(serie: SerieMacro, pontos: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Series calculadas sobre o mes (ex.: Selic acumulada, PTAX media) ficam parciais
    enquanto o mes nao acaba; o ponto do mes corrente seria enganoso."""
    if not serie.descartar_mes_corrente:
        return pontos
    inicio_mes = date.today().replace(day=1)
    return [(d, v) for d, v in pontos if d < inicio_mes]


def _agregar_ao_mes(serie: SerieMacro, pontos: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Leva serie diaria ao mes (ultimo valor do mes), como declarado no catalogo."""
    if not serie.agregacao:
        return pontos
    if serie.agregacao != "last":
        raise ValueError(f"agregacao nao suportada: {serie.agregacao}")
    por_mes: dict[date, float] = {}
    for data, valor in pontos:  # pontos ja vem ordenados por data
        por_mes[data.replace(day=1)] = valor
    return sorted(por_mes.items())


def coletar_series(db_path: str = DB_PATH, series: tuple[SerieMacro, ...] = SERIES) -> dict[str, str]:
    """Coleta todas as series do catalogo pelas APIs publicas e grava no banco
    de series temporais. Uma falha nao interrompe as demais; o resultado por
    serie e devolvido e fica registrado na tabela `coletas`."""
    sessao = _sessao()
    resultado: dict[str, str] = {}

    with conectar(db_path) as conexao:
        for serie in series:
            registrar_serie(
                conexao,
                {
                    "id": serie.id, "fonte": serie.fonte, "codigo": serie.codigo,
                    "nome": serie.nome, "unidade": serie.unidade, "tipo": serie.tipo,
                    "frequencia": serie.frequencia, "defasagem_meses": serie.defasagem_meses,
                },
            )
            try:
                pontos, bruto = coletar(serie, sessao)
                arquivo = salvar_bruto(serie, bruto)
                # a resposta bruta guarda tudo; no banco ficam so os dados a partir de 2005
                # (antes disso ha hiperinflacao e outras mudancas de moeda, fora do escopo)
                pontos = [(d, v) for d, v in pontos if d >= INICIO_PADRAO]
                pontos = _agregar_ao_mes(serie, _descartar_mes_corrente(serie, pontos))
                n = gravar_observacoes(conexao, serie.id, pontos)
                registrar_coleta(conexao, serie.id, n, "ok", arquivo_bruto=arquivo)
                resultado[serie.id] = f"ok ({n} pontos, {pontos[0][0]} a {pontos[-1][0]})"
            except Exception as erro:  # uma serie com problema nao derruba as outras
                registrar_coleta(conexao, serie.id, 0, "erro", erro=str(erro)[:500])
                resultado[serie.id] = f"ERRO: {erro}"
            conexao.commit()
            print(f"[SERIES] {serie.id}: {resultado[serie.id]}")

    return resultado
