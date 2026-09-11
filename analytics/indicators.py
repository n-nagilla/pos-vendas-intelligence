import pandas as pd
import numpy as np

class MetricasFinanceiras:
    @staticmethod
    def calcular_kpis_gerais(df: pd.DataFrame) -> dict:
        if df.empty:
            return {
                "total": 0.0, "total_adm": 0.0, "total_pessoal": 0.0,
                "total_vendas": 0.0, "media_mensal": 0.0, "top_conta": ("N/A", 0.0)
            }
        
        total = df["Valor_Liquido"].sum()
        total_adm = df[df["Dre"] == "DESPESAS ADMINISTRATIVAS"]["Valor_Liquido"].sum()
        total_pessoal = df[df["Dre"] == "DESPESAS COM PESSOAL"]["Valor_Liquido"].sum()
        total_vendas = df[df["Dre"] == "DESPESAS COM VENDAS"]["Valor_Liquido"].sum()
        
        meses_contados = max(df["Competencia"].nunique(), 1)
        media_mensal = total / meses_contados
        
        # Maior conta ofensora
        ranking = df.groupby("Conta")["Valor_Liquido"].sum().sort_values(ascending=False)
        top_conta = (ranking.index[0], ranking.iloc[0]) if not ranking.empty else ("N/A", 0.0)
        
        return {
            "total": total,
            "total_adm": total_adm,
            "total_pessoal": total_pessoal,
            "total_vendas": total_vendas,
            "media_mensal": media_mensal,
            "top_conta": top_conta
        }

    @staticmethod
    def calcular_evolucao_mensal(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        return df.groupby(["Competencia", "Dre"])["Valor_Liquido"].sum().reset_index()

    @staticmethod
    def ranking_ofensores(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        res = df.groupby(["Conta", "Dre"])["Valor_Liquido"].sum().reset_index()
        return res.sort_values(by="Valor_Liquido", ascending=False).head(top_n)