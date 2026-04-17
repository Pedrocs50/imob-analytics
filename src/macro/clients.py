from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import unicodedata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_number(raw: Any) -> float | None:
    if raw is None:
        return None

    txt = str(raw).strip()
    if txt in ("", "...", "-", "null", "None"):
        return None

    if "," in txt and "." in txt:
        txt = txt.replace(".", "").replace(",", ".")
    elif "," in txt:
        txt = txt.replace(",", ".")

    try:
        return float(txt)
    except ValueError:
        return None


def _parse_bcb_date(d: str) -> date:
    return datetime.strptime(d, "%d/%m/%Y").date()


def _infer_freq_from_period_code(code: str) -> str:
    digits = re.sub(r"\D", "", str(code))
    if len(digits) == 8:
        return "D"
    if len(digits) == 6:
        return "M"
    if len(digits) == 5:
        return "Q"
    if len(digits) == 4:
        return "A"
    return "M"


def _period_code_to_date(code: str) -> date | None:
    digits = re.sub(r"\D", "", str(code))
    if len(digits) == 8:
        y, m, d = int(digits[0:4]), int(digits[4:6]), int(digits[6:8])
        return date(y, m, d)
    if len(digits) == 6:
        y, m = int(digits[0:4]), int(digits[4:6])
        return date(y, m, 1)
    if len(digits) == 5:
        y, q = int(digits[0:4]), int(digits[4])
        m = {1: 1, 2: 4, 3: 7, 4: 10}.get(q, 1)
        return date(y, m, 1)
    if len(digits) == 4:
        return date(int(digits), 1, 1)
    return None


# ---------------------------------------------------------------------------
# Base HTTP
# ---------------------------------------------------------------------------

