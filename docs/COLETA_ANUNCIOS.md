# Coleta de anuncios (ZAP Imoveis e VivaReal)

Data: 2026-10-26. Implementacao: `src/scraper.py`, `src/jsonld.py`; testes em `tests/` (`python -m unittest discover -s tests -t .`).

## Como funciona

- **Um worker por portal**, em paralelo (ZAP e VivaReal), com as **mesmas regras do coletor original**: fatias de preco por tipo (foco em casas e apartamentos; terrenos e "imoveis" so com `TIPOS=casas,apartamentos,terrenos`) para contornar o limite de
  paginas, retomada por pagina, espera de CAPTCHA (a pessoa resolve na janela) e atrasos de 8 a 15 s.
- **Leitura do JSON-LD** (schema.org) que a propria pagina traz: id, URL, tipo, rua, quartos, banheiros, area, comodidades, preco e data de publicacao (`datePosted`); bairro e vagas sao extraidos do titulo/`keywords`.
- **Campos guardados por anuncio** (`imoveis_raw`): fonte, id, URL, rua, bairro, preco, area, quartos, banheiros, vagas, comodidades, data de publicacao, condominio (taxa do JSON-LD, completada pelo card), IPTU (card), tipo do imovel (`additionalType`: House, Apartment...), numero de comodos, aceita pets, disponibilidade, numero de fotos e destaque ("destaque"/"super destaque", do card) e o **JSON-LD bruto do anuncio** (`json_ld`), para minerar campos que ainda nao foram usados sem recoletar. Ficam de fora, de proposito: imagens, nome do anunciante e telefones (dado de terceiros).
  Condominio e IPTU vem dos cards, ligados ao anuncio pelo id do link. Sem JSON-LD, volta para os cards.
- **Nao guarda** nome, telefone nem identificacao do anunciante.
- **`robots.txt`** lido pelo navegador; caminhos proibidos sao pulados.
- **Navegador:** Chrome com `undetected_chromedriver`, perfil proprio por portal em `data/chrome_profile/` (cookies da sessao persistem). Configuravel por `CHROME_BIN`, `CHROMEDRIVER`, `CHROME_VERSION`,
  `CAPTCHA_MAX_WAIT` (padrao 300 s) e `ESPERA_CARREGAMENTO` (padrao 40 s).
- **Se o navegador cair:** `_tentar` reinicia e repete a pagina (3 tentativas), e o log diz se o processo do Chrome foi encerrado (janela fechada) ou se ficou vivo (travado/lento).
- **Modo HTTP** (`--http`): baixa o HTML da listagem e le o JSON-LD, sem navegador. Se o portal responder 403/429 ou com desafio, **para e avisa**; nada e contornado.
- **Deduplicacao:** dentro do portal, por (fonte, id); entre portais, no `DataCleaner`: mesma rua, area, quartos e banheiros com preco ate 3% diferente (o preco entra para nao juntar
  apartamentos iguais do mesmo predio).

## Comandos

```fish
env CHROME_BIN=/usr/bin/google-chrome-stable python main.py scrape --amostra   # 1 pagina por tipo, sem gravar no banco; salva JSON-LD e contagens em data/raw/amostras_scraper/
python main.py scrape --http --amostra                                         # o mesmo, por HTTP (sem navegador)
env CHROME_BIN=/usr/bin/google-chrome-stable python main.py scrape             # coleta completa (retomavel)
python main.py clean                                                           # limpa e junta os dois portais
```

## O que a amostra real mostrou (2026-10-26)

- **VivaReal:** 30 anuncios no JSON-LD e 30 cards na tela, em casas e apartamentos; ids unicos; preco, area, quartos e banheiros em 30/30. Rua ausente em 3/30 e vagas em 7-8/30 (anunciante nao informa).
  O JSON-LD **nao traz latitude/longitude**.
- **ZAP:** o navegador caiu durante a amostra e o arquivo de JSON-LD veio vazio; o diagnostico acima e o `segundos_ate_carregar` do resumo da amostra servem para separar carregamento lento de janela fechada.
- Por HTTP simples, os dois portais responderam 403 nesta maquina de desenvolvimento.

## Limites

- Uma coleta e uma **fotografia**: para uma serie de precos de Jacarei no LSTM e preciso repetir a coleta periodicamente, guardando data e id.
- Termos de uso dos portais nao foram revisados; o uso em volume deve respeitar as regras de cada site.

## Bloqueio do Cloudflare ("Sorry, you have been blocked")

Diferente do CAPTCHA (que pede uma verificacao que voce resolve na janela), esta pagina **nega o acesso**. Em 2026-10-26 apareceu nos dois portais depois de varias rodadas seguidas de `--amostra` e de testes automatizados. O coletor reconhece a pagina, **para o portal na hora**, avisa no log e preserva o que ja foi gravado (a coleta retoma de onde parou). O projeto **nao tenta contornar** (sem proxy, sem trocar de IP, sem esconder o navegador): o bloqueio expira com o tempo; rodar de novo com menos pressa (`DELAY_MIN`/`DELAY_MAX` maiores) e evitar rodadas repetidas ajuda. Se persistir, usar a base compartilhada pelo orientador (marco/2026) ou dados abertos (ITBI).

## Diario da coleta (2026-10-26)

1. **Janelas caindo:** causa = segfault do chromedriver remendado pelo `undetected_chromedriver` (`journalctl -k`, 13 em 3 h). Solucao: Selenium puro (padrao; `NAVEGADOR=uc` volta ao antigo), encerramento do Chrome preso ao perfil e diagnostico "chromedriver morreu".
2. **ZAP terrenos "pagina nao encontrada":** a pagina de erro mostra anuncios recomendados, que seriam gravados como se fossem da listagem. Solucao: deteccao da pagina de erro, caminhos candidatos (`lotes-terrenos`, `terrenos`).
3. **Foco:** apenas casas e apartamentos (9 faixas de preco); outros tipos so com `TIPOS=`.
4. **Condominio/IPTU lidos em 2 de 30 cards:** o leitor subia so 8 niveis e usava `innerText`. Solucao: maior bloco com um unico preco + `textContent`. Falta conferir na pagina real (precisa de nova amostra apos o bloqueio expirar).
5. **Amostra limpa nos dois portais:** 30 anuncios no JSON-LD = 30 cards, sem queda, sem CAPTCHA. ZAP e VivaReal repetem os mesmos anuncios (mesmo grupo): o `clean` deduplica por rua, area, quartos, banheiros e preco.
6. **Bloqueio do Cloudflare nos dois portais** depois de varias rodadas seguidas (incluindo testes automatizados nossos). O coletor agora para na hora; nada foi contornado. Proximo passo: esperar expirar e rodar uma coleta unica (`python main.py scrape`), depois `python main.py clean`.
