import time
import os
import random
import multiprocessing

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.database import Database
from src.repository import DataRepository


# =============================================================================
# CONFIGURACOES CENTRALIZADAS
# =============================================================================

CHROME_BIN_PATH = os.path.join(os.getcwd(), "scripts", "chrome-win64", "chrome.exe")
CHROMEDRIVER_PATH = os.path.join(os.getcwd(), "scripts", "chromedriver.exe")
CHROME_VERSION = 145  # atualize se instalar uma versao nova do Chrome
DELAY_MIN = 8  # segundos minimos entre paginas
DELAY_MAX = 15  # segundos maximos entre paginas
MAX_PAGINAS = 400  # limite seguro por segmento antes de bloqueio do Zap

# Evita travar infinito no CAPTCHA
CAPTCHA_MAX_WAIT = 90  # segundos
CAPTCHA_POLL = 3  # segundos


# Segmentos = fatias do catalogo para driblar o limite de ~400 paginas por URL
SEGMENTOS_WORKER_1 = [
    {"tipo": "casas", "preco_min": 0, "preco_max": 300_000},
    {"tipo": "casas", "preco_min": 300_000, "preco_max": 600_000},
    {"tipo": "casas", "preco_min": 600_000, "preco_max": 1_000_000},
    {"tipo": "casas", "preco_min": 1_000_000, "preco_max": 2_000_000},
    {"tipo": "casas", "preco_min": 2_000_000, "preco_max": 99_999_999},
    {"tipo": "apartamentos", "preco_min": 0, "preco_max": 300_000},
    {"tipo": "apartamentos", "preco_min": 300_000, "preco_max": 600_000},
]

SEGMENTOS_WORKER_2 = [
    {"tipo": "apartamentos", "preco_min": 600_000, "preco_max": 1_000_000},
    {"tipo": "apartamentos", "preco_min": 1_000_000, "preco_max": 99_999_999},
    {"tipo": "terrenos", "preco_min": 0, "preco_max": 200_000},
    {"tipo": "terrenos", "preco_min": 200_000, "preco_max": 99_999_999},
    {"tipo": "imoveis", "preco_min": 0, "preco_max": 500_000},
    {"tipo": "imoveis", "preco_min": 500_000, "preco_max": 99_999_999},
]


# =============================================================================
# EXTRACTOR
# =============================================================================

class ExtractorZap:
    _SELETORES = {
        "preco": '[data-cy="rp-cardProperty-price-txt"]',
        "endereco": '[data-cy="rp-cardProperty-location-txt"]',
        "area": '[data-cy="rp-cardProperty-propertyArea-txt"]',
        "quartos": '[data-cy="rp-cardProperty-bedroomQuantity-txt"]',
        "banheiros": '[data-cy="rp-cardProperty-bathroomQuantity-txt"]',
        "vagas": '[data-cy="rp-cardProperty-parkingSpacesQuantity-txt"]',
    }

    _CARDS_CSS = 'div[class*="content-stretch"][class*="min-w-0"]'

    def extrair_pagina(self, driver, segmento: dict, pagina: int) -> list[dict]:
        self._aguardar_carregamento(driver)
        self._rolar_pagina(driver)

        cards = driver.find_elements(By.CSS_SELECTOR, self._CARDS_CSS)
        resultados = []

        for card in cards:
            dado = self._extrair_card(card, segmento, pagina)
            if dado:
                resultados.append(dado)

        return resultados

    def pagina_tem_resultados(self, driver) -> bool:
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, self._CARDS_CSS)
            return len(cards) > 0
        except Exception:
            return False

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

    def _extrair_card(self, card, segmento: dict, pagina: int) -> dict | None:
        try:
            preco_el = card.find_element(By.CSS_SELECTOR, self._SELETORES["preco"])
            preco = preco_el.text.replace("\n", " ").strip()
        except Exception:
            return None

        def get(campo):
            try:
                return card.find_element(By.CSS_SELECTOR, self._SELETORES[campo]).text
            except Exception:
                return "N/A"

        return {
            "segmento": segmento["tipo"],
            "preco_min_filtro": segmento["preco_min"],
            "pagina": pagina,
            "endereco": get("endereco"),
            "preco": preco,
            "area": get("area"),
            "quartos": get("quartos"),
            "banheiros": get("banheiros"),
            "vagas": get("vagas"),
        }


