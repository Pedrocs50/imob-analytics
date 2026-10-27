import json
import unittest

from src.jsonld import extrair_anuncios

# modelo montado a partir dos campos vistos na resposta de uma pagina de listagem do ZAP
ANUNCIO = {
    "@id": "2919071120",
    "name": "Casa para alugar com 60 m², 2 quartos, 1 banheiro em Parque Santo Antônio, São Paulo",
    "url": "https://www.zapimoveis.com.br/imovel/aluguel-casa-2-quartos-id-2919071120/",
    "additionalType": "https://schema.org/House",
    "address": {"@type": "PostalAddress", "streetAddress": "Rua Isabel Garcia Marques",
                "addressLocality": "São Paulo", "addressRegion": "SP", "addressCountry": "BR"},
    "numberOfRooms": 2, "numberOfBedrooms": 2, "numberOfBathroomsTotal": 1,
    "floorSize": {"@type": "QuantitativeValue", "value": 60, "unitCode": "M2"},
    "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": "Amenity", "value": "Kitchen"}],
    "offers": {"@type": "Offer", "url": "https://www.zapimoveis.com.br/imovel/x", "price": 1480, "priceCurrency": "BRL"},
}


class TesteJsonLd(unittest.TestCase):
    def test_le_campos_principais(self):
        [a] = extrair_anuncios([json.dumps(ANUNCIO)])
        self.assertEqual(a["external_id"], "2919071120")
        self.assertEqual(a["preco"], "R$ 1.480")
        self.assertEqual(a["area"], "60 m²")
        self.assertEqual(a["quartos"], "2")
        self.assertEqual(a["banheiros"], "1")
        self.assertEqual(a["vagas"], "N/A")
        self.assertIn("Rua Isabel Garcia Marques", a["endereco"])
        self.assertEqual(json.loads(a["comodidades"]), ["Kitchen"])

    def test_acha_anuncios_aninhados_e_remove_repetidos(self):
        pagina = {"@graph": [{"@type": "ItemList", "itemListElement": [{"item": ANUNCIO}, {"item": ANUNCIO}]}]}
        self.assertEqual(len(extrair_anuncios([json.dumps(pagina)])), 1)

    def test_id_vem_da_url_quando_nao_ha_id_numerico(self):
        sem_id = {**ANUNCIO, "@id": "https://exemplo/x"}
        [a] = extrair_anuncios([json.dumps(sem_id)])
        self.assertEqual(a["external_id"], "2919071120")

    def test_ignora_json_invalido_e_blocos_sem_anuncio(self):
        self.assertEqual(extrair_anuncios(["{quebrado", json.dumps({"@type": "WebSite"})]), [])

    def test_endereco_serve_ao_cleaner(self):
        from src.cleaner import DataCleaner
        [a] = extrair_anuncios([json.dumps(ANUNCIO)])
        self.assertEqual(DataCleaner._definir_tipo(a["endereco"]), "Casa")
        self.assertEqual(DataCleaner._limpar_preco(a["preco"]), 1480.0)
        self.assertEqual(DataCleaner._extrair_numero(a["area"]), 60.0)


if __name__ == "__main__":
    unittest.main()
