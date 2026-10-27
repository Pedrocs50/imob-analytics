import json
import re
import signal
import requests
import time
import os
import random
import multiprocessing
import urllib.robotparser

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from urllib3.exceptions import HTTPError
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.database import Database
from src.jsonld import blocos_do_html, extrair_anuncios, valores_do_card
from src.repository import DataRepository


# =============================================================================
# CONFIGURACOES CENTRALIZADAS
# =============================================================================

# Sem variavel de ambiente, usa o Chrome instalado no sistema e detecta a versao sozinho.
CHROME_BIN_PATH = os.environ.get("CHROME_BIN")  # ex.: /usr/bin/google-chrome
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER")
CHROME_VERSION = int(os.environ["CHROME_VERSION"]) if os.environ.get("CHROME_VERSION") else None
DELAY_MIN = 8  # segundos minimos entre paginas
DELAY_MAX = 15  # segundos maximos entre paginas
MAX_PAGINAS = 400  # limite seguro por segmento antes de bloqueio do portal

# para evitar o capcha infinito, ja que estava tentando esperar uma liberação que não existe
CAPTCHA_MAX_WAIT = int(os.environ.get("CAPTCHA_MAX_WAIT", 300))  # segundos para voce resolver na janela aberta
CAPTCHA_POLL = 3  # segundos

# perfil do navegador por portal: cookies da sessao (inclusive depois de resolver um CAPTCHA a mao) persistem entre execucoes
PERFIL_DIR = os.environ.get("PERFIL_NAVEGADOR_DIR", os.path.join("data", "chrome_profile"))
# modo HTTP: baixa o HTML da listagem e le o JSON-LD, sem navegador. Ritmo proprio e identificacao honesta.
HTTP_DELAY_MIN = float(os.environ.get("HTTP_DELAY_MIN", 2))
HTTP_DELAY_MAX = float(os.environ.get("HTTP_DELAY_MAX", 4))
HTTP_TIMEOUT = 30
USER_AGENT = os.environ.get(
    "SCRAPER_USER_AGENT", "imob-analytics/1.0 (pesquisa de iniciacao cientifica, IFSP Jacarei)"
)
# Navegador: Selenium puro com o chromedriver oficial (padrao). O undetected_chromedriver (NAVEGADOR=uc) remenda o binario do
# chromedriver e, no Chrome 156 deste projeto, ele deu segfault repetidamente (journalctl -k): o driver morria e o Chrome ficava vivo.
NAVEGADOR = os.environ.get("NAVEGADOR", "selenium")
SEM_JANELA = os.environ.get("NAVEGADOR_SEM_JANELA") == "1"  # para testes; a coleta normal usa janela visivel
# quanto esperar a listagem aparecer (o ZAP monta a pagina no navegador e pode demorar mais que o VivaReal)
ESPERA_CARREGAMENTO = int(os.environ.get("ESPERA_CARREGAMENTO", 40))
AMOSTRAS_DIR = os.path.join("data", "raw", "amostras_scraper")
CARD_PRECO_CSS = '[data-cy="rp-cardProperty-price-txt"]'

# fatias do catalogo para driblar o limite de paginas que stava dando menos de 50 por pagina
SEGMENTOS = [
    {"tipo": "casas", "preco_min": 0, "preco_max": 300_000},
    {"tipo": "casas", "preco_min": 300_000, "preco_max": 600_000},
    {"tipo": "casas", "preco_min": 600_000, "preco_max": 1_000_000},
    {"tipo": "casas", "preco_min": 1_000_000, "preco_max": 2_000_000},
    {"tipo": "casas", "preco_min": 2_000_000, "preco_max": 99_999_999},
    {"tipo": "apartamentos", "preco_min": 0, "preco_max": 300_000},
    {"tipo": "apartamentos", "preco_min": 300_000, "preco_max": 600_000},
    {"tipo": "apartamentos", "preco_min": 600_000, "preco_max": 1_000_000},
    {"tipo": "apartamentos", "preco_min": 1_000_000, "preco_max": 99_999_999},
    {"tipo": "terrenos", "preco_min": 0, "preco_max": 200_000},
    {"tipo": "terrenos", "preco_min": 200_000, "preco_max": 99_999_999},
    {"tipo": "imoveis", "preco_min": 0, "preco_max": 500_000},
    {"tipo": "imoveis", "preco_min": 500_000, "preco_max": 99_999_999},
]

