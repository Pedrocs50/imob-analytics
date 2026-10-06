# IC Mercado Imobiliario (Jacarei-SP)

Iniciacao cientifica sobre analise e previsao do mercado imobiliario de Jacarei-SP: **precificacao** de imoveis (gradient boosting), **series temporais** do
indice FipeZAP (ARIMA, LSTM) e **projecao de preco**, com dados abertos (anuncios, FipeZAP, IBGE, BCB, IPEA).

**Resultados principais** (detalhes no [relatorio](reports/relatorio_analitico.md)):

| | Apartamento | Casa |
|---|---|---|
| R² do R$/m² (teste temporal, anuncios mais recentes) | 0,73 | 0,80 |
| Erro tipico por imovel (MAPE) | 11% | 15% |
| Valor estimado hoje (mediana, R$/m²) | ~6.460 | ~4.600 |
| Tendencia do R$/m² em 12 meses (cenario central) | +8% | +8% |

Nas series, o **ARIMA(0,2,3) e o melhor modelo no indice nacional**; em Sao Jose dos Campos as redes erram menos aos 6 e 12 meses, mas sem significancia estatistica.

## Estado das metas

Todas as 9 metas estao atingidas (algumas com ressalvas). Detalhes em [`docs/METAS.md`](docs/METAS.md).

| Meta | Descricao | Estado | Comando |
|---|---|---|---|
| 1 | Coleta de dados publicos | Atingida (faltam registros municipais) | `series-coletar`, `scrape` |
| 2 | Tratamento e organizacao | Atingida | `vivareal-prep`, `series-painel` |
| 3 | Estatistica descritiva e exploratoria | Atingida | `eda-series`, `eda-vivareal` |
| 4 | Regressao linear multipla e ARIMA | Atingida para precos (sem serie de demanda) | `reg-linear`, `arima` |
| 5 | LSTM | Atingida (sem preditores macro) | `lstm` |
| 6 | Comparacao ARIMA x LSTM | Atingida com ressalvas | `lstm` |
| 7 | Sensibilidade e relevancia das variaveis | Atingida | `sensibilidade` |
| 8 | Visualizacoes interativas | Atingida | `painel` |
| 9 | Relatorios analiticos automaticos | Atingida | `relatorio` |

## Inicio rapido

```bash
python -m venv venv                      # 1. ambiente virtual (Python 3.11 ou superior)
venv\Scripts\activate                    #    Windows (Linux/macOS: source venv/bin/activate)
python -m pip install -r requirements.txt

python main.py verificar                 # 2. confere ambiente, dados e o que ja pode rodar
python main.py painel --abrir            # 3. gera e abre o painel interativo no navegador
python main.py relatorio --abrir         #    gera e abre o relatorio
```

Sem a base do orientador (veja "Dados"), os passos 1 a 3 funcionam com o que estiver versionado: cartoes cujos dados nao existem mostram um aviso com o comando que os gera.

## Abrir o painel e o relatorio (HTML)

O painel e o relatorio sao **arquivos HTML autocontidos**: nao precisam de servidor nem de internet.

1. Gere: `python main.py painel` e `python main.py relatorio` (segundos; so leem resultados ja salvos).
2. Abra com **duplo clique** em um destes arquivos (qualquer navegador moderno):
   - `reports/figures/painel_interativo.html`: painel com 6 abas (Resumo, Mercado, Modelos, Sensibilidade, Series temporais, Projecao), seletores, mapas e tema claro/escuro.
   - `reports/relatorio_analitico.html`: relatorio completo, com a comparacao com a literatura (o `.md` equivalente e `reports/relatorio_analitico.md`).
3. Ou use `--abrir` (`python main.py painel --abrir`) para gerar e abrir de uma vez. No Windows tambem: `start reports\figures\painel_interativo.html`.

Os dois arquivos sao **gerados** (nao versionados): rode os comandos de novo depois de atualizar qualquer resultado. Guia do painel: [`docs/PAINEL_INTERATIVO.md`](docs/PAINEL_INTERATIVO.md).
Para uma imagem pronta, os PNG das analises ficam em `reports/figures/`, e o mapa por setor tem a versao `reports/figures/mapa_setores_interativo.html`.

## Publicar o painel e o relatorio na web (GitHub Pages)

Para qualquer pessoa (orientador, banca) ver **sem instalar nada e sem os dados**: o site e estatico e ja traz os resultados dentro dos HTML.

