"""Leitura dos dados estruturados (JSON-LD, schema.org) que as paginas de anuncio ja trazem embutidos.

Mais robusto que ler cards pelo CSS: o formato e padronizado, traz id e URL do anuncio e nao depende
de rolar a pagina. Funcao pura (recebe os textos dos blocos), testavel sem navegador.
"""
import json
import re
from html.parser import HTMLParser

_ID_NA_URL = re.compile(r"id-(\d+)")
_VAGAS = re.compile(r"(\d+)\s+vagas?", re.IGNORECASE)
_BAIRRO = re.compile(r".*\bem\s+([^,]+),\s*Jacare[íi]", re.IGNORECASE)  # "... 2 vagas em  Parque Imperial, Jacareí"
_CONDOMINIO = re.compile(r"Cond\.?\s*(R\$\s*([\d.]+)|isento|n[ãa]o informado)", re.IGNORECASE)
_IPTU = re.compile(r"IPTU\s*(R\$\s*([\d.]+)|isento|n[ãa]o informado)", re.IGNORECASE)
_FOTOS = re.compile(r"\+?\s*(\d+)\s*fotos", re.IGNORECASE)
_DESTAQUE = re.compile(r"\b(super\s+destaque|destaque)\b", re.IGNORECASE)
# nada que identifique o anunciante nem imagens: fora do JSON bruto guardado
_CAMPOS_FORA = {"image", "photo", "seller", "provider", "author", "agent", "broker", "telephone", "email", "contactPoint"}


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


def _valor_do_card(achado) -> float | None:
    if not achado:
        return None
    if achado.group(2):
        return float(achado.group(2).replace(".", ""))
    return 0.0 if achado.group(1).lower() == "isento" else None


def valores_do_card(texto: str) -> dict:
    """Condominio e IPTU do texto do card ("Cond. R$ 1 • IPTU R$ 500"). Isento = 0; "nao informado" = ausente."""
    fotos, destaque = _FOTOS.search(texto), _DESTAQUE.search(texto)
    return {"condominio": _valor_do_card(_CONDOMINIO.search(texto)), "iptu": _valor_do_card(_IPTU.search(texto)),
            "fotos": int(fotos.group(1)) if fotos else None,
            "destaque": " ".join(destaque.group(1).lower().split()) if destaque else None}


def _sem_dados_do_anunciante(no):
    if isinstance(no, dict):
        return {k: _sem_dados_do_anunciante(v) for k, v in no.items() if k not in _CAMPOS_FORA}
    if isinstance(no, list):
        return [_sem_dados_do_anunciante(v) for v in no]
    return no


def _taxa_condominio(oferta: dict) -> float | None:
    """O JSON-LD traz o condominio como PropertyValue "Condominium Fee" (BRL/month) em offers.additionalProperty."""
    props = oferta.get("additionalProperty") or []
    for prop in props if isinstance(props, list) else [props]:
        if isinstance(prop, dict) and "condominium" in str(prop.get("name", "")).lower():
            return _numero(prop.get("value"))
    return None


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
    if vagas is None:  # o VivaReal traz as vagas no texto de `keywords` ("... 3 banheiros, 2 vagas em ...")
        achado = _VAGAS.search(f"{no.get('keywords') or ''} {no.get('name') or ''}")
        vagas = float(achado.group(1)) if achado else None
    comodidades = [str(c.get("value") or c.get("name")) for c in no.get("amenityFeature") or [] if isinstance(c, dict)]
    rua, cidade = endereco.get("streetAddress"), endereco.get("addressLocality")
    titulo = str(no.get("name") or "")
    bairro = _BAIRRO.match(titulo)

    def texto(valor, formato):
        return formato.format(int(round(valor))) if valor is not None else "N/A"

    pets = no.get("petsAllowed")
    return {
        "external_id": _id_externo(no, url),
        "tipo_imovel": str(no.get("additionalType") or "").rsplit("/", 1)[-1] or None,  # House, Apartment, Place...
        "n_comodos": _numero(no.get("numberOfRooms")),
        "aceita_pets": int(pets) if isinstance(pets, bool) else None,
        "disponibilidade": str(oferta.get("availability") or "").rsplit("/", 1)[-1] or None,
        "condominio": _taxa_condominio(oferta),
        "json_ld": json.dumps(_sem_dados_do_anunciante(no), ensure_ascii=False),
        "url": url,
        "rua": rua or None,
        "bairro": bairro.group(1).strip() if bairro else None,
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
    datas: dict[str, str] = {}  # data de publicacao vem em outro bloco (RealEstateListing), ligada pelo id da URL
    for texto in blocos:
        try:
            dados = json.loads(texto)
        except (TypeError, ValueError):
            continue
        for no in _percorrer(dados):
            if no.get("datePosted") and no.get("url"):
                datas[_id_externo({}, str(no["url"])) or str(no["url"])] = str(no["datePosted"])
            if "offers" not in no:
                continue
            anuncio = _anuncio(no)
            if anuncio:
                vistos.setdefault(anuncio["external_id"] or anuncio["url"], anuncio)
    for chave, anuncio in vistos.items():
        anuncio["data_publicacao"] = datas.get(chave)
    return list(vistos.values())


class _BlocosLdJson(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocos: list[str] = []
        self._dentro = False

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self._dentro = True
            self.blocos.append("")

    def handle_endtag(self, tag):
        if tag == "script":
            self._dentro = False

    def handle_data(self, dados):
        if self._dentro:
            self.blocos[-1] += dados


def blocos_do_html(html: str) -> list[str]:
    """Textos dos `<script type="application/ld+json">` de uma pagina HTML (a resposta que o Network mostra)."""
    leitor = _BlocosLdJson()
    leitor.feed(html)
    return leitor.blocos
