import os
import streamlit as st
import pandas as pd
from data.ingestion import ERPDataPipeline

CAMINHO_CONSOLIDADO = os.path.join("data", "raw", "DESPESAS_CONSOLIDADAS_HISTORICO.xlsx")
CAMINHO_PADRAO_INICIAL = os.path.join("data", "raw", "DA DP DV 1 A 8 - 26.xlsx")

@st.cache_data(show_spinner=False)
def carregar_dados_disco(caminho: str) -> pd.DataFrame:
    pipeline = ERPDataPipeline()
    return pipeline.processar_arquivo(caminho)

def obter_dados_ativos() -> pd.DataFrame:
    """Retorna a base consolidada ativa na memória ou carrega do disco."""
    if "dados_despesas" in st.session_state and st.session_state["dados_despesas"] is not None:
        return st.session_state["dados_despesas"]
    
    # 1. Tenta carregar a base consolidada acumulada
    if os.path.exists(CAMINHO_CONSOLIDADO):
        df = carregar_dados_disco(CAMINHO_CONSOLIDADO)
        st.session_state["dados_despesas"] = df
        return df
    
    # 2. Se for a primeira vez, carrega o arquivo inicial (1 a 8)
    if os.path.exists(CAMINHO_PADRAO_INICIAL):
        df = carregar_dados_disco(CAMINHO_PADRAO_INICIAL)
        st.session_state["dados_despesas"] = df
        return df
    
    return pd.DataFrame()

def atualizar_base_com_upload(arquivo_upload) -> pd.DataFrame:
    """
    Acrescenta os novos lançamentos (ex: mês de Setembro) à base histórica,
    eliminando duplicidades com base no código único do lançamento do NBS/ERP.
    """
    pipeline = ERPDataPipeline()
    df_novo = pipeline.processar_arquivo(arquivo_upload)
    df_existente = obter_dados_ativos()
    
    if not df_existente.empty:
        # Junta o histórico existente com o novo mês
        df_consolidado = pd.concat([df_existente, df_novo], ignore_index=True)
        
        # Elimina duplicidades baseado no código único do lançamento contábil
        if "Lancamento_Codigo" in df_consolidado.columns and df_consolidado["Lancamento_Codigo"].notna().any():
            df_consolidado = df_consolidado.drop_duplicates(subset=["Lancamento_Codigo"], keep="last")
        elif "idOrigem" in df_consolidado.columns and df_consolidado["idOrigem"].notna().any():
            df_consolidado = df_consolidado.drop_duplicates(subset=["idOrigem"], keep="last")
        else:
            # Fallback caso os IDs venham vazios
            df_consolidado = df_consolidado.drop_duplicates(
                subset=["Lancamento_Data", "Empresa_NomeFantasia", "Conta", "Debito", "Credito"],
                keep="last"
            )
    else:
        df_consolidado = df_novo

    # Ordena cronologicamente
    df_consolidado = df_consolidado.sort_values(by="Lancamento_Data").reset_index(drop=True)

    # Salva a base unificada permanente
    os.makedirs(os.path.join("data", "raw"), exist_ok=True)
    df_consolidado.to_excel(CAMINHO_CONSOLIDADO, index=False)
    
    # Atualiza a sessão e limpa cache do Streamlit
    st.session_state["dados_despesas"] = df_consolidado
    st.cache_data.clear()
    
    return df_consolidado