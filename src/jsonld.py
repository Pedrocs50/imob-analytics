"""Leitura dos dados estruturados (JSON-LD, schema.org) que as paginas de anuncio ja trazem embutidos.

Mais robusto que ler cards pelo CSS: o formato e padronizado, traz id e URL do anuncio e nao depende
de rolar a pagina. Funcao pura (recebe os textos dos blocos), testavel sem navegador.
"""
import json
import re

_ID_NA_URL = re.compile(r"id-(\d+)")


def _percorrer(no):
    """Todos os objetos do JSON, em qualquer profundidade (cobre @graph, ItemList, item, etc.)."""
    if isinstance(no, dict):
        yield no
        for valor in no.values():
            yield from _percorrer(valor)
    elif isinstance(no, list):
        for valor in no:
            yield from _percorrer(valor)


def _numero(valor) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _primeiro(valor) -> dict:
    if isinstance(valor, list):
        valor = valor[0] if valor else {}
    return valor if isinstance(valor, dict) else {}


def _id_externo(no: dict, url: str) -> str | None:
    candidato = str(no.get("@id") or no.get("id") or "")
    if candidato.isdigit():
        return candidato
    achado = _ID_NA_URL.search(url)
    return achado.group(1) if achado else None


def _anuncio(no: dict) -> dict | None:
    url = str(no.get("url") or "")
    oferta = _primeiro(no.get("offers"))
    preco = _numero(oferta.get("price"))
    if not url or preco is None:
        return None
    endereco = _primeiro(no.get("address"))
    area = _numero(_primeiro(no.get("floorSize")).get("value"))
    quartos = _numero(no.get("numberOfBedrooms"))
    banheiros = _numero(no.get("numberOfBathroomsTotal"))
    vagas = _numero(no.get("numberOfParkingSpaces"))
    comodidades = [str(c.get("value") or c.get("name")) for c in no.get("amenityFeature") or [] if isinstance(c, dict)]
    rua, cidade = endereco.get("streetAddress"), endereco.get("addressLocality")
    titulo = str(no.get("name") or "")

    def texto(valor, formato):
        return formato.format(int(round(valor))) if valor is not None else "N/A"

    return {
        "external_id": _id_externo(no, url),
        "url": url,
        # campos de texto no mesmo formato do coletor antigo: o DataCleaner continua funcionando
        "endereco": ", ".join(p for p in (titulo, rua, cidade) if p) or "N/A",
        "preco": "R$ " + f"{int(round(preco)):,}".replace(",", "."),
        "area": texto(area, "{} m²"),
        "quartos": texto(quartos, "{}"),
        "banheiros": texto(banheiros, "{}"),
        "vagas": texto(vagas, "{}"),
        "comodidades": json.dumps(comodidades, ensure_ascii=False),
    }


def extrair_anuncios(blocos: list[str]) -> list[dict]:
    """Anuncios encontrados nos blocos `application/ld+json` de uma pagina (sem repeticao por id)."""
    vistos: dict[str, dict] = {}
    for texto in blocos:
        try:
            dados = json.loads(texto)
        except (TypeError, ValueError):
            continue
        for no in _percorrer(dados):
            if "offers" not in no:
                continue
            anuncio = _anuncio(no)
            if anuncio:
                vistos.setdefault(anuncio["external_id"] or anuncio["url"], anuncio)
    return list(vistos.values())