1. **Gerar o site:** `python main.py publicar` cria a pasta `site/` com `index.html` (pagina inicial), `painel.html` e `relatorio.html` (~4 MB; plotly.js vem de CDN).
2. **Enviar ao GitHub:** commitar `site/` e `.github/` e dar push no `main`:
   ```bash
   git add site .github
   git commit -m "docs: publica painel e relatorio no GitHub Pages"
   git push origin main
   ```
3. **Ativar uma unica vez no GitHub:** repositorio > *Settings* > *Pages* > *Build and deployment* > **Source: GitHub Actions**. O workflow `.github/workflows/pages.yml` publica `site/` a cada push que o altere.
4. **Endereco:** https://pedrocs50.github.io/imob-analytics/ (aparece tambem na aba *Actions*, no job "Publicar site").

Para atualizar depois de novos resultados: `python main.py publicar`, commit e push de `site/`. O site **nao tem** a base do orientador nem dados de anunciantes
(o painel mostra medianas por setor e pontos preco x estimado sem identificador de anuncio); mesmo assim, avise o orientador antes de divulgar o link.
Os mapas de Jacarei usam Leaflet com mapa de fundo do Esri carregado da internet; sem internet eles nao carregam.

## Instalacao

- **Python 3.11 ou superior** (desenvolvido com 3.14). `python main.py verificar` confere se todas as bibliotecas importam.
- O `requirements.txt` inclui o PyTorch (grande; a versao CPU basta), geopandas, lightgbm, catboost, optuna, plotly e markdown.
- O scraper (`scrape`) exige o Chrome for Testing e o chromedriver em `scripts/`, que nao sao versionados; os demais comandos nao precisam deles.

## Dados: o que esta e o que nao esta no repositorio

O repositorio e **publico**, entao alguns dados ficam de fora de proposito.

