import json
import unittest

import pandas as pd

from src.cleaner import DataCleaner
from src.jsonld import extrair_anuncios
from src.scraper import PORTAIS, SEGMENTOS, ExtractorPortal, montar_url, robots_do_texto
from tests.test_jsonld import ANUNCIO


class TesteUrls(unittest.TestCase):
    def test_zap_mantem_o_formato_original(self):
        url = montar_url(PORTAIS["zap"], {"tipo": "casas", "preco_min": 0, "preco_max": 300_000}, 3)
        self.assertEqual(url, "https://www.zapimoveis.com.br/venda/casas/sp+jacarei/?page=3&precoMinimo=0&precoMaximo=300000")

    def test_todos_os_tipos_tem_caminho_em_cada_portal(self):
        for portal in PORTAIS.values():
            for seg in SEGMENTOS:
                self.assertIn(seg["tipo"], portal["caminhos"])
                self.assertTrue(montar_url(portal, seg, 1).startswith(portal["base"]))


class TesteRobots(unittest.TestCase):
    def test_respeita_disallow(self):
        rp = robots_do_texto("https://x.com", "User-agent: *\nDisallow: /venda/privado/\n")
        self.assertFalse(rp.can_fetch("*", "https://x.com/venda/privado/a"))
        self.assertTrue(rp.can_fetch("*", "https://x.com/venda/casas/"))


class TesteVagas(unittest.TestCase):
    def test_vagas_vem_do_keywords_do_vivareal(self):
        no = {**ANUNCIO, "keywords": "Casa para comprar com 177 m², 3 quartos, 3 banheiros, 2 vagas em Jardim"}
        [a] = extrair_anuncios([json.dumps(no)])
        self.assertEqual(a["vagas"], "2")
        self.assertEqual(a["rua"], "Rua Isabel Garcia Marques")


class FakeDriver:
    def __init__(self, blocos):
        self.blocos = blocos

    def execute_script(self, js):
        return self.blocos

    def find_elements(self, *a):
        return []


class TesteExtrator(unittest.TestCase):
    def test_marca_fonte_e_segmento(self):
        ex = ExtractorPortal("vivareal")
        ex._aguardar_carregamento = lambda d: None
        [a] = ex.extrair_pagina(FakeDriver([json.dumps(ANUNCIO)]), {"tipo": "casas", "preco_min": 0}, 2)
        self.assertEqual((a["fonte"], a["segmento"], a["pagina"]), ("vivareal", "vivareal:casas", 2))

    def test_contagens(self):
        c = ExtractorPortal("zap").contagens(FakeDriver([json.dumps(ANUNCIO)]))
        self.assertEqual((c["blocos_json_ld"], c["anuncios_no_json_ld"], c["cards_na_tela"]), (1, 1, 0))


def _linha(fonte, ext, rua, preco, area=60.0, quartos=2, banheiros=1):
    return {"fonte": fonte, "external_id": ext, "rua": rua, "endereco": f"{ext} {rua}", "preco_venda": preco,
            "area_m2": area, "qtd_quartos": quartos, "qtd_banheiros": banheiros}


class TesteDedupeEntreFontes(unittest.TestCase):
    def dedupe(self, linhas):
        c = DataCleaner.__new__(DataCleaner)
        return c._remover_duplicatas_entre_fontes(pd.DataFrame(linhas))

    def test_mesmo_imovel_em_dois_portais_vira_um(self):
        df = self.dedupe([_linha("zap", "1", "Rua das Flores", 500_000), _linha("vivareal", "9", "R. das Flores", 505_000)])
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["fonte"], "vivareal")  # ordem alfabetica das fontes

    def test_unidades_iguais_no_mesmo_predio_com_precos_diferentes_ficam(self):
        df = self.dedupe([_linha("zap", "1", "Rua das Flores", 500_000), _linha("vivareal", "9", "Rua das Flores", 600_000)])
        self.assertEqual(len(df), 2)

    def test_mesma_fonte_nunca_e_juntada_aqui(self):
        df = self.dedupe([_linha("zap", "1", "Rua das Flores", 500_000), _linha("zap", "2", "Rua das Flores", 500_000)])
        self.assertEqual(len(df), 2)

    def test_sem_rua_nao_junta(self):
        df = self.dedupe([_linha("zap", "1", None, 500_000), _linha("vivareal", "9", None, 500_000)])
        self.assertEqual(len(df), 2)


