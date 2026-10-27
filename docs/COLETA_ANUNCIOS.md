# Coleta de anuncios (ZAP Imoveis e VivaReal)

Data: 2026-10-26. Implementacao: `src/scraper.py`, `src/jsonld.py`; testes em `tests/` (`python -m unittest discover -s tests -t .`).

## Como funciona

- **Um worker por portal**, em paralelo (ZAP e VivaReal), com as **mesmas regras do coletor original**: fatias de preco por tipo (foco em casas e apartamentos; terrenos e "imoveis" so com `TIPOS=casas,apartamentos,terrenos`) para contornar o limite de
  paginas, retomada por pagina, espera de CAPTCHA (a pessoa resolve na janela) e atrasos de 8 a 15 s.
- **Leitura do JSON-LD** (schema.org) que a propria pagina traz: id, URL, tipo, rua, quartos, banheiros, area, comodidades, preco e data de publicacao (`datePosted`); bairro e vagas sao extraidos do titulo/`keywords`.
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