| Dado | No git? | Como obter |
|---|---|---|
| Excel do FipeZAP (`data/raw/fipezap-serieshistoricas (2).xlsx`) | Sim | Download manual em [fipe.org.br](https://www.fipe.org.br/pt-br/indices/fipezap/) |
| Recorte de Jacarei da malha de setores do IBGE (`data/raw/ibge/jacarei_setores_2022.gpkg`, 0,9 MB) e Censo 2022 por setor | Sim | Gerados da malha completa de SP (`SP_setores_CD2022`, 335 MB, **nao versionada**), baixada de [geoftp.ibge.gov.br](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/) e salva em `data/raw/SP_setores_CD2022/` |
| Respostas das APIs (`data/raw/macro/`) | Sim | `python main.py series-coletar` |
| **Base VivaReal do orientador** | **Nao** | Pedir ao orientador e salvar em `data/raw/vivareal_jacarei/vivareal_jacarei_20260324.db`. Contem nome, telefone, WhatsApp e CRECI de anunciantes: **nunca versionar**. |
| `data/database/*.db` (banco do scraper e `series_temporais.db`) | Nao | Gerados pelos comandos abaixo |
| `data/processed/` (datasets, paineis, `projecao_anuncios.csv`) | Nao | Gerados pelos comandos abaixo |
| Modelo treinado (`*.pkl`) | Nao | `python main.py jacarei-train` |

## Como rodar tudo (reproducao completa)

**Pre-requisito:** a base do orientador e o Excel do FipeZAP nos caminhos acima. `python main.py verificar` mostra o que falta. Rode **na ordem**; os tempos sao desta maquina (so CPU).

| Etapa | Comando | Tempo | O que produz |
|---|---|---|---|
| **Dados** | `python main.py vivareal-prep` | curto | `apartamento.csv`, `casa.csv`, `residencial.csv` limpos (`data/processed/vivareal/`) e `reports/results/vivareal_limpeza.md` |
| | `python main.py series-coletar` | minutos | 14 series macro (BCB, IPEA, IBGE) pelas APIs publicas |
| | `python main.py series-fipezap` | curto | le o Excel do FipeZAP |
| | `python main.py series-painel` | curto | valida as series, testa vazamento temporal e gera os paineis mensal e trimestral (termina com erro se houver vazamento) |
| **Exploracao** | `python main.py eda-series`, `eda-vivareal` | curto | analise exploratoria (`docs/ANALISE_EXPLORATORIA.md`) |
| **Series temporais** | `python main.py arima` | ~45 s | ARIMA do FipeZAP com walk-forward (`docs/MODELOS_TEMPORAIS.md`) |
| | `python main.py arima-plus` | ~2 min | combinacao, ARIMAX e cidades vizinhas |
| | `python main.py lstm` | ~7 min | LSTM e gradient boosting em painel de 50 cidades (`docs/MODELOS_LSTM.md`) |
| **Precificacao** | `python main.py reg-linear` | curto | regressao linear por segmento (`docs/MODELOS_PRECIFICACAO.md`) |
| | `python main.py reg-geo` | minutos | coordenadas, vizinhos, setor IBGE, Censo e gradient boosting (`docs/ANALISE_GEOGRAFICA.md`) |
| | `python main.py ajuste-gb` | ~7 min | ajuste de parametros e importancia das variaveis |
| | `python main.py modelos-avancados` | **~70 min** | LightGBM/CatBoost, busca Optuna, conjunto e intervalos (`docs/MODELOS_AVANCADOS.md`) |
| **Analises finais** | `python main.py sensibilidade` | ~2,5 min | relevancia por grupo, cenarios "e se?", efeito do bairro (`docs/SENSIBILIDADE.md`) |
| | `python main.py projecao` | ~4 min | valor estimado de cada anuncio x tendencia do FipeZAP (`docs/PROJECAO_JACAREI.md`) |
| **Saidas** | `python main.py painel` | segundos | painel interativo (meta 8) |
| | `python main.py relatorio` | segundos | relatorio analitico (meta 9; `docs/RELATORIO_AUTOMATICO.md`) |

Outros comandos:

| Comando | O que faz |
|---|---|
| `python main.py publicar` | Monta `site/` (pagina inicial, painel e relatorio para a web) para o GitHub Pages (segundos). |
| `python main.py verificar` | Confere o ambiente, os dados e quais comandos podem rodar (nao altera nada). |
| `python main.py prever --segmento casa --bairro "Centro" --area 150 --quartos 3` | Avalia um imovel: valor estimado hoje, intervalos de 80% e 90% e projecao em 3, 6 e 12 meses (~40 s; precisa de `vivareal-prep` e `modelos-avancados`; `--help` lista as opcoes). |
| `python main.py mapa-setores` | Mapa de R$/m2 por setor censitario: PNG e HTML interativo. |
| `python main.py jacarei-train` | Treina o baseline Random Forest legado. |
| `python main.py` | Menu interativo. |
| `python main.py scrape`, `clean`, `stats`, `all` | Fluxo legado (coleta e limpeza do scraper). |

Os parametros e as sementes sao fixos: reexecutar reproduz os numeros (conferir em `reports/results/modelos_avancados.md`).

## Como testar que esta tudo certo

1. **Ambiente e dados:** `python main.py verificar` deve mostrar `OK` em todas as bibliotecas e nos dados de entrada.
2. **Teste rapido (segundos), com os resultados ja gerados:** `python main.py painel --abrir` e `python main.py relatorio --abrir`. No relatorio, o **Apendice C** deve dizer que
   todas as afirmacoes foram conferidas contra os numeros; no painel, nenhuma aba deve mostrar cartoes de aviso.
3. **Avaliar um imovel (~40 s):**
   ```bash
   python main.py prever --segmento casa --bairro "Loteamento Villa Branca" --area 150 --quartos 3 --suites 1 --vagas 2 --terreno 250
   ```
   Deve imprimir um valor estimado por m² (ordem de R$ 5.000 a 6.000 para esse exemplo), intervalos de 80% e 90% e a projecao em 3, 6 e 12 meses.
4. **Reproducao dos numeros:** depois de rodar `vivareal-prep` e `modelos-avancados`, o R² do conjunto final no teste temporal deve ser **~0,73 (apartamento), ~0,80 (casa) e ~0,81 (residencial)**.
5. **Vazamento temporal:** `python main.py series-painel` falha de proposito se algum painel usar informacao do futuro.

## Estrutura do projeto

```text
main.py                     ponto de entrada (comandos e menu)
src/
  scraper.py, cleaner.py, database.py, repository.py, stats.py, macro/
                            coleta e fluxo legado (nao usar o macro/ legado para modelar)
  vivareal/                 carga e limpeza da base do orientador por segmento
  pricing/                  precificacao: regressao linear, geografia/Censo, ajuste, modelos avancados,
                            projecao, prever (um imovel) e sensibilidade
  timeseries/               FipeZAP + macro: coleta por API, banco, validacao, paineis "as-of",
                            ARIMA, ARIMAX e LSTM em painel
  analysis/                 analise exploratoria e mapas por setor
  evaluation/               metricas e comparacao de modelos
  visualization/            painel interativo (meta 8)
  reporting/                relatorio analitico automatico (meta 9)
  verificar.py              checagem de ambiente e dados
data/
  raw/                      dados brutos de fontes publicas (nunca sobrescrever; a base do orientador nao e versionada)
  processed/                datasets, paineis e projecao (gerados)
reports/
  results/                  relatorios e tabelas geradas
  figures/                  figuras e HTML (painel interativo gerado)
  relatorio_analitico.md    relatorio final (gerado)
sql/queries/                consultas SQL de apoio
docs/                       metas, metodos, resultados e organizacao
```

## O que ler primeiro

- [`reports/relatorio_analitico.md`](reports/relatorio_analitico.md): o relatorio final (gerado), com a comparacao com a literatura.
- [`docs/METAS.md`](docs/METAS.md): metas, dados disponiveis e proximas etapas.
- [`docs/DIARIO_MODELAGEM.md`](docs/DIARIO_MODELAGEM.md): tecnicas, tratamento de dados faltantes, evolucao do R², tempos e problemas contornados (base do relatorio).
- [`docs/ANALISE_EXPLORATORIA.md`](docs/ANALISE_EXPLORATORIA.md): o que a analise mostrou e as decisoes para a modelagem.
- Precificacao: [`MODELOS_PRECIFICACAO`](docs/MODELOS_PRECIFICACAO.md), [`ANALISE_GEOGRAFICA`](docs/ANALISE_GEOGRAFICA.md), [`MODELOS_AVANCADOS`](docs/MODELOS_AVANCADOS.md), [`SENSIBILIDADE`](docs/SENSIBILIDADE.md), [`PROJECAO_JACAREI`](docs/PROJECAO_JACAREI.md).
- Series: [`SERIES_TEMPORAIS`](docs/SERIES_TEMPORAIS.md) (fontes, defasagens, vazamento), [`MODELOS_TEMPORAIS`](docs/MODELOS_TEMPORAIS.md) (ARIMA), [`MODELOS_LSTM`](docs/MODELOS_LSTM.md).
- Saidas: [`PAINEL_INTERATIVO`](docs/PAINEL_INTERATIVO.md), [`RELATORIO_AUTOMATICO`](docs/RELATORIO_AUTOMATICO.md), [`COMPARACAO_LITERATURA`](docs/COMPARACAO_LITERATURA.md).
- [`docs/AUDITORIA_VIVAREAL.md`](docs/AUDITORIA_VIVAREAL.md) e [`docs/ORGANIZACAO_REPOSITORIO.md`](docs/ORGANIZACAO_REPOSITORIO.md): qualidade da base e decisoes de organizacao.

## Paineis de series temporais

Os arquivos `painel_mensal.csv` e `painel_trimestral.csv` (em `data/processed/series/`) sao **"as-of"**: cada linha traz so o que ja estava publicado naquele mes. Use-os como
variaveis explicativas. Os `*_referencia.csv` alinham cada valor pela data a que ele se refere e servem **so para definir o alvo**.

## Baseline legado (Random Forest)

`python main.py jacarei-train` treina um `RandomForestRegressor` para prever `preco_m2` (alvo com `log1p`/`expm1`). E o baseline original de **precificacao de anuncios**, nao um modelo temporal.
Os artefatos em `data/models/jacarei/` (R² de 0,78 em 18.453 linhas) foram gerados com limites de limpeza mais largos que os atuais (`src/pricing/config.py`): **nao cite o R² de 0,78 como resultado atual**.
Os modelos oficiais do projeto sao os de `modelos-avancados` (comparacao com o Random Forest nas mesmas condicoes em `docs/MODELOS_PRECIFICACAO.md` e no relatorio).

## Limitacoes conhecidas

- A base do VivaReal e uma fotografia de anuncios ativos (precos **pedidos**), com vies de sobrevivencia; as datas de criacao nao formam uma serie de precos.
- O FipeZAP e media movel trimestral e **nao tem Jacarei** (Sao Jose dos Campos e a cidade coberta mais proxima); a projecao e uma premissa.
- Cinco defasagens de publicacao sao estimativas e o IBC-Br dessazonalizado e revisado pela fonte (ver `docs/SERIES_TEMPORAIS.md`).
- Lista completa e ameacas a validade: secao 8 do relatorio.

## Proximos passos

1. Confirmar com o orientador a unidade do IPTU (mediana de R$ 100 a R$ 150 por ano e suspeita) e o uso do FipeZAP de SJC como proxy.
2. Variaveis de qualidade do imovel e mais arquivos do Censo; snapshots periodicos do VivaReal para formar uma serie propria de Jacarei.
3. Ler os textos completos dos trabalhos comparados e replicar suas divisoes na base de Jacarei (`docs/COMPARACAO_LITERATURA.md`).
