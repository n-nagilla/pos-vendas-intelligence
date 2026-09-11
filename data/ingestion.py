import pandas as pd
import numpy as np
from datetime import datetime

class ERPDataPipeline:
    """
    Processa a planilha bruta exportada do sistema da concessionária (NBS/ERP),
    limpa cabeçalhos duplicados, normaliza datas, filiais, marcas e calcula valores líquidos.
    """
    
    MAPEAMENTO_MARCAS = {
        'MARDISA AGRO - FENDT BALSAS': ('FENDT', 'BALSAS'),
        'MARDISA AGRO - VALTRA BALSAS': ('VALTRA', 'BALSAS'),
        'MARDISA AGRO - VALTRA IMPERATRIZ': ('VALTRA', 'IMPERATRIZ'),
        'MARDISA AGRO - VALTRA A.ALEGRE': ('VALTRA', 'ALTO ALEGRE'),
    }

    MESES_PT = {
        1: '01 - Jan', 2: '02 - Fev', 3: '03 - Mar', 4: '04 - Abr',
        5: '05 - Mai', 6: '06 - Jun', 7: '07 - Jul', 8: '08 - Ago',
        9: '09 - Set', 10: '10 - Out', 11: '11 - Nov', 12: '12 - Dez'
    }

    def processar_arquivo(self, arquivo_ou_caminho) -> pd.DataFrame:
        # Lê a planilha bruta
        df_raw = pd.read_excel(arquivo_ou_caminho, sheet_name=0)

        # 1. Filtra apenas as linhas válidas de despesas (elimina cabeçalhos intermediários e nulos)
        categorias_validas = [
            'DESPESAS ADMINISTRATIVAS',
            'DESPESAS COM PESSOAL',
            'DESPESAS COM VENDAS'
        ]
        df = df_raw[df_raw['Dre'].isin(categorias_validas)].copy()

        # 2. Conversão e Tratamento de Datas
        df['Lancamento_Data'] = pd.to_datetime(df['Lancamento_Data'], errors='coerce')
        df = df.dropna(subset=['Lancamento_Data'])
        
        df['Ano'] = df['Lancamento_Data'].dt.year
        df['Mes_Num'] = df['Lancamento_Data'].dt.month
        df['Mes_Ano'] = df['Mes_Num'].map(self.MESES_PT)
        df['Competencia'] = df['Lancamento_Data'].dt.to_period('M').astype(str)

        # 3. Tratamento Financeiro (Débito - Crédito)
        df['Debito'] = pd.to_numeric(df['Debito'], errors='coerce').fillna(0)
        df['Credito'] = pd.to_numeric(df['Credito'], errors='coerce').fillna(0)
        
        # Em contabilidade DRE, despesa é débito. Estornos entram como crédito.
        # Calculamos o valor absoluto positivo para visualização gerencial direta
        df['Valor_Liquido'] = (df['Debito'] - df['Credito']).abs()

        # 4. Mapeamento de Marca, Filial e Nome Amigável
        df['Marca'] = df['Empresa_NomeFantasia'].apply(
            lambda x: self.MAPEAMENTO_MARCAS.get(str(x).strip(), ('OUTROS', 'OUTROS'))[0]
        )
        df['Filial'] = df['Empresa_NomeFantasia'].apply(
            lambda x: self.MAPEAMENTO_MARCAS.get(str(x).strip(), ('OUTROS', str(x)))[1]
        )
        df['Unidade_Completa'] = df['Marca'] + ' ' + df['Filial']

        # 5. Normalização de Textos
        df['Conta'] = df['Conta'].astype(str).str.strip().str.upper()
        df['Dre'] = df['Dre'].astype(str).str.strip().str.upper()
        df['Fornecedor'] = df['Fornecedor'].fillna('NÃO INFORMADO').astype(str).str.strip().str.upper()
        df['Lancamento_Historico'] = df['Lancamento_Historico'].fillna('').astype(str)

        return df