"""Meta 8: visualizacoes interativas. `python main.py painel` gera um unico HTML a partir dos resultados ja salvos em
`reports/results/` e `data/processed/` (nada e recalculado aqui).

Estrutura:
    estrutura.py     Bloco e Secao: os tijolos do painel
    tema.py          paleta, layout base dos graficos
    dados.py         leitura dos resultados (tolera arquivo ausente)
    mercado.py       mapa por setor, bairros, distribuicao do R$/m2
    modelos.py       evolucao do R2, metricas, real x estimado, intervalos
    sensibilidade.py relevancia por grupo, cenarios, curvas, bairros
    series.py        FipeZAP e previsao, erro por horizonte (ARIMA x LSTM)
    projecao.py      cenarios de tendencia, projecao por segmento, premio por setor
    painel.py        resumo (KPIs), montagem do HTML com abas e tema claro/escuro
"""
