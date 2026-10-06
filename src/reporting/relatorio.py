"""Monta o relatorio analitico: Markdown (com figuras por caminho relativo) e HTML autocontido (figuras embutidas)."""
from __future__ import annotations

import base64
import os
import re
from datetime import datetime

import markdown

from src.reporting import numeros, secoes

SAIDA_MD = os.path.join("reports", "relatorio_analitico.md")
SAIDA_HTML = os.path.join("reports", "relatorio_analitico.html")
CSS = """
body{font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;max-width:920px;margin:0 auto;padding:24px 16px 64px;color:#1a1a19;background:#fcfcfb}
h1{font-size:28px;margin:0 0 4px}h2{font-size:21px;margin:36px 0 8px;padding-top:12px;border-top:1px solid #e1e0d9}h3{font-size:17px;margin:24px 0 6px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0;display:block;overflow-x:auto}th,td{border-bottom:1px solid #e1e0d9;padding:6px 9px;text-align:left;vertical-align:top}
th{color:#52514e;background:#f4f3ef}img{max-width:100%;height:auto;display:block;margin:12px auto 2px}em{color:#52514e}code{background:#eeede8;padding:1px 5px;border-radius:4px;font-size:13px}
blockquote{margin:16px 0;padding:8px 16px;border-left:4px solid #2a78d6;background:#f4f3ef}a{color:#2a78d6;word-break:break-all}.meta{color:#52514e;font-size:14px}
@media (prefers-color-scheme:dark){body{background:#0d0d0d;color:#f3f2ee}h2{border-color:#2c2c2a}th{background:#1a1a19;color:#c3c2b7}th,td{border-color:#2c2c2a}code{background:#1a1a19}blockquote{background:#1a1a19}em{color:#c3c2b7}}
"""


def montar() -> tuple[str, list[str]]:
    n = numeros.coletar()
    r = secoes.Relato()
    partes = [secoes.resumo(n, r), secoes.escopo_dados(n, r), secoes.metodos(n, r), secoes.resultados_precificacao(n, r), secoes.resultados_series(n, r),
              secoes.projecao(n, r), secoes.literatura(n, r), secoes.limitacoes(n, r), secoes.conclusoes(n, r), secoes.apendices(n, r)]
    verificacoes = ("## Apêndice C. Verificação automática do texto\n\n" + ("Todas as afirmações interpretativas foram checadas contra os números atuais e são sustentadas por eles."
                                                                           if not r.avisos else "Itens a revisar:\n\n" + "\n".join(f"- {a}" for a in r.avisos)))
    cabecalho = (f"# Análise e previsão do mercado imobiliário de Jacareí-SP\n\n"
                 f"<p class=\"meta\">Relatório analítico da iniciação científica · gerado automaticamente em {datetime.now():%d/%m/%Y %H:%M} por <code>python main.py relatorio</code> a partir dos resultados salvos. "
                 f"Números lidos dos arquivos; textos interpretativos conferidos contra os números (Apêndice C).</p>\n")
    return "\n\n".join([cabecalho, *partes, verificacoes]) + "\n", r.avisos


def _embutir_figuras(html: str, base: str) -> str:
    def troca(m: re.Match) -> str:
        caminho = os.path.join(base, m.group(1))
        if not os.path.exists(caminho):
            return m.group(0)
        with open(caminho, "rb") as f:
            return f'src="data:image/png;base64,{base64.b64encode(f.read()).decode()}"'
    return re.sub(r'src="(figures/[^"]+\.png)"', troca, html)


def pagina_html(texto: str, voltar: bool = False) -> str:
    """Pagina HTML autocontida (figuras embutidas). `voltar=True` acrescenta o link para a pagina inicial do site publicado."""
    corpo = markdown.markdown(texto, extensions=["tables", "sane_lists"])
    topo = '<p class="meta"><a href="index.html">← Início</a> · <a href="painel.html">Painel interativo</a></p>' if voltar else ""
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Relatório — mercado imobiliário de Jacareí</title><meta name="description" content="Relatório analítico da iniciação científica sobre o mercado imobiliário de Jacareí-SP.">'
            f'<style>{CSS}</style></head><body>{topo}{_embutir_figuras(corpo, "reports")}</body></html>')


def executar() -> str:
    texto, avisos = montar()
    os.makedirs(os.path.dirname(SAIDA_MD), exist_ok=True)
    with open(SAIDA_MD, "w", encoding="utf-8") as f:
        f.write(texto)
    pagina = pagina_html(texto)
    with open(SAIDA_HTML, "w", encoding="utf-8") as f:
        f.write(pagina)
    print(f"[RELATORIO] {SAIDA_MD} e {SAIDA_HTML} ({len(pagina) / 1e6:.1f} MB); {len(avisos)} aviso(s) de consistência")
    for a in avisos:
        print(f"[RELATORIO] revisar: {a}")
    return SAIDA_MD
