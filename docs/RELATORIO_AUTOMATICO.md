# Relatorio analitico automatico (meta 9)

Data: 2026-10-05.

```bash
python main.py relatorio     # segundos; gera reports/relatorio_analitico.md e reports/relatorio_analitico.html
```

- `reports/relatorio_analitico.md`: texto em Markdown, figuras por caminho relativo (`figures/...`). **Versionado.**
- `reports/relatorio_analitico.html`: o mesmo relatorio em uma pagina autocontida, com as figuras embutidas (~1 MB), pronta para enviar. **Nao versionada** (gerada).

Como o painel (`docs/PAINEL_INTERATIVO.md`), o relatorio **so le resultados ja salvos**; nao recalcula modelos. Rode antes os comandos que o alimentam
(`modelos-avancados`, `sensibilidade`, `projecao`, `lstm`, `arima`...) e depois `relatorio`.

## Conteudo (12 secoes)

| Secao | O que traz |
|---|---|
| 1. Resumo executivo | Os numeros principais (R², erro, ARIMA, projecao) e a ressalva central |
| 2. Objetivo, escopo e dados | As duas trilhas, contagens da limpeza (lidas de `vivareal_limpeza.md`), dados externos e **dados faltantes e como foram tratados** |
| 3. Metodos | Validacao, modelos, variaveis, ajuste, intervalos; ARIMA/walk-forward/Diebold-Mariano; LSTM em painel; projecao |
| 4. Resultados: precificacao | Evolucao do R², modelos finais, calibracao dos intervalos, importancia e cenarios "e se?" |
| 5. Resultados: series | MAPE por horizonte (nacional e SJC) para ARIMA, LSTM e gradient boosting; significancia; resultados negativos |
| 6. Projecao de preco | Medianas por segmento e cenarios de tendencia com IC |
| 7. **Comparacao com a literatura** | Tabela dos trabalhos, comparacao justa (R² do preco total, particao aleatoria), o que concorda e o que difere (`docs/COMPARACAO_LITERATURA.md`) |
| 8. Limitacoes e ameacas a validade | Tabela com efeito de cada limitacao e o que foi feito ou falta |
| 9. Conclusoes e proximos passos | |
| Apendices | A: como reproduzir (comandos e tempos); B: referencias com ressalvas; C: verificacao automatica do texto |

## Como se garante que o texto acompanha os numeros

1. **Numeros nunca sao digitados.** `numeros.py` le os CSVs/relatorios e calcula tudo o que e citado (inclusive o R² e o MAPE do **preco total**, derivados
   das previsoes fora da amostra, para a comparacao com a literatura brasileira).
2. **Afirmacoes interpretativas sao condicionais.** `Relato.afirmar(condicao, texto)` so mostra a frase se os numeros a sustentam (ex.: "o ARIMA tem o menor erro em todos os
   horizontes no nacional", "a cobertura dos intervalos fica a ate 3 pontos do nominal", "trocar o modelo linear por arvores foi o maior salto"). Se deixar de valer, aparece
   um marcador **[revisar]** no texto e um aviso no **Apendice C** e no terminal.
3. **Fonte ausente nao quebra o relatorio.** A secao correspondente mostra o comando que gera o resultado que falta.
4. Frases que dependem de leitura humana (ex.: "informacao nova rendeu tanto quanto o ajuste", comparacoes com a literatura) sao estaticas e foram revisadas em 2026-10-05;
   por isso ha a data e o aviso no cabecalho. Ao mudar um resultado de forma grande, releia as secoes 7 a 9.

## Estrutura do codigo (`src/reporting/`)

```text
numeros.py      coleta e calcula todos os numeros (uma fonte unica); reaproveita src/visualization/dados.py
referencias.py  os trabalhos da literatura (dados, metodo, resultado, ressalva, link); fonte unica da secao 7 e do apendice B
secoes.py       uma funcao por secao, em Markdown; utilidades (formato brasileiro de numeros, tabelas, acentuacao dos rotulos dos CSVs)
relatorio.py    monta, verifica a consistencia, grava .md e .html (markdown + figuras embutidas em base64)
```

Para **acrescentar uma secao**: crie a funcao em `secoes.py` e inclua-a em `relatorio.montar()`. Para **acrescentar uma referencia**: edite `referencias.py` (e descreva a
leitura em `docs/COMPARACAO_LITERATURA.md`).

## Limitacoes

- O relatorio e **Markdown/HTML**; nao ha exportacao em PDF/DOCX (o HTML pode ser impresso como PDF pelo navegador).
- Parte do texto interpretativo e estatica (item 4 acima).
- A comparacao com a literatura usa resumos e paginas de busca para varios trabalhos; as ressalvas estao no apendice B (`docs/COMPARACAO_LITERATURA.md`).
- Os rotulos dos CSVs saem sem acento por convencao do repositorio; o relatorio os acentua por substituicao (lista em `secoes.acentuar`) e rotulos novos podem aparecer sem acento.