# Um worker por portal: sites diferentes em paralelo, cada um com seu proprio ritmo.
# `caminho`: parte da URL por tipo; `parametros`: nomes dos filtros. O ZAP e o que ja funcionava;
# os do VivaReal seguem o mesmo padrao e devem ser conferidos com `python main.py scrape --amostra`.
PORTAIS = {
    "zap": {
        "base": "https://www.zapimoveis.com.br",
        "url": "{base}/venda/{caminho}/sp+jacarei/?{pagina_param}={pagina}&precoMinimo={preco_min}&precoMaximo={preco_max}",
        # lista = caminhos candidatos: vale o primeiro que nao cair na pagina "nao encontrada" (conferido na amostra)
        "caminhos": {"casas": "casas", "apartamentos": "apartamentos", "terrenos": ["lotes-terrenos", "terrenos"],
                     "imoveis": "imoveis"},
        "pagina_param": "page",
    },
    "vivareal": {
        "base": "https://www.vivareal.com.br",
        "url": "{base}/venda/sp/jacarei/{caminho}?{pagina_param}={pagina}&precoMinimo={preco_min}&precoMaximo={preco_max}",
        "caminhos": {"casas": "casa_residencial/", "apartamentos": "apartamento_residencial/",
                     "terrenos": "lote-terreno_residencial/", "imoveis": ""},
        "pagina_param": "pagina",
    },
}


# =============================================================================
# EXTRACTOR
# =============================================================================

_PAGINA_NAO_ENCONTRADA = re.compile(
    r"encontrar\s+a\s+p[áa]gina\s+solicitada|p[áa]gina\s+n[ãa]o\s+(foi\s+)?encontrada|page\s+not\s+found", re.IGNORECASE)


def pagina_de_erro(texto: str) -> bool:
    return bool(_PAGINA_NAO_ENCONTRADA.search(texto))


class ExtractorPortal:
    """Le os anuncios de uma pagina de listagem. Prefere o JSON-LD embutido (id, URL, endereco, comodidades);
    se a pagina nao trouxer, volta para os cards (so o que aparece na tela)."""

    _SELETORES = {
        "preco": CARD_PRECO_CSS,
        "endereco": '[data-cy="rp-cardProperty-location-txt"]',
        "area": '[data-cy="rp-cardProperty-propertyArea-txt"]',
        "quartos": '[data-cy="rp-cardProperty-bedroomQuantity-txt"]',
        "banheiros": '[data-cy="rp-cardProperty-bathroomQuantity-txt"]',
        "vagas": '[data-cy="rp-cardProperty-parkingSpacesQuantity-txt"]',
    }

    _CARDS_CSS = 'div[class*="content-stretch"][class*="min-w-0"]'
    _JSON_LD_JS = "return [...document.querySelectorAll('script[type=\"application/ld+json\"]')].map(s => s.textContent);"

    # texto de cada card ligado ao id do anuncio: sobe a partir do preco ate o menor elemento com o link do anuncio
    _CARDS_TEXTO_JS = """return [...document.querySelectorAll('[data-cy="rp-cardProperty-price-txt"]')].map(p => {
        let n = p;
        for (let i = 0; i < 8 && n; i++) {
            const a = n.querySelector && n.querySelector('a[href*="-id-"]');
            if (a) return n.querySelectorAll('[data-cy="rp-cardProperty-price-txt"]').length === 1 ? {href: a.href, texto: n.innerText} : null;
            n = n.parentElement;
        }
        return null;
    }).filter(Boolean);"""

    def __init__(self, fonte: str):
        self._fonte = fonte

    def exemplos_de_cards(self, driver, n: int = 3) -> list[str]:
        """Texto cru dos primeiros cards (preco, endereco, caracteristicas): para conferir o que o card mostra de condominio/IPTU."""
        try:
            cards = driver.execute_script(self._CARDS_TEXTO_JS) or []
        except Exception:
            return []
        return [" | ".join(str(c.get("texto", "")).split())[:400] for c in cards[:n] if isinstance(c, dict)]

    def valores_dos_cards(self, driver) -> dict[str, dict]:
        """{id do anuncio: {condominio, iptu}}: esses dois so aparecem nos cards, nao no JSON-LD."""
        try:
            cards = driver.execute_script(self._CARDS_TEXTO_JS) or []
        except Exception:
            return {}
        saida = {}
        for c in cards:
            if not isinstance(c, dict):
                continue
            achado = re.search(r"id-(\d+)", c.get("href", ""))
            if achado:
                saida[achado.group(1)] = valores_do_card(c.get("texto", ""))
        return saida

    def blocos_json_ld(self, driver) -> list[str]:
        try:
            return driver.execute_script(self._JSON_LD_JS) or []
        except Exception:
            return []

    def extrair_pagina(self, driver, segmento: dict, pagina: int) -> list[dict]:
        self._aguardar_carregamento(driver)
        anuncios = extrair_anuncios(self.blocos_json_ld(driver))
        if anuncios:
            cards = self.valores_dos_cards(driver)
            for a in anuncios:
                a.update(cards.get(a["external_id"], {}))
        if not anuncios:
            self._rolar_pagina(driver)
            anuncios = [d for d in (self._extrair_card(c) for c in driver.find_elements(By.CSS_SELECTOR, self._CARDS_CSS)) if d]
        for a in anuncios:
            a.update({"fonte": self._fonte, "segmento": f"{self._fonte}:{segmento['tipo']}",
                      "preco_min_filtro": segmento["preco_min"], "pagina": pagina})
        return anuncios

    _TEXTO_PAGINA_JS = "return (document.title + ' | ' + (document.body ? document.body.innerText : '')).slice(0, 3000);"

    def texto_da_pagina(self, driver) -> str:
        try:
            return str(driver.execute_script(self._TEXTO_PAGINA_JS) or "")
        except Exception:
            return ""

    def pagina_nao_encontrada(self, driver) -> bool:
        """Pagina de erro do portal ("nao conseguimos encontrar a pagina solicitada"). Ela mostra anuncios
        recomendados, que NAO sao desta listagem e nao podem ser gravados como se fossem."""
        return pagina_de_erro(self.texto_da_pagina(driver))

    def pagina_tem_resultados(self, driver) -> bool:
        try:
            if self.pagina_nao_encontrada(driver):
                return False
            if extrair_anuncios(self.blocos_json_ld(driver)):
                return True
            return len(driver.find_elements(By.CSS_SELECTOR, self._CARDS_CSS)) > 0
        except Exception:
            return False

    def contagens(self, driver) -> dict:
        """Numeros para conferir se o JSON-LD traz todos os anuncios que a pagina mostra."""
        blocos = self.blocos_json_ld(driver)
        return {"blocos_json_ld": len(blocos), "anuncios_no_json_ld": len(extrair_anuncios(blocos)),
                "cards_na_tela": len(driver.find_elements(By.CSS_SELECTOR, CARD_PRECO_CSS))}

    def _aguardar_carregamento(self, driver) -> float | None:
        """Espera os anuncios aparecerem (card de preco ou JSON-LD com anuncios). Devolve os segundos esperados, ou None no timeout."""
        inicio = time.time()
        try:
            WebDriverWait(driver, ESPERA_CARREGAMENTO).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, self._SELETORES["preco"]) or extrair_anuncios(self.blocos_json_ld(d))
            )
            return round(time.time() - inicio, 1)
        except Exception:
            return None

    def _rolar_pagina(self, driver) -> None:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1.5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

    def _extrair_card(self, card) -> dict | None:
        try:
            preco = card.find_element(By.CSS_SELECTOR, self._SELETORES["preco"]).text.replace("\n", " ").strip()
        except Exception:
            return None

        def get(campo):
            try:
                return card.find_element(By.CSS_SELECTOR, self._SELETORES[campo]).text
            except Exception:
                return "N/A"

        return {"endereco": get("endereco"), "preco": preco, "area": get("area"), "quartos": get("quartos"),
                "banheiros": get("banheiros"), "vagas": get("vagas")}


# =============================================================================
# SCRAPER
# =============================================================================

def encerrar_chrome_do_perfil(perfil: str, espera: float = 3.0) -> int:
    """Encerra os Chrome que ainda seguram `perfil` (sobras de uma queda ou de Ctrl+C) e limpa as travas do perfil.
    Sem isso, o Chrome novo abre no processo antigo, e o driver perde o navegador. So olha processos com este perfil."""
    if not os.path.isdir("/proc"):
        return 0
    alvo, encerrados = f"--user-data-dir={perfil}", []
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                argumentos = f.read().split(b"\0")
        except OSError:
            continue
        if int(pid) != os.getpid() and alvo.encode() in argumentos:
            try:
                os.kill(int(pid), signal.SIGTERM)
                encerrados.append(int(pid))
            except OSError:
                pass
    limite = time.time() + espera
    while encerrados and time.time() < limite and any(os.path.exists(f"/proc/{p}") for p in encerrados):
        time.sleep(0.2)
    for p in encerrados:
        if os.path.exists(f"/proc/{p}"):
            try:
                os.kill(p, signal.SIGKILL)
            except OSError:
                pass
    for trava in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        try:
            os.unlink(os.path.join(perfil, trava))
        except OSError:
            pass
    return len(encerrados)


