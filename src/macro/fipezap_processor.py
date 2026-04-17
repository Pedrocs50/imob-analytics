import pandas as pd
import os
import unicodedata

from src.database import Database, DB_PATH
from src.repository import DataRepository


class CSVReader:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def read(self) -> pd.DataFrame:
        print("[INFO] Lendo CSV bruto...")
        return pd.read_csv(self.filepath, header=[0, 1, 2, 3], encoding="latin-1")


class FipeZapCleaner:
    def __init__(self):
        self.meses = {
            "jan": "01", "fev": "02", "mar": "03", "abr": "04",
            "mai": "05", "jun": "06", "jul": "07", "ago": "08",
            "set": "09", "out": "10", "nov": "11", "dez": "12"
        }

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        print("[INFO] Limpando dados...")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = self._flatten_multiindex_columns(df.columns)
        else:
            df.columns = [str(col).strip() for col in df.columns]

        data_col = self._find_data_column(df)
        df = df.rename(columns={data_col: "data"})
        df["data"] = self._clean_data(df["data"])

        feature_map = self._find_relevant_columns(df)
        if "preco_m2" not in feature_map:
            feature_map["preco_m2"] = self._find_preco_column(df)

        output_cols = ["data"] + [feature_map[name] for name in feature_map]
        df = df[output_cols].copy()
        df = df.rename(columns={v: k for k, v in feature_map.items()})

        for col in df.columns:
            if col == "data":
                continue
            df[col] = self._clean_numeric(df[col])

        df = df.dropna(subset=["data", "preco_m2"])
        df = df.sort_values("data")

        print(f"[INFO] Linhas limpas: {len(df)}")

        return df

    def _find_relevant_columns(self, df: pd.DataFrame) -> dict[str, str]:
        found = {
            "preco": [],
            "var_mensal": [],
            "var_12m": [],
            "yield": []
        }

        for col in df.columns:
            if self._matches_column(col, ["preco medio", "preco médio", "pre�o m�dio", "preco m�dio", "r$/m"]):
                found["preco"].append(col)
            elif self._matches_column(col, ["var. mensal", "var mensal"]):
                found["var_mensal"].append(col)
            elif self._matches_column(col, ["var. em 12 meses", "var em 12 meses"]):
                found["var_12m"].append(col)
            elif self._matches_column(col, ["rentabilidade do aluguel", "rental yield"]):
                found["yield"].append(col)

        feature_map = {}
        if len(found["preco"]) > 0:
            feature_map["preco_m2"] = found["preco"][0]
        if len(found["preco"]) > 1:
            feature_map["preco_m2_locacao_residencial"] = found["preco"][1]

        if len(found["var_mensal"]) > 0:
            feature_map["var_mensal_venda_residencial"] = found["var_mensal"][0]
        if len(found["var_mensal"]) > 1:
            feature_map["var_mensal_locacao_residencial"] = found["var_mensal"][1]

        if len(found["var_12m"]) > 0:
            feature_map["var_12m_venda_residencial"] = found["var_12m"][0]
        if len(found["var_12m"]) > 1:
            feature_map["var_12m_locacao_residencial"] = found["var_12m"][1]

        if len(found["yield"]) > 0:
            feature_map["rentabilidade_aluguel_residencial"] = found["yield"][0]

        return feature_map

    def _matches_column(self, col: object, patterns: list[str]) -> bool:
        name = str(col).strip().lower()
        for pattern in patterns:
            if pattern in name:
                return True
        return False

    def _clean_numeric(self, serie: pd.Series) -> pd.Series:
        return (
            serie.astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.replace("%", "", regex=False)
            .str.replace(" ", "", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )

    def _flatten_multiindex_columns(self, columns: pd.MultiIndex) -> list[str]:
        flattened = []
        for col in columns:
            parts = [str(item).strip() for item in col if str(item).strip() and not str(item).startswith("Unnamed")]
            if not parts:
                parts = [str(col[-1]).strip()]
            flattened.append(" ".join(parts))

        unique_names = []
        counts = {}
        for name in flattened:
            if name in counts:
                counts[name] += 1
                unique_names.append(f"{name}_{counts[name]}")
            else:
                counts[name] = 0
                unique_names.append(name)
        return unique_names

    def _normalize_column_name(self, name: object) -> str:
        text = str(name).strip().lower()
        try:
            text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        except Exception:
            pass
        return text

    def _find_data_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            norm = self._normalize_column_name(col)
            if norm == "data" or norm.endswith(" data") or norm.startswith("data "):
                return col

        for col in df.columns:
            if "data" in self._normalize_column_name(col):
                return col

        return df.columns[1] if len(df.columns) > 1 else df.columns[0]

    def _find_preco_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if self._matches_column(col, ["preco medio", "preco médio", "pre�o m�dio", "preco m�dio", "r$/m"]):
                return col

        print("[WARNING] Coluna não encontrada automaticamente, usando fallback...")
        for col in df.columns:
            if "total" in self._normalize_column_name(col):
                continue
            return col
        return df.columns[-1]

    def _clean_preco(self, serie: pd.Series) -> pd.Series:
        return (
            serie.astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )

    def _clean_data(self, serie: pd.Series) -> pd.Series:
        def parse(valor):
            try:
                mes, ano = valor.split("-")
                mes = self.meses[mes[:3].lower()]
                ano = "20" + ano
                return f"{ano}-{mes}-01"
            except:
                return None

        return pd.to_datetime(serie.astype(str).apply(parse), errors="coerce")


class CSVWriter:
    def __init__(self, output_path: str):
        self.output_path = output_path

    def write(self, df: pd.DataFrame):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        df.to_csv(self.output_path, index=False)
        print(f"[SUCCESS] Salvo em: {self.output_path}")


class DBWriter:
    def __init__(self, db_path: str = DB_PATH):
        self.db = Database(db_path)
        self.db.setup()
        self.repo = DataRepository(self.db)

    def write(self, df: pd.DataFrame):
        self.repo.salvar_fipezap_sjc(df)
        print(f"[SUCCESS] Salvo no banco: {self.db.db_path}")


class FipeZapProcessor:
    def __init__(self, reader: CSVReader, cleaner: FipeZapCleaner, writer):
        self.reader = reader
        self.cleaner = cleaner
        self.writer = writer

    def execute(self):
        df_raw = self.reader.read()
        df_clean = self.cleaner.clean(df_raw)
        self.writer.write(df_clean)


if __name__ == "__main__":
    INPUT_PATH = "data/raw/fipezap_sjc.csv"

    reader = CSVReader(INPUT_PATH)
    cleaner = FipeZapCleaner()
    writer = DBWriter()

    processor = FipeZapProcessor(reader, cleaner, writer)
    processor.execute()