class BaseHttpClient:
    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.session = requests.Session()

        retries = Retry(
            total=4,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# BCB / SGS
# ---------------------------------------------------------------------------

class BCBClient(BaseHttpClient):
    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

    def _fetch_sgs_chunk(
        self,
        codigo_serie: str,
        data_inicial: date | None,
        data_final: date | None,
    ) -> list[dict]:
        params: dict[str, str] = {"formato": "json"}
        if data_inicial:
            params["dataInicial"] = data_inicial.strftime("%d/%m/%Y")
        if data_final:
            params["dataFinal"] = data_final.strftime("%d/%m/%Y")

        url = self.BASE_URL.format(codigo=codigo_serie)
        data = self.get_json(url, params=params)
        return data if isinstance(data, list) else []

    def fetch_sgs(
        self,
        codigo_serie: str,
        data_inicial: str | None = None,
        data_final: str | None = None,
    ) -> list[dict]:
        start = datetime.strptime(data_inicial, "%Y-%m-%d").date() if data_inicial else None
        end   = datetime.strptime(data_final,   "%Y-%m-%d").date() if data_final   else date.today()

        if start is None:
            raw = self._fetch_sgs_chunk(codigo_serie, None, end)
            return [
                {"data_ref": _parse_bcb_date(r["data"]), "valor": _parse_number(r.get("valor"))}
                for r in raw
                if _parse_number(r.get("valor")) is not None
            ]

        bloco_dias  = 3300
        atual       = start
        acumulado: list[dict] = []

        while atual <= end:
            fim_bloco = min(atual + timedelta(days=bloco_dias), end)
            raw = self._fetch_sgs_chunk(codigo_serie, atual, fim_bloco)
            for r in raw:
                v = _parse_number(r.get("valor"))
                if v is not None:
                    acumulado.append({"data_ref": _parse_bcb_date(r["data"]), "valor": v})
            atual = fim_bloco + timedelta(days=1)

        dedup = {r["data_ref"]: r["valor"] for r in acumulado}
        return [{"data_ref": d, "valor": dedup[d]} for d in sorted(dedup.keys())]


# ---------------------------------------------------------------------------
# IBGE / SIDRA
# ---------------------------------------------------------------------------

class IBGESidraClient(BaseHttpClient):
    BASE_URL = "https://apisidra.ibge.gov.br/values/{sidra_path}"

    def fetch_sidra(self, sidra_path: str) -> list[dict]:
        sidra_path = sidra_path.strip("/")
        data = self.get_json(self.BASE_URL.format(sidra_path=sidra_path))
        return [x for x in data if isinstance(x, dict)] if isinstance(data, list) else []

    @staticmethod
    def normalize_sidra_rows(rows: list[dict], meta: dict) -> list[dict]:
        out: list[dict] = []

        def _normalize_text(s: str) -> str:
            s = unicodedata.normalize("NFKD", str(s))
            return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()

        filtros    = [_normalize_text(x) for x in meta.get("filtro_texto", [])]
        value_key  = meta.get("value_key", "V")
        forced_pk  = meta.get("period_key")
        forced_freq = meta.get("frequencia_origem")

        for row in rows:
            raw_val = row.get(value_key)
            val = _parse_number(raw_val)
            if val is None:
                continue

            if filtros:
                text_fields = [str(v) for k, v in row.items() if str(k).endswith("N")]
                pool = _normalize_text(" ".join(text_fields))
                if not all(f in pool for f in filtros):
                    continue

            period_key = forced_pk
            if not period_key:
                for k in row.keys():
                    if not re.match(r"^D\d+C$", k):
                        continue
                    candidate = str(row.get(k, "")).strip()
                    # Só aceita como coluna de período se os primeiros 4 dígitos
                    # formam um ano plausível (1990–2035).
                    # Isso evita pegar colunas de classificação cujo valor é
                    # um código numérico como "4099", "5933", "5941", etc.
                    digits = re.sub(r"\D", "", candidate)
                    # Só aceita formatos válidos de período:
                    # YYYYMM, YYYYQ, YYYY, YYYYMMDD
                    if len(digits) in (4, 5, 6, 8):
                        year = int(digits[:4])
                        if 1990 <= year <= 2035:
                            period_key = k
                            break

            if not period_key:
                continue

            period_code = str(row.get(period_key, "")).strip()
            dt = _period_code_to_date(period_code)
            # Dupla checagem: rejeita datas com ano fora do range esperado
            if dt is None:
                continue

            # mata lixo tipo 4099, 5933, etc
            if dt.year < 1990 or dt.year > 2035:
                continue

            # opcional: garante que mês faz sentido
            if dt.month < 1 or dt.month > 12:
                continue

            freq = forced_freq or _infer_freq_from_period_code(period_code)

            out.append({
                "fonte":        meta["fonte"],
                "codigo_serie": meta["codigo_serie"],
                "nome_serie":   meta["nome_serie"],
                "data_ref":     dt,
                "valor":        val,
                "unidade":      meta.get("unidade"),
                "frequencia":   freq,
            })

        return out


# ---------------------------------------------------------------------------
# IpeaData  (OData4 – sem token)
#
# Endpoint:
#   http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='<codigo>')
#
# Cada linha do array "value" tem:
#   SERCODIGO  str   – código da série
#   VALDATA    str   – ISO 8601  "2024-01-01T00:00:00-03:00"
#   VALVALOR   float | null
# ---------------------------------------------------------------------------

class IpeaDataClient(BaseHttpClient):
    BASE_URL = "http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{codigo}')"

    def fetch_serie(self, codigo_serie: str) -> list[dict]:
        """
        Baixa todos os pontos de uma série IpeaData.
        Retorna lista de {'data_ref': date, 'valor': float}.
        """
        url  = self.BASE_URL.format(codigo=codigo_serie)
        data = self.get_json(url)

        rows = data.get("value", []) if isinstance(data, dict) else []
        out: list[dict] = []

        for row in rows:
            val = _parse_number(row.get("VALVALOR"))
            if val is None:
                continue

            raw_date = str(row.get("VALDATA", "")).strip()
            dt = self._parse_ipea_date(raw_date)
            if dt is None:
                continue

            out.append({"data_ref": dt, "valor": val})

        # garante ordem cronológica
        out.sort(key=lambda r: r["data_ref"])
        return out

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_ipea_date(raw: str) -> date | None:
        """
        Aceita formatos que o IpeaData retorna:
          '2024-01-01T00:00:00-03:00'
          '2024-01-01T00:00:00'
          '2024-01-01'
        """
        if not raw:
            return None
        # remove timezone offset e microsegundos
        raw = re.sub(r"([+-]\d{2}:\d{2}|Z)$", "", raw).strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None