def caminhos_candidatos(portal: dict, tipo: str) -> list[str]:
    caminho = portal["caminhos"][tipo]
    return list(caminho) if isinstance(caminho, (list, tuple)) else [caminho]


def montar_url(portal: dict, segmento: dict, pagina: int, caminho: str | None = None) -> str:
    return portal["url"].format(
        base=portal["base"], caminho=caminho if caminho is not None else caminhos_candidatos(portal, segmento["tipo"])[0],
        pagina_param=portal["pagina_param"],
        pagina=pagina, preco_min=segmento["preco_min"], preco_max=segmento["preco_max"],
    )


def robots_do_texto(base: str, texto: str) -> urllib.robotparser.RobotFileParser:
    rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
    rp.parse(texto.splitlines())
    return rp


class ScraperPortal:
    def __init__(self, worker_id: int, fonte: str, segmentos: list[dict], fila_progresso, db_path: str, trava_driver=None):
        self.worker_id = worker_id
        self.fonte = fonte
        self._trava_driver = trava_driver
        self.portal = PORTAIS[fonte]
        self.segmentos = segmentos
        self.fila_progresso = fila_progresso
        self._db = Database(db_path)
        self._repo = DataRepository(self._db)
        self._extractor = ExtractorPortal(fonte)
        self._driver = None
        self._robots = None
        self._caminhos: dict[str, str] = {}  # tipo -> caminho que funcionou

    def _url(self, segmento: dict, pagina: int) -> str:
        return montar_url(self.portal, segmento, pagina, self._caminhos.get(segmento["tipo"]))

    def _escolher_caminho(self, segmento: dict) -> bool:
        """Define o caminho da URL do tipo: o primeiro candidato cuja pagina 1 nao e de erro. False se nenhum serve."""
        tipo = segmento["tipo"]
        if tipo in self._caminhos:
            return True
        candidatos = caminhos_candidatos(self.portal, tipo)
        for caminho in candidatos:
            url = montar_url(self.portal, segmento, 1, caminho)
            if not self._permitido(url):
                continue
            self._driver.get(url)
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            if not self._extractor.pagina_tem_resultados(self._driver) and self._detectar_captcha():
                self._aguardar_liberacao_captcha()
            self._extractor._aguardar_carregamento(self._driver)
            if not self._extractor.pagina_nao_encontrada(self._driver):
                self._caminhos[tipo] = caminho
                if len(candidatos) > 1:
                    self._log(f"{tipo}: caminho '{caminho}' funciona ({url})")
                return True
            self._log(f"{tipo}: o portal respondeu 'pagina nao encontrada' para {url}")
        return False

    def executar(self) -> None:
        self._iniciar_driver()
        try:
            self._ler_robots()
            for segmento in self.segmentos:
                self._scrape_segmento(segmento)
        except KeyboardInterrupt:
            self._log("Interrompido.")
        finally:
            if self._driver is not None:
                self._driver.quit()
            self._log("Navegador fechado.")

    def executar_amostra(self) -> None:
        """Uma pagina por tipo (primeira faixa de preco): grava o JSON-LD bruto e as contagens, sem tocar no banco.
        Serve para conferir as URLs do portal e a cobertura do JSON-LD sem coleta em volume."""
        self._iniciar_driver()
        os.makedirs(AMOSTRAS_DIR, exist_ok=True)
        resumo = {}
        try:
            self._ler_robots()
            for segmento in [s for s in self.segmentos if s["preco_min"] == 0]:
                url = montar_url(self.portal, segmento, 1)
                if not self._permitido(url):
                    resumo[segmento["tipo"]] = {"url": url, "erro": "bloqueado pelo robots.txt"}
                    continue
                try:
                    if not self._tentar(lambda: self._escolher_caminho(segmento)):
                        resumo[segmento["tipo"]] = {"url": url, "erro": "pagina nao encontrada em todos os caminhos testados: "
                                                    + ", ".join(caminhos_candidatos(self.portal, segmento["tipo"]))}
                        self._log(f"amostra {segmento['tipo']}: {resumo[segmento['tipo']]}")
                        continue
                    url = self._url(segmento, 1)
                    resumo[segmento["tipo"]] = self._tentar(lambda: self._amostrar(segmento, url))
                except Exception as erro:
                    resumo[segmento["tipo"]] = {"url": url, "erro": f"{type(erro).__name__}: {erro}"[:300]}
                self._log(f"amostra {segmento['tipo']}: {resumo[segmento['tipo']]}")
        finally:
            if self._driver is not None:
                self._driver.quit()
        with open(os.path.join(AMOSTRAS_DIR, f"{self.fonte}_resumo.json"), "w", encoding="utf-8") as f:
            json.dump(resumo, f, ensure_ascii=False, indent=2)

    def _amostrar(self, segmento: dict, url: str) -> dict:
        self._driver.get(url)
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        if not self._extractor.pagina_tem_resultados(self._driver) and self._detectar_captcha():
            self._aguardar_liberacao_captcha()
        espera = self._extractor._aguardar_carregamento(self._driver)
        blocos = self._extractor.blocos_json_ld(self._driver)
        arquivo = os.path.join(AMOSTRAS_DIR, f"{self.fonte}_{segmento['tipo']}_p1.json")
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(blocos, f, ensure_ascii=False)
        return {"url": self._driver.current_url, "pagina_nao_encontrada": self._extractor.pagina_nao_encontrada(self._driver),
                "titulo": self._driver.title, "arquivo": arquivo,
                "exemplos_de_cards": self._extractor.exemplos_de_cards(self._driver), "segundos_ate_carregar": espera,
                "timeout_de_carregamento": espera is None, "captcha_visivel": self._detectar_captcha(),
                **self._extractor.contagens(self._driver),
                "cards_com_condominio_ou_iptu": sum(1 for v in self._extractor.valores_dos_cards(self._driver).values()
                                                    if v["condominio"] is not None or v["iptu"] is not None)}

    def _tentar(self, funcao, tentativas: int = 3):
        """Executa uma etapa com o navegador; se ele cair (fechado, travado), reinicia e repete."""
        for numero in range(1, tentativas + 1):
            try:
                return funcao()
            except (WebDriverException, HTTPError, ConnectionError) as erro:
                self._log(f"navegador caiu ({type(erro).__name__}: {str(erro).splitlines()[0][:100] if str(erro) else ''}); "
                          f"{self._diagnostico_navegador()}; reiniciando ({numero}/{tentativas})")
                if numero == tentativas:
                    raise
                self._reiniciar_driver()

    def _diagnostico_navegador(self) -> str:
        """Separa 'a janela foi fechada / o Chrome morreu' de 'o Chrome esta vivo mas nao responde'."""
        def vivo(pid):
            try:
                os.kill(pid, 0)
                return True
            except ProcessLookupError:
                return False
            except PermissionError:
                return True

        pid = getattr(self._driver, "browser_pid", None)  # so o undetected_chromedriver expoe o pid do Chrome
        pid_driver = getattr(getattr(getattr(self._driver, "service", None), "process", None), "pid", None)
        if isinstance(pid_driver, int) and not vivo(pid_driver):
            return (f"o chromedriver (pid {pid_driver}) MORREU: crash do driver (veja `journalctl -k | grep segfault`); "
                    "o Chrome pode ter ficado vivo")
        if not pid:
            return "pid do Chrome desconhecido"
        if vivo(pid):
            return f"o processo do Chrome (pid {pid}) ainda existe: travou ou esta lento, nao foi fechado"
        return f"o processo do Chrome (pid {pid}) NAO existe mais: a janela foi fechada ou o Chrome morreu"

    def _reiniciar_driver(self) -> None:
        try:
            self._driver.quit()
        except Exception:
            pass
        encerrar_chrome_do_perfil(self._perfil)
        time.sleep(3)
        self._iniciar_driver()

    def _coletar_pagina(self, segmento: dict, pagina: int, url: str):
        """Uma pagina da listagem. Devolve os anuncios, ou None quando o segmento acabou."""
        self._driver.get(url)
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        # Recheca cards para evitar falso "fim de segmento"
        if not self._extractor.pagina_tem_resultados(self._driver):
            if self._detectar_captcha():
                self._aguardar_liberacao_captcha()
            if not self._extractor.pagina_tem_resultados(self._driver):
                return None
        return self._extractor.extrair_pagina(self._driver, segmento, pagina)

    def _scrape_segmento(self, segmento: dict) -> None:
        nome = f"{self.fonte}:{segmento['tipo']} R${segmento['preco_min']:,}-{segmento['preco_max']:,}"
        chave = f"{self.fonte}:{segmento['tipo']}"
        self._log(f"Iniciando segmento: {nome}")
        if not self._tentar(lambda: self._escolher_caminho(segmento)):
            self._log(f"ATENCAO: {nome} ignorado: o portal nao achou a pagina em nenhum caminho "
                      f"({', '.join(caminhos_candidatos(self.portal, segmento['tipo']))}). Confira a URL no navegador.")
            return

        for pagina in range(1, MAX_PAGINAS + 1):
            if self._repo.pagina_ja_coletada(chave, segmento["preco_min"], pagina):
                continue

            url = self._url(segmento, pagina)
            if not self._permitido(url):
                self._log(f"robots.txt nao permite {url}; segmento ignorado.")
                return
            dados = self._tentar(lambda: self._coletar_pagina(segmento, pagina, url))
            if dados is None:
                self._log(f"Fim do segmento na pagina {pagina}.")
                break
            self._repo.salvar_raw(dados)
            self._repo.marcar_pagina_coletada(chave, segmento["preco_min"], pagina)

            total_db = self._repo.total_raw()
            self._reportar_progresso(segmento, pagina, len(dados), total_db)

    @property
    def _perfil(self) -> str:
        return os.path.abspath(os.path.join(PERFIL_DIR, self.fonte))

    def _criar_navegador(self):
        if NAVEGADOR == "uc":
            options = uc.ChromeOptions()
            if CHROME_BIN_PATH:
                options.binary_location = CHROME_BIN_PATH
            options.add_argument("--start-maximized")
            return uc.Chrome(options=options, driver_executable_path=CHROMEDRIVER_PATH, version_main=CHROME_VERSION,
                             user_data_dir=self._perfil)
        options = webdriver.ChromeOptions()
        if CHROME_BIN_PATH:
            options.binary_location = CHROME_BIN_PATH
        options.add_argument("--start-maximized")
        options.add_argument(f"--user-data-dir={self._perfil}")
        if SEM_JANELA:
            options.add_argument("--headless=new")
        return webdriver.Chrome(options=options, service=Service(executable_path=CHROMEDRIVER_PATH) if CHROMEDRIVER_PATH else Service())

    def _iniciar_driver(self) -> None:
        os.makedirs(self._perfil, exist_ok=True)
        if encerrar_chrome_do_perfil(self._perfil):
            self._log("havia um Chrome antigo segurando o perfil; encerrado.")
        criar = self._criar_navegador
        if self._trava_driver is None:
            self._driver = criar()
        else:
            with self._trava_driver:  # um navegador por vez: o chromedriver e baixado/renomeado na criacao
                self._driver = criar()

    def _ler_robots(self) -> None:
        """Le o robots.txt pelo proprio navegador. Se nao for possivel ler, segue e avisa."""
        try:
            self._driver.get(self.portal["base"] + "/robots.txt")
            texto = self._driver.find_element(By.TAG_NAME, "body").text
            if "user-agent" not in texto.lower():
                raise ValueError("resposta nao parece um robots.txt")
            self._robots = robots_do_texto(self.portal["base"], texto)
            self._log("robots.txt lido.")
        except Exception as erro:
            self._robots = None
            self._log(f"AVISO: nao foi possivel ler o robots.txt ({erro}); conferir as regras do portal manualmente.")

    def _permitido(self, url: str) -> bool:
        return self._robots is None or self._robots.can_fetch("*", url)

    def _detectar_captcha(self) -> bool:
        try:
            url = (self._driver.current_url or "").lower()
            title = (self._driver.title or "").lower()

            if "captcha" in url or "captcha" in title:
                return True
            if "challenges.cloudflare.com" in url:
                return True

            seletores = [
                'iframe[src*="captcha"]',
                'iframe[title*="captcha"]',
                "#cf-challenge-running",
                '[id*="captcha"]',
                '[class*="captcha"]',
            ]
            # o DOM de paginas normais tem elementos de captcha escondidos (selo do reCAPTCHA): so conta o que aparece na tela
            return any(e.is_displayed() for s in seletores for e in self._driver.find_elements(By.CSS_SELECTOR, s))
        except Exception:
            return False

    def _aguardar_liberacao_captcha(self) -> None:
        self._log(f"CAPTCHA detectado. Aguardando liberacao por ate {CAPTCHA_MAX_WAIT}s...")
        inicio = time.time()
        while self._detectar_captcha() and not self._extractor.pagina_tem_resultados(self._driver):
            if (time.time() - inicio) >= CAPTCHA_MAX_WAIT:
                self._log("Timeout de CAPTCHA. Continuando fluxo.")
                return
            time.sleep(CAPTCHA_POLL)

    def _log(self, msg: str) -> None:
        print(f"[WORKER {self.worker_id} {self.fonte}] {msg}")

    def _reportar_progresso(self, segmento: dict, pagina: int, novos: int, total: int) -> None:
        self.fila_progresso.put(
            {
                "worker_id": self.worker_id,
                "segmento": f"{self.fonte}:{segmento['tipo']} R${segmento['preco_min']:,}+",
                "pagina": pagina,
                "novos": novos,
                "total_db": total,
            }
        )


