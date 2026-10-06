"""Meta 9: relatorio analitico automatico. `python main.py relatorio` monta `reports/relatorio_analitico.md` (e a versao HTML com as
figuras embutidas) a partir dos resultados salvos. Os numeros vem sempre dos arquivos; as afirmacoes interpretativas so aparecem se os
numeros as sustentam (senao o relatorio avisa para revisar).

Estrutura:
    numeros.py      le os resultados e calcula os numeros citados (uma fonte unica)
    referencias.py  trabalhos da literatura usados na comparacao (dados + ressalvas), com link
    secoes.py       uma funcao por secao do relatorio (devolve Markdown)
    relatorio.py    monta, verifica a consistencia e grava .md e .html
"""
