from __future__ import annotations

import os

import pandas as pd

from src.vivareal.cleaning import adicionar_texto, deduplicar, limpar_segmento, preparar_base
from src.vivareal.config import VivaRealConfig
from src.vivareal.loader import carregar_listings


def construir_datasets(config: VivaRealConfig | None = None) -> dict[str, pd.DataFrame]:
    """Gera os datasets limpos (apartamento, casa e residencial) a partir do
    banco bruto, que e aberto somente para leitura, e salva CSVs e o relatorio."""
    cfg = config or VivaRealConfig()

    bruto = carregar_listings(cfg.db_path)
    print(f"[VIVAREAL] {len(bruto)} registros carregados de {cfg.db_path}")

    base = preparar_base(bruto)
    base = base[base["usage_type"] == cfg.usage_type]
    n_residencial = len(base)
    base, removidas = deduplicar(base)
    base = adicionar_texto(base)
    print(f"[VIVAREAL] {n_residencial} residenciais; {removidas} duplicatas removidas por external_id")

    datasets: dict[str, pd.DataFrame] = {}
    logs: dict[str, list[tuple[str, int]]] = {}
    ajustes: dict[str, list[dict]] = {}
    for seg in cfg.segmentos:
        datasets[seg.nome], logs[seg.nome], ajustes[seg.nome] = limpar_segmento(base, seg, cfg.outlier_iqr_factor)
        print(f"[VIVAREAL] {seg.nome}: {len(datasets[seg.nome])} registros limpos")

    datasets["residencial"] = pd.concat(
        [datasets[seg.nome] for seg in cfg.segmentos], ignore_index=True
    )
    print(f"[VIVAREAL] residencial: {len(datasets['residencial'])} registros limpos")

    os.makedirs(cfg.output_dir, exist_ok=True)
    for nome, df in datasets.items():
        df.to_csv(os.path.join(cfg.output_dir, f"{nome}.csv"), index=False, encoding="utf-8")

    _escrever_relatorio(cfg, len(bruto), n_residencial, removidas, len(base), logs, ajustes, datasets)
    print(f"[VIVAREAL] Datasets em {cfg.output_dir} | relatorio em {cfg.report_path}")
    return datasets


def _escrever_relatorio(
    cfg: VivaRealConfig,
    n_bruto: int,
    n_residencial: int,
    removidas: int,
    n_dedup: int,
    logs: dict[str, list[tuple[str, int]]],
    ajustes: dict[str, list[dict]],
    datasets: dict[str, pd.DataFrame],
) -> None:
    linhas = [
        "# Limpeza do dataset VivaReal Jacarei",
        "",
        "Gerado por `python main.py vivareal-prep`. Nao editar manualmente.",
        f"Banco de origem (somente leitura): `{cfg.db_path.replace(chr(92), '/')}`",
        "",
        "## Etapas comuns",
        "",
        "| Etapa | Linhas |",
        "|---|---|",
        f"| registros na tabela `listings` | {n_bruto} |",
        f"| usage_type = {cfg.usage_type} | {n_residencial} |",
        f"| apos remover duplicatas por `external_id` (mantido o `scraped_at` mais recente; {removidas} removidas) | {n_dedup} |",
        "",
    ]
    for nome, log in logs.items():
        linhas += [f"## Segmento: {nome}", "", "| Etapa (cumulativa) | Linhas restantes |", "|---|---|"]
        anterior = n_dedup
        for etapa, restantes in log:
            linhas.append(f"| {etapa} (-{anterior - restantes}) | {restantes} |")
            anterior = restantes
        linhas += ["", f"Ajustes de valores no segmento {nome} (nenhuma linha removida):", ""]
        tabela = pd.DataFrame(ajustes[nome])
        linhas += ["| " + " | ".join(tabela.columns) + " |", "|" + "---|" * len(tabela.columns)]
        linhas += ["| " + " | ".join(str(v) for v in linha) + " |" for linha in tabela.itertuples(index=False)]
        linhas.append("")

    linhas += ["## Arquivos gerados", "", "| Arquivo | Linhas |", "|---|---|"]
    for nome, df in datasets.items():
        linhas.append(f"| `{cfg.output_dir.replace(chr(92), '/')}/{nome}.csv` | {len(df)} |")
    linhas += [
        "",
        "Valores ausentes foram mantidos (sem imputacao). `em_condominio` so existe",
        "para casas; fica vazio em apartamentos. Coordenadas lat/lon = 0 viraram vazias.",
        "Taxas de condominio e IPTU positivas fora da faixa plausivel viraram ausentes (zero = sem taxa,",
        "mantido). `condominio_informado` e `iptu_informado` indicam se a taxa existe apos o ajuste.",
        "",
    ]

    os.makedirs(os.path.dirname(cfg.report_path), exist_ok=True)
    with open(cfg.report_path, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))