if __name__ == "__main__":
    unittest.main()


class TesteModoHttp(unittest.TestCase):
    HTML = "<html><head><script type='application/ld+json'>%s</script></head><body>x</body></html>" % json.dumps(ANUNCIO)

    def test_extrai_json_ld_do_html(self):
        from src.jsonld import blocos_do_html
        [a] = extrair_anuncios(blocos_do_html(self.HTML))
        self.assertEqual(a["external_id"], "2919071120")

    def test_detecta_bloqueio(self):
        from src.scraper import resposta_bloqueada
        self.assertTrue(resposta_bloqueada(403, "x"))
        self.assertTrue(resposta_bloqueada(200, "<title>Attention Required! | Cloudflare</title>"))
        self.assertFalse(resposta_bloqueada(200, self.HTML))

    def test_http_para_quando_bloqueado(self):
        import queue, tempfile, os
        from unittest import mock
        from src.scraper import Bloqueado, ScraperHttp
        from src.database import Database
        db = os.path.join(tempfile.mkdtemp(), "t.db")
        Database(db).setup()
        s = ScraperHttp(1, "zap", SEGMENTOS[:1], queue.Queue(), db)
        resposta = mock.Mock(status_code=403, text="blocked")
        with mock.patch.object(s._sessao, "get", return_value=resposta):
            with self.assertRaises(Bloqueado):
                s._baixar("https://exemplo/x")

    def test_http_grava_e_pagina_ate_acabar(self):
        import queue, tempfile, os
        from unittest import mock
        from src.scraper import ScraperHttp
        from src.database import Database
        db = os.path.join(tempfile.mkdtemp(), "t.db")
        Database(db).setup()
        s = ScraperHttp(1, "zap", SEGMENTOS[:1], queue.Queue(), db)
        s._robots = None
        paginas = iter([self.HTML, "<html></html>"])
        with mock.patch.object(s, "_baixar", side_effect=lambda u: next(paginas)), mock.patch("src.scraper.time.sleep"):
            s._scrape_segmento(SEGMENTOS[0])
        self.assertEqual(s._repo.total_raw(), 1)
        self.assertTrue(s._repo.pagina_ja_coletada("zap:casas", 0, 1))


class TesteCaptcha(unittest.TestCase):
    def _scraper(self, elementos, resultados):
        import queue, tempfile, os
        from unittest import mock
        from src.scraper import ScraperPortal
        from src.database import Database
        db = os.path.join(tempfile.mkdtemp(), "t.db")
        Database(db).setup()
        s = ScraperPortal(1, "vivareal", SEGMENTOS[:1], queue.Queue(), db)
        drv = mock.Mock(current_url="https://x/casas", title="Casas")
        drv.find_elements.return_value = elementos
        s._driver = drv
        s._extractor.pagina_tem_resultados = lambda d: resultados
        return s

    def test_elemento_de_captcha_escondido_nao_e_captcha(self):
        from unittest import mock
        escondido = mock.Mock(is_displayed=lambda: False)
        self.assertFalse(self._scraper([escondido], True)._detectar_captcha())

    def test_elemento_de_captcha_visivel_e_captcha(self):
        from unittest import mock
        visivel = mock.Mock(is_displayed=lambda: True)
        self.assertTrue(self._scraper([visivel], False)._detectar_captcha())

    def test_nao_espera_quando_a_pagina_ja_tem_resultados(self):
        from unittest import mock
        visivel = mock.Mock(is_displayed=lambda: True)
        s = self._scraper([visivel], True)
        with mock.patch("src.scraper.time.sleep") as dorme:
            s._aguardar_liberacao_captcha()
        dorme.assert_not_called()
