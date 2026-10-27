import re
import unicodedata
import pandas as pd

from src.database import Database
from src.repository import DataRepository


class DataCleaner:
    """
    Responsabilidade única: transformar dados brutos em dados limpos e salvá-los.
    Não sabe de scraping, não sabe de análise.
    """

    def __init__(self, db: Database):
        self._repo = DataRepository(db)

    def executar(self) -> pd.DataFrame:
        print("[CLEANER] Carregando dados brutos do banco...")
        df = self._repo.carregar_raw_como_df()
        print(f"[CLEANER] {len(df)} registros brutos carregados.")

        df = self._limpar(df)
        df = self._remover_duplicatas(df)
        df = self._filtrar_invalidos(df)

        self._repo.salvar_processados(df)
        print(f"[CLEANER] {len(df)} imóveis únicos e válidos salvos em imoveis_processados.")
        return df

    # ------------------------------------------------------------------
    # Pipeline de transformação
    # ------------------------------------------------------------------

    def _limpar(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['tipo'] = df['endereco'].apply(self._definir_tipo)
        df['area_m2'] = df['area'].apply(self._extrair_numero)
        df['preco_venda'] = df['preco'].apply(self._limpar_preco)
        df['qtd_quartos'] = df['quartos'].apply(self._extrair_numero)
        df['qtd_banheiros'] = df['banheiros'].apply(self._extrair_numero)
        df['qtd_vagas'] = df['vagas'].apply(self._extrair_numero)
        return df


    def _remover_duplicatas(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicatas pelo conjunto (endereco + preco_venda + area_m2).
        Isso cobre imóveis que aparecem em múltiplos segmentos de preço.
        """
        antes = len(df)
        if 'external_id' in df:
            # com id do anuncio, a chave e (fonte, id); so os registros sem id caem na regra aproximada
            chave_id = ['fonte', 'external_id'] if 'fonte' in df else ['external_id']
            com_id = df['external_id'].notna()
            df = pd.concat([df[com_id].drop_duplicates(subset=chave_id), df[~com_id]])
        df = df.drop_duplicates(subset=['endereco', 'preco_venda', 'area_m2'])
        df = self._remover_duplicatas_entre_fontes(df)
        removidos = antes - len(df)
        print(f"[CLEANER] Duplicatas removidas: {removidos}")
        return df

    TOLERANCIA_PRECO_ENTRE_FONTES = 0.03

    def _remover_duplicatas_entre_fontes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mesmo imovel anunciado em dois portais: mesma rua, area, quartos e banheiros, com preco dentro de 3%.
        O preco entra na regra porque apartamentos iguais no mesmo predio tem rua, area e comodos identicos.
        Mantem o anuncio da primeira fonte em ordem alfabetica; so compara fontes diferentes."""
        if not {'fonte', 'rua'} <= set(df.columns):
            return df
        antes = len(df)
        df = df.copy()
        df['_rua'] = df['rua'].map(self._normalizar_rua)
        chave = ['_rua', 'area_m2', 'qtd_quartos', 'qtd_banheiros']
        sem_chave = df['_rua'].eq('') | df['fonte'].isna()
        remover = []
        for _, grupo in df[~sem_chave].groupby(chave, dropna=False):
            if grupo['fonte'].nunique() < 2:
                continue
            mantidos = []  # (fonte, preco) dos anuncios que ficam
            for idx, linha in grupo.sort_values(['fonte', 'preco_venda']).iterrows():
                duplicado = any(f != linha['fonte'] and abs(p - linha['preco_venda']) <= self.TOLERANCIA_PRECO_ENTRE_FONTES * p
                                for f, p in mantidos)
                if duplicado:
                    remover.append(idx)
                else:
                    mantidos.append((linha['fonte'], linha['preco_venda']))
        df = df.drop(index=remover).drop(columns='_rua')
        print(f"[CLEANER] Duplicatas entre fontes removidas: {antes - len(df)}")
        return df

    @staticmethod
    def _normalizar_rua(rua) -> str:
        if pd.isna(rua):
            return ''
        texto = unicodedata.normalize('NFKD', str(rua)).encode('ascii', 'ignore').decode().lower()
        texto = re.sub(r'\b(rua|r|avenida|av|travessa|tv|alameda|al|estrada|est)\b\.?', ' ', texto)
        return re.sub(r'[^a-z0-9]+', ' ', texto).strip()

    def _filtrar_invalidos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove imóveis sem preço ou sem área e calcula preço/m²."""
        antes = len(df)

        df = df.dropna(subset=['preco_venda', 'area_m2'])
        df = df[df['area_m2'] > 0]

        # Calcula só depois de validar dados e arredonda para 2 casas
        df['preco_m2'] = (df['preco_venda'] / df['area_m2']).round(2)

        print(f"[CLEANER] Removidos sem preço/área: {antes - len(df)}")
        return df


    # ------------------------------------------------------------------
    # Funções de transformação individuais (privadas)
    # ------------------------------------------------------------------

    @staticmethod
    def _definir_tipo(titulo: str) -> str:
        titulo = str(titulo).lower()
        if 'apartamento' in titulo:
            return 'Apartamento'
        if 'casa' in titulo or 'sobrado' in titulo:
            return 'Casa'
        if 'terreno' in titulo or 'lote' in titulo:
            return 'Terreno'
        return 'Outro'

    @staticmethod
    def _extrair_numero(texto) -> float | None:
        if pd.isna(texto) or str(texto).strip() in ('N/A', ''):
            return None
        numeros = re.findall(r'\d+', str(texto).replace('.', ''))
        return float(numeros[0]) if numeros else None

    @staticmethod
    def _limpar_preco(texto) -> float | None:
        if pd.isna(texto):
            return None
        limpo = str(texto).split('Cond')[0].split('IPTU')[0]
        valor = re.sub(r'[^\d]', '', limpo)
        return float(valor) if valor else None