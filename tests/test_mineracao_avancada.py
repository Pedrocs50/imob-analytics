import unittest

import numpy as np
import pandas as pd

from src.pricing.mineracao_avancada import _com_bairro, regras, tempo_no_ar


class TesteRegras(unittest.TestCase):
    def test_lift_da_combinacao_que_realmente_acompanha_o_alvo(self):
        rng = np.random.default_rng(0)
        n = 4000
        itens = pd.DataFrame({"piscina": rng.random(n) < 0.3, "ruido": rng.random(n) < 0.5})
        alvo = pd.Series(np.where(itens["piscina"], rng.random(n) < 0.7, rng.random(n) < 0.2))
        tabela = regras(itens, alvo)
        piscina = tabela[tabela["se o anuncio tem"] == "piscina"].iloc[0]
        ruido = tabela[tabela["se o anuncio tem"] == "ruido"].iloc[0]
        self.assertGreater(piscina["lift"], 1.5)
        self.assertAlmostEqual(ruido["lift"], 1.0, delta=0.1)
        self.assertEqual(tabela.iloc[0]["se o anuncio tem"], "piscina")  # ordenado por lift

    def test_regra_maior_so_entra_se_melhora_a_menor(self):
        rng = np.random.default_rng(1)
        n = 4000
        piscina = rng.random(n) < 0.4
        itens = pd.DataFrame({"piscina": piscina, "ruido": rng.random(n) < 0.5})
        alvo = pd.Series(np.where(piscina, rng.random(n) < 0.7, rng.random(n) < 0.2))
        nomes = set(regras(itens, alvo)["se o anuncio tem"])
        self.assertNotIn("piscina + ruido", nomes)  # o ruido nao acrescenta nada a "piscina"


class TesteBairroETempo(unittest.TestCase):
    def test_bairros_com_poucos_anuncios_ficam_de_fora_e_rel_bairro_usa_a_mediana(self):
        df = pd.DataFrame({"neighborhood": ["A"] * 20 + ["B"] * 3, "preco_m2": [100.0] * 10 + [200.0] * 10 + [50.0] * 3})
        base = _com_bairro(df)
        self.assertEqual(set(base["neighborhood"]), {"A"})
        self.assertAlmostEqual(base["rel_bairro"].min(), 100 / 150)

    def test_tempo_no_ar_em_faixas(self):
        df = pd.DataFrame({"scraped_at": ["2026-03-20 10:00:00"] * 4,
                           "created_at": ["2026-03-10T10:00:00Z", "2025-12-01T10:00:00Z", "2025-01-01T10:00:00Z", "2023-01-01T10:00:00Z"],
                           "rel_bairro": [1.0, 1.0, 0.9, 0.8], "preco_m2": [1.0, 1.0, 1.0, 1.0]})
        tabela, _ = tempo_no_ar(df)
        self.assertEqual(list(tabela["faixa"]), ["ate 30 dias", "91-180 dias", "1 a 2 anos", "mais de 2 anos"])
