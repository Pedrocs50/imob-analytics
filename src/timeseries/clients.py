from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.timeseries.catalogo import SerieMacro
from src.timeseries.config import RAW_MACRO_DIR

INICIO_PADRAO = date(2005, 1, 1)
JANELA_SGS_DIAS = 1800  # janelas >= ~3000 dias falham de forma intermitente no SGS; 1800 passou sempre


class ColetaErro(RuntimeError):
    """Falha de coleta. A mensagem inclui o que a API respondeu."""


def _numero(bruto) -> float | None:
    if bruto is None:
        return None
    txt = str(bruto).strip()
    if txt in ("", "...", "-", "..", "X", "null", "None"):
        return None
    if "," in txt and "." in txt:
        txt = txt.replace(".", "").replace(",", ".")
    elif "," in txt:
        txt = txt.replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


def _sessao() -> requests.Session:
    sessao = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retries)
    sessao.mount("http://", adapter)
    sessao.mount("https://", adapter)
    return sessao


def _json(sessao: requests.Session, url: str, params: dict | None = None, tentativas: int = 4):
    ultimo_erro = ""
    for tentativa in range(1, tentativas + 1):
        resp = sessao.get(url, params=params, timeout=90)
        if not resp.ok:
            raise ColetaErro(f"HTTP {resp.status_code} em {resp.url}")
        tipo = resp.headers.get("content-type", "")
        if "json" in tipo:
            return resp.json()
        # o BCB responde 200 com uma pagina HTML quando recusa a requisicao (as vezes de
        # forma intermitente): repete algumas vezes antes de desistir
        trecho = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", resp.text)).strip()[:160]
        ultimo_erro = f"resposta nao-JSON ({tipo}) em {resp.url}: {trecho}"
        time.sleep(2 * tentativa)
    raise ColetaErro(f"{ultimo_erro} (apos {tentativas} tentativas)")


def salvar_bruto(serie: SerieMacro, conteudo, raw_dir: str = RAW_MACRO_DIR) -> str:
    """Grava a resposta original da API. Cada coleta gera um arquivo novo."""
    pasta = os.path.join(raw_dir, serie.fonte.lower())
    os.makedirs(pasta, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = os.path.join(pasta, f"{serie.id}_{carimbo}.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False)
    return caminho


def _data_bcb(texto: str) -> date:
    return datetime.strptime(texto, "%d/%m/%Y").date()


def coletar_bcb(sessao: requests.Session, serie: SerieMacro) -> tuple[list[tuple[date, float]], object]:
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie.codigo}/dados"
    if serie.diaria:
        brutos: list[dict] = []
        atual, hoje = INICIO_PADRAO, date.today()
        while atual <= hoje:
            fim = min(atual + timedelta(days=JANELA_SGS_DIAS), hoje)
            params = {
                "formato": "json",
                "dataInicial": atual.strftime("%d/%m/%Y"),
                "dataFinal": fim.strftime("%d/%m/%Y"),
            }
            brutos.extend(_json(sessao, url, params))
            atual = fim + timedelta(days=1)
    else:
        brutos = _json(sessao, url, {"formato": "json"})

    if not isinstance(brutos, list) or not brutos:
        raise ColetaErro(f"serie {serie.codigo} do BCB voltou vazia")

    pontos = {}
    for linha in brutos:
        valor = _numero(linha.get("valor"))
        if valor is not None:
            pontos[_data_bcb(linha["data"])] = valor
    return sorted(pontos.items()), brutos


def coletar_ipea(sessao: requests.Session, serie: SerieMacro) -> tuple[list[tuple[date, float]], object]:
    url = f"http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{serie.codigo}')"
    dados = _json(sessao, url)
    linhas = dados.get("value", []) if isinstance(dados, dict) else []
    if not linhas:
        raise ColetaErro(f"serie {serie.codigo} do IPEA voltou vazia (codigo inexistente?)")

    pontos = {}
    for linha in linhas:
        valor = _numero(linha.get("VALVALOR"))
        data_txt = str(linha.get("VALDATA", ""))[:10]
        if valor is None or not data_txt:
            continue
        pontos[datetime.strptime(data_txt, "%Y-%m-%d").date()] = valor
    return sorted(pontos.items()), dados


def _data_periodo_sidra(codigo: str, frequencia: str) -> date:
    """Periodos do SIDRA: trimestrais como AAAAQQ (201203 = 3o trimestre de 2012) e
    mensais como AAAAMM. O mesmo codigo pode ser lido das duas formas, entao a
    frequencia declarada da serie decide. Retorna o primeiro dia do periodo."""
    digitos = re.sub(r"\D", "", str(codigo))
    if len(digitos) != 6:
        raise ColetaErro(f"periodo SIDRA inesperado: {codigo!r}")
    ano, sufixo = int(digitos[:4]), int(digitos[4:])
    if not 1990 <= ano <= 2100:
        raise ColetaErro(f"ano implausivel no periodo SIDRA {codigo!r}")
    if frequencia == "Q":
        if not 1 <= sufixo <= 4:
            raise ColetaErro(f"trimestre invalido no periodo SIDRA {codigo!r}")
        return date(ano, (sufixo - 1) * 3 + 1, 1)
    if not 1 <= sufixo <= 12:
        raise ColetaErro(f"mes invalido no periodo SIDRA {codigo!r}")
    return date(ano, sufixo, 1)


def coletar_sidra(sessao: requests.Session, serie: SerieMacro) -> tuple[list[tuple[date, float]], object]:
    url = f"https://apisidra.ibge.gov.br/values/{serie.sidra_path}"
    linhas = _json(sessao, url)
    if not isinstance(linhas, list) or len(linhas) < 2:
        raise ColetaErro(f"SIDRA sem dados para {serie.sidra_path}")

    cabecalho, dados = linhas[0], linhas[1:]
    # a coluna do periodo e identificada pelo nome do cabecalho, nunca pelo formato do valor
    col_periodo = next(
        (k for k, v in cabecalho.items() if k.startswith("D") and k.endswith("C")
         and str(v).lower().startswith(("trimestre", "mês", "mes"))),
        None,
    )
    col_variavel = next(
        (k for k, v in cabecalho.items() if k.startswith("D") and k.endswith("C")
         and str(v).lower().startswith("variável")),
        None,
    )
    if col_periodo is None or col_variavel is None:
        raise ColetaErro(f"cabecalho SIDRA sem coluna de periodo/variavel: {cabecalho}")

    pontos = {}
    for linha in dados:
        if str(linha.get(col_variavel)) != str(serie.sidra_variavel):
            continue
        valor = _numero(linha.get("V"))
        if valor is None:
            continue
        pontos[_data_periodo_sidra(linha[col_periodo], serie.frequencia)] = valor
    if not pontos:
        raise ColetaErro(f"variavel {serie.sidra_variavel} nao encontrada em {serie.sidra_path}")
    return sorted(pontos.items()), linhas


COLETORES = {"BCB": coletar_bcb, "IPEA": coletar_ipea, "IBGE_SIDRA": coletar_sidra}


def coletar(serie: SerieMacro, sessao: requests.Session | None = None):
    """Coleta uma serie. Retorna (pontos [(data, valor)], resposta_bruta)."""
    return COLETORES[serie.fonte](sessao or _sessao(), serie)