class Bloqueado(Exception):
    """O portal recusou a requisicao (403/429/desafio). O coletor para: nao tenta contornar."""


def resposta_bloqueada(status: int, html: str) -> bool:
    texto = html[:6000].lower()
    return status in (403, 429, 503) or "attention required" in texto or "cf-error-details" in texto or "captcha" in texto


class ScraperHttp:
    """Mesmo fluxo do ScraperPortal (fatias de preco, paginas, retomada, robots.txt), mas por requisicao HTTP
    direta ao HTML da listagem. Se o portal bloquear, para e avisa; o modo navegador (`scrape`) continua disponivel."""

    def __init__(self, worker_id: int, fonte: str, segmentos: list[dict], fila_progresso, db_path: str):
        self.worker_id, self.fonte, self.portal = worker_id, fonte, PORTAIS[fonte]
        self.segmentos, self.fila_progresso = segmentos, fila_progresso
        self._repo = DataRepository(Database(db_path))
        self._sessao = requests.Session()
        self._sessao.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"})
        self._robots = None

    def executar(self) -> None:
        try:
            self._ler_robots()
            for segmento in self.segmentos:
                self._scrape_segmento(segmento)
        except Bloqueado as erro:
            self._log(f"BLOQUEADO: {erro}. Coleta interrompida (nada foi contornado). Use o modo navegador: python main.py scrape")
        except KeyboardInterrupt:
            self._log("Interrompido.")

    def executar_amostra(self) -> None:
        os.makedirs(AMOSTRAS_DIR, exist_ok=True)
        resumo = {}
        try:
            self._ler_robots()
            for segmento in [s for s in self.segmentos if s["preco_min"] == 0]:
                url = montar_url(self.portal, segmento, 1)
                if not self._permitido(url):
                    resumo[segmento["tipo"]] = {"url": url, "erro": "bloqueado pelo robots.txt"}
                    continue
                html = self._baixar(url)
                blocos = blocos_do_html(html)
                arquivo = os.path.join(AMOSTRAS_DIR, f"{self.fonte}_{segmento['tipo']}_p1_http.json")
                with open(arquivo, "w", encoding="utf-8") as f:
                    json.dump(blocos, f, ensure_ascii=False)
                resumo[segmento["tipo"]] = {"url": url, "arquivo": arquivo, "blocos_json_ld": len(blocos),
                                            "anuncios_no_json_ld": len(extrair_anuncios(blocos))}
                self._log(f"amostra {segmento['tipo']}: {resumo[segmento['tipo']]}")
                time.sleep(random.uniform(HTTP_DELAY_MIN, HTTP_DELAY_MAX))
        except Bloqueado as erro:
            resumo["erro"] = f"BLOQUEADO: {erro}"
            self._log(resumo["erro"])
        with open(os.path.join(AMOSTRAS_DIR, f"{self.fonte}_resumo_http.json"), "w", encoding="utf-8") as f:
            json.dump(resumo, f, ensure_ascii=False, indent=2)

    def _baixar(self, url: str) -> str:
        resposta = self._sessao.get(url, timeout=HTTP_TIMEOUT)
        if resposta_bloqueada(resposta.status_code, resposta.text):
            raise Bloqueado(f"HTTP {resposta.status_code} em {url}")
        resposta.raise_for_status()
        return resposta.text

    def _scrape_segmento(self, segmento: dict) -> None:
        chave = f"{self.fonte}:{segmento['tipo']}"
        self._log(f"Iniciando segmento: {chave} R${segmento['preco_min']:,}-{segmento['preco_max']:,}")
        for pagina in range(1, MAX_PAGINAS + 1):
            if self._repo.pagina_ja_coletada(chave, segmento["preco_min"], pagina):
                continue
            url = montar_url(self.portal, segmento, pagina)
            if not self._permitido(url):
                self._log(f"robots.txt nao permite {url}; segmento ignorado.")
                return
            anuncios = extrair_anuncios(blocos_do_html(self._baixar(url)))
            if not anuncios:
                self._log(f"Fim do segmento na pagina {pagina}.")
                return
            for a in anuncios:
                a.update({"fonte": self.fonte, "segmento": chave, "preco_min_filtro": segmento["preco_min"], "pagina": pagina})
            self._repo.salvar_raw(anuncios)
            self._repo.marcar_pagina_coletada(chave, segmento["preco_min"], pagina)
            self.fila_progresso.put({"worker_id": self.worker_id, "segmento": f"{chave} R${segmento['preco_min']:,}+",
                                     "pagina": pagina, "novos": len(anuncios), "total_db": self._repo.total_raw()})
            time.sleep(random.uniform(HTTP_DELAY_MIN, HTTP_DELAY_MAX))

    def _ler_robots(self) -> None:
        try:
            self._robots = robots_do_texto(self.portal["base"], self._baixar(self.portal["base"] + "/robots.txt"))
            self._log("robots.txt lido.")
        except Bloqueado:
            raise
        except Exception as erro:
            self._robots = None
            self._log(f"AVISO: nao foi possivel ler o robots.txt ({erro}); conferir as regras do portal manualmente.")

    def _permitido(self, url: str) -> bool:
        return self._robots is None or self._robots.can_fetch("*", url)

    def _log(self, msg: str) -> None:
        print(f"[WORKER {self.worker_id} {self.fonte} HTTP] {msg}")


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class ScraperOrchestrator:
    def __init__(self, db_path: str, amostra: bool = False, http: bool = False):
        self._db_path = db_path
        self._amostra = amostra
        self._http = http

    def executar(self) -> None:
        Database(self._db_path).setup()
        fila = multiprocessing.Queue()
        trava_driver = multiprocessing.Lock()

        processos = [
            multiprocessing.Process(
                target=_run_worker,
                args=(i, fonte, SEGMENTOS, fila, self._db_path, self._amostra, self._http, trava_driver),
                daemon=True,
            )
            for i, fonte in enumerate(PORTAIS, start=1)
        ]

        print("=" * 65)
        print("  MODO AMOSTRA: 1 PAGINA POR TIPO, SEM GRAVAR NO BANCO" if self._amostra
              else "  SCRAPER PARALELO - META: TODOS OS IMOVEIS DE JACAREI")
        print("=" * 65)

        for p in processos:
            p.start()

        status = {i: {} for i in range(1, len(processos) + 1)}
        try:
            while any(p.is_alive() for p in processos):
                try:
                    msg = fila.get(timeout=1)
                    status[msg["worker_id"]] = msg
                    self._exibir_painel(status)
                except Exception:
                    pass
        except KeyboardInterrupt:
            print("\nInterrompido. Aguardando workers encerrarem...")
        finally:
            for p in processos:
                p.join(timeout=10)

        print("\nColeta finalizada!")
        if self._amostra:
            print(f"Amostras e contagens em {AMOSTRAS_DIR}")

    @staticmethod
    def _exibir_painel(status: dict) -> None:
        os.system("cls" if os.name == "nt" else "clear")
        print("=" * 65)
        print("  SCRAPER PARALELO - PROGRESSO EM TEMPO REAL")
        print("=" * 65)
        for wid, s in status.items():
            if not s:
                print(f"  [WORKER {wid}] Iniciando...")
                continue
            print(
                f"  [WORKER {wid}] {s.get('segmento', ''):<35} "
                f"| Pag {s.get('pagina', 0):>4} "
                f"| +{s.get('novos', 0):>3} imoveis"
            )
        total = max((s.get("total_db", 0) for s in status.values()), default=0)
        print("-" * 65)
        print(f"  TOTAL NO BANCO: {total:,} registros brutos")
        print("=" * 65)


def _run_worker(worker_id: int, fonte: str, segmentos: list, fila, db_path: str, amostra: bool = False, http: bool = False,
                trava_driver=None) -> None:
    scraper = ScraperHttp(worker_id, fonte, segmentos, fila, db_path) if http else \
        ScraperPortal(worker_id, fonte, segmentos, fila, db_path, trava_driver)
    scraper.executar_amostra() if amostra else scraper.executar()
