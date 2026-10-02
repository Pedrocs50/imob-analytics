from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG_DIR = os.path.join("reports", "figures")
TAB_DIR = os.path.join("reports", "results", "eda")


def md(df: pd.DataFrame, casas: int = 3) -> str:
    """Tabela em Markdown (sem depender de `tabulate`)."""
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return "" if pd.isna(v) else f"{v:.{casas}f}"
        return str(v)

    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join(fmt(v) for v in linha) + " |" for linha in df.itertuples(index=False)]
    return "\n".join(linhas)


def salvar_fig(fig, nome: str) -> str:
    os.makedirs(FIG_DIR, exist_ok=True)
    caminho = os.path.join(FIG_DIR, nome)
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return caminho.replace("\\", "/")


def salvar_tab(df: pd.DataFrame, nome: str) -> None:
    os.makedirs(TAB_DIR, exist_ok=True)
    df.to_csv(os.path.join(TAB_DIR, nome), index=False, encoding="utf-8")
