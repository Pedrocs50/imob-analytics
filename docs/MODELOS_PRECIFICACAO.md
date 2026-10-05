# Modelos de precificacao: regressao linear multipla (meta 4, parte 1)

Data: 2026-10-02. Numeros e tabelas completos em `reports/results/regressao_linear.md`
(metricas e coeficientes em CSV em `reports/results/eda/regressao_linear_*.csv`;
figuras `reports/figures/reg_linear_*.png`).

```bash
python main.py reg-linear
```

Implementacao: `src/pricing/linear_regression.py`. Alvo: `preco_m2`, um modelo por
segmento (apartamento, casa, residencial) sobre `data/processed/vivareal/*.csv`.

## Metodo

- **Variaveis:** log da area, quartos, banheiros, suites, vagas, comodidades e
  bairro (bairros com menos de 30 anuncios no treino viram uma categoria unica);
  tipo (apartamento e residencial) ou `em_condominio` (casas). Ausentes imputados
  pela mediana com indicador de ausencia.
- **Fora do modelo:** IPTU (unidade nao confirmada), coordenadas (so ~48% dos
  anuncios as tem; ficam para uma etapa propria).
- **Variantes do condominio:** `base` (sem), `+ condominio informado`
  (indicador de que a taxa existe) e `+ valor do condominio`.
- **Alvo em nivel ou em log**, ambos avaliados na escala original (R$/m2).
- **Tres validacoes:** holdout aleatorio de 20%, 5-fold e divisao **temporal**
  (treino nos 75% de anuncios mais antigos, teste nos 25% mais recentes).
- **Baseline ingenuo:** mediana do R$/m2 do bairro no treino.
- **Coeficientes:** OLS em log(preco_m2) com erros-padrao robustos (HC3), porque
  o teste de Breusch-Pagan indica heterocedasticidade nos tres segmentos.

## Desempenho (alvo em nivel; R2 e MAE em R$/m2)

| Segmento | Variante | R2 holdout | R2 5-fold | R2 temporal | MAE temporal |
|---|---|---|---|---|---|
| apartamento | base | 0,44 | 0,48 | 0,49 | 1.012 |
| apartamento | + valor do condominio | 0,44 | 0,48 | 0,49 | 1.011 |
| apartamento | baseline (mediana do bairro) | 0,30 | 0,37 | 0,37 | 1.085 |
| casa | base | 0,61 | 0,60 | 0,58 | 975 |
| casa | + valor do condominio | 0,63 | 0,62 | 0,61 | 942 |
| casa | baseline (mediana do bairro) | 0,39 | 0,39 | 0,37 | 1.208 |
| residencial | base | 0,62 | 0,61 | 0,60 | 1.014 |
| residencial | + valor do condominio | 0,63 | 0,63 | 0,61 | 993 |
| residencial | baseline (mediana do bairro) | 0,33 | 0,34 | 0,33 | 1.339 |

## O que os resultados mostram

1. **A regressao melhora bem o baseline, mas explica pouco em apartamentos.** O R2
   fica em ~0,45 a 0,49 (erro medio de ~R$ 1.010/m2, ~17%) contra ~0,30 a 0,37 do
   baseline. Em casas e no residencial chega a 0,58 a 0,63. As variaveis
   disponiveis (area, comodos e bairro) deixam de fora o que mais diferencia
   anuncios: localizacao fina, idade e estado do imovel.
2. **A divisao temporal e semelhante a aleatoria** (o R2 temporal nao e menor), o
   que e um sinal de que a validacao aleatoria nao esta muito inflada por
   anuncios repetidos. Isso nao elimina o risco: anuncios do mesmo predio podem
   estar nos dois lados.
3. **Condominio:** em **apartamentos nao ajuda** (R2 igual com e sem). Em **casas
   o valor da taxa acrescenta ~0,03 de R2** (MAE cai ~35 R$/m2) alem do indicador
   `em_condominio`. O indicador `condominio_informado` sozinho nao melhora a
   previsao; o ganho vem do valor.
4. **Log ou nivel:** o alvo em nivel e ligeiramente melhor (0,01 a 0,03 de R2),
   coerente com a analise exploratoria (o `preco_m2` ja e razoavelmente simetrico).
5. **Residuos:** o modelo subestima os R$/m2 mais altos (regressao a media) e a
   variancia cresce com o preco (figuras `reg_linear_*.png`).

## Coeficientes (alvo log, variante `+ condominio informado`; efeito aproximado no R$/m2)

| Variavel | Apartamento | Casa |
|---|---|---|
| log da area (elasticidade) | -0,47 | -0,52 |
| por suite | +18% | +9% |
| por vaga | +13% | +4% |
| por quarto | ns | +6% |
| casa em condominio | - | +25% |
| suites ausentes (indicador) | -21% | -15% |
| efeitos de bairro vs. referencia | -22% a +54% | -23% a +90% |

Todos significativos a 1%, exceto os marcados "ns". Interpretacoes:

- Imoveis maiores tem R$/m2 menor (um imovel 10% maior tem ~5% menos R$/m2).
- **Anuncios sem informacao de suites tem R$/m2 menor.** A ausencia e informativa,
  possivelmente por padrao de preenchimento dos anunciantes e nao por uma
  caracteristica do imovel; tratar com cuidado.
- Os coeficientes sao associacoes, nao efeitos causais.

## Correcao feita durante o desenvolvimento

A primeira versao incluia, nas casas, tanto `tipo` quanto `em_condominio`, que
sao a mesma informacao (colinearidade perfeita). As previsoes nao mudavam, mas os
coeficientes dessas variaveis eram indeterminados (erro-padrao de 47). Cada
informacao agora entra uma unica vez.

## Atualizacao: modelos nao lineares e geografia

Este baseline linear ficou **abaixo do que os mesmos dados permitem**. Um gradient boosting com as
mesmas variaveis chega a R2 de 0,63 (apartamento) e 0,72 (casa), e com latitude, longitude e preco
dos vizinhos a 0,69, 0,73 e 0,74 (`docs/ANALISE_GEOGRAFICA.md`). Os numeros desta pagina continuam
validos como referencia linear interpretavel (coeficientes), nao como o melhor desempenho.

## Limitacoes e proximos passos

- Isto e um baseline linear. O Random Forest ainda precisa ser reavaliado **nos
  mesmos datasets e divisoes** para uma comparacao justa: o R2 de 0,78 dos
  artefatos antigos nao e comparavel (limpeza diferente, sem remocao de
  duplicatas, possivel vazamento por duplicatas).
- Coordenadas foram avaliadas depois (`docs/ANALISE_GEOGRAFICA.md`): ajudam muito em
  apartamentos, mas so ~48% dos anuncios as tem.
- Confirmar a unidade do IPTU antes de testa-lo.
- Falta o lado temporal da meta 4: ARIMA no FipeZAP nacional (`d = 2`).