# =============================================================================
# SCRAPER
# =============================================================================

class ScraperZap:
    def __init__(self, worker_id: int, segmentos: list[dict], fila_progresso, db_path: str):
        self.worker_id = worker_id
        self.segmentos = segmentos
        self.fila_progresso = fila_progresso
        self._db = Database(db_path)
        self._repo = DataRepository(self._db)
        self._extractor = ExtractorZap()
        self._driver = None

    def executar(self) -> None:
        self._iniciar_driver()
        try:
            for segmento in self.segmentos:
                self._scrape_segmento(segmento)
        except KeyboardInterrupt:
            self._log("Interrompido.")
        finally:
            if self._driver is not None:
                self._driver.quit()
            self._log("Navegador fechado.")

    def _scrape_segmento(self, segmento: dict) -> None:
        nome = f"{segmento['tipo']} R${segmento['preco_min']:,}-{segmento['preco_max']:,}"
        self._log(f"Iniciando segmento: {nome}")

        for pagina in range(1, MAX_PAGINAS + 1):
            if self._repo.pagina_ja_coletada(segmento["tipo"], segmento["preco_min"], pagina):
                continue

            url = self._montar_url(segmento, pagina)
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
            self._repo.marcar_pagina_coletada(segmento["tipo"], segmento["preco_min"], pagina)

            total_db = self._repo.total_raw()
            self._reportar_progresso(segmento, pagina, len(dados), total_db)

    def _iniciar_driver(self) -> None:
        options = uc.ChromeOptions()
        options.binary_location = CHROME_BIN_PATH
        options.add_argument("--start-maximized")
        self._driver = uc.Chrome(
            options=options,
            driver_executable_path=CHROMEDRIVER_PATH,
            version_main=CHROME_VERSION,
        )

    def _montar_url(self, segmento: dict, pagina: int) -> str:
        return (
            f"https://www.zapimoveis.com.br/venda/{segmento['tipo']}/sp+jacarei/"
            f"?page={pagina}&precoMinimo={segmento['preco_min']}&precoMaximo={segmento['preco_max']}"
        )

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
        print(f"[WORKER {self.worker_id}] {msg}")

    def _reportar_progresso(self, segmento: dict, pagina: int, novos: int, total: int) -> None:
        self.fila_progresso.put(
            {
                "worker_id": self.worker_id,
                "segmento": f"{segmento['tipo']} R${segmento['preco_min']:,}+",
                "pagina": pagina,
                "novos": novos,
                "total_db": total,
            }
        )


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class ScraperOrchestrator:
    def __init__(self, db_path: str):
        self._db_path = db_path

    def executar(self) -> None:
        Database(self._db_path).setup()
        fila = multiprocessing.Queue()

        processos = [
            multiprocessing.Process(
                target=_run_worker,
                args=(1, SEGMENTOS_WORKER_1, fila, self._db_path),
                daemon=True,
            ),
            multiprocessing.Process(
                target=_run_worker,
                args=(2, SEGMENTOS_WORKER_2, fila, self._db_path),
                daemon=True,
            ),
        ]

        print("=" * 65)
        print("  SCRAPER PARALELO - META: TODOS OS IMOVEIS DE JACAREI")
        print("=" * 65)

        for p in processos:
            p.start()

        status = {1: {}, 2: {}}
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


def _run_worker(worker_id: int, segmentos: list, fila, db_path: str) -> None:
    scraper = ScraperZap(worker_id, segmentos, fila, db_path)
    scraper.executar()
