import json
import time
import os
import random
import multiprocessing
import urllib.robotparser

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.database import Database
from src.jsonld import extrair_anuncios
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
        "caminhos": {"casas": "casas", "apartamentos": "apartamentos", "terrenos": "terrenos", "imoveis": "imoveis"},
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

    def __init__(self, fonte: str):
        self._fonte = fonte

    def blocos_json_ld(self, driver) -> list[str]:
        try:
            return driver.execute_script(self._JSON_LD_JS) or []
        except Exception:
            return []

    def extrair_pagina(self, driver, segmento: dict, pagina: int) -> list[dict]:
        self._aguardar_carregamento(driver)
        anuncios = extrair_anuncios(self.blocos_json_ld(driver))
        if not anuncios:
            self._rolar_pagina(driver)
            anuncios = [d for d in (self._extrair_card(c) for c in driver.find_elements(By.CSS_SELECTOR, self._CARDS_CSS)) if d]
        for a in anuncios:
            a.update({"fonte": self._fonte, "segmento": f"{self._fonte}:{segmento['tipo']}",
                      "preco_min_filtro": segmento["preco_min"], "pagina": pagina})
        return anuncios

    def pagina_tem_resultados(self, driver) -> bool:
        try:
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

    def _aguardar_carregamento(self, driver) -> None:
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self._SELETORES["preco"]))
            )
        except Exception:
            pass

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

def montar_url(portal: dict, segmento: dict, pagina: int) -> str:
    return portal["url"].format(
        base=portal["base"], caminho=portal["caminhos"][segmento["tipo"]], pagina_param=portal["pagina_param"],
        pagina=pagina, preco_min=segmento["preco_min"], preco_max=segmento["preco_max"],
    )


def robots_do_texto(base: str, texto: str) -> urllib.robotparser.RobotFileParser:
    rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
    rp.parse(texto.splitlines())
    return rp


class ScraperPortal:
    def __init__(self, worker_id: int, fonte: str, segmentos: list[dict], fila_progresso, db_path: str):
        self.worker_id = worker_id
        self.fonte = fonte
        self.portal = PORTAIS[fonte]
        self.segmentos = segmentos
        self.fila_progresso = fila_progresso
        self._db = Database(db_path)
        self._repo = DataRepository(self._db)
        self._extractor = ExtractorPortal(fonte)
        self._driver = None
        self._robots = None

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
                self._driver.get(url)
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                if self._detectar_captcha():
                    self._aguardar_liberacao_captcha()
                self._extractor._aguardar_carregamento(self._driver)
                blocos = self._extractor.blocos_json_ld(self._driver)
                arquivo = os.path.join(AMOSTRAS_DIR, f"{self.fonte}_{segmento['tipo']}_p1.json")
                with open(arquivo, "w", encoding="utf-8") as f:
                    json.dump(blocos, f, ensure_ascii=False)
                resumo[segmento["tipo"]] = {"url": self._driver.current_url, "arquivo": arquivo,
                                            **self._extractor.contagens(self._driver)}
                self._log(f"amostra {segmento['tipo']}: {resumo[segmento['tipo']]}")
        finally:
            if self._driver is not None:
                self._driver.quit()
        with open(os.path.join(AMOSTRAS_DIR, f"{self.fonte}_resumo.json"), "w", encoding="utf-8") as f:
            json.dump(resumo, f, ensure_ascii=False, indent=2)

    def _scrape_segmento(self, segmento: dict) -> None:
        nome = f"{self.fonte}:{segmento['tipo']} R${segmento['preco_min']:,}-{segmento['preco_max']:,}"
        chave = f"{self.fonte}:{segmento['tipo']}"
        self._log(f"Iniciando segmento: {nome}")

        for pagina in range(1, MAX_PAGINAS + 1):
            if self._repo.pagina_ja_coletada(chave, segmento["preco_min"], pagina):
                continue

            url = montar_url(self.portal, segmento, pagina)
            if not self._permitido(url):
                self._log(f"robots.txt nao permite {url}; segmento ignorado.")
                return
            self._driver.get(url)

            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            time.sleep(delay)

            # Recheca cards para evitar falso "fim de segmento"
            if not self._extractor.pagina_tem_resultados(self._driver):
                if self._detectar_captcha():
                    self._aguardar_liberacao_captcha()

                if not self._extractor.pagina_tem_resultados(self._driver):
                    self._log(f"Fim do segmento na pagina {pagina}.")
                    break

            dados = self._extractor.extrair_pagina(self._driver, segmento, pagina)
            self._repo.salvar_raw(dados)
            self._repo.marcar_pagina_coletada(chave, segmento["preco_min"], pagina)

            total_db = self._repo.total_raw()
            self._reportar_progresso(segmento, pagina, len(dados), total_db)

    def _iniciar_driver(self) -> None:
        options = uc.ChromeOptions()
        if CHROME_BIN_PATH:
            options.binary_location = CHROME_BIN_PATH
        options.add_argument("--start-maximized")
        self._driver = uc.Chrome(
            options=options,
            driver_executable_path=CHROMEDRIVER_PATH,
            version_main=CHROME_VERSION,
            user_data_dir=os.path.abspath(os.path.join(PERFIL_DIR, self.fonte)),
        )

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
            return any(self._driver.find_elements(By.CSS_SELECTOR, s) for s in seletores)
        except Exception:
            return False

    def _aguardar_liberacao_captcha(self) -> None:
        self._log(f"CAPTCHA detectado. Aguardando liberacao por ate {CAPTCHA_MAX_WAIT}s...")
        inicio = time.time()
        while self._detectar_captcha():
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


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class ScraperOrchestrator:
    def __init__(self, db_path: str, amostra: bool = False):
        self._db_path = db_path
        self._amostra = amostra

    def executar(self) -> None:
        Database(self._db_path).setup()
        fila = multiprocessing.Queue()

        processos = [
            multiprocessing.Process(
                target=_run_worker,
                args=(i, fonte, SEGMENTOS, fila, self._db_path, self._amostra),
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


def _run_worker(worker_id: int, fonte: str, segmentos: list, fila, db_path: str, amostra: bool = False) -> None:
    scraper = ScraperPortal(worker_id, fonte, segmentos, fila, db_path)
    scraper.executar_amostra() if amostra else scraper.executar()
