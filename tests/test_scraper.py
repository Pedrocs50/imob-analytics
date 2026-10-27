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
