import streamlit as st
import pandas as pd
from datetime import datetime

def render(df):
    st.subheader("⏱️ Controle do Processo de Garantia & Prazos (30d / 60d)")
    
    if df.empty:
        st.info("Nenhum dado disponível para análise de prazos.")
        return

    hoje = datetime.now()
    if "Emissao" in df.columns:
        dt_emissao = pd.to_datetime(df["Emissao"], format="%d/%m/%Y", errors="coerce")
        df["Dias_Aberto_OS"] = (hoje - dt_emissao).dt.days.fillna(0).astype(int)
    else:
        df["Dias_Aberto_OS"] = 0

    colunas_exibir = [c for c in [
        "Numero", "Cliente", "Modelo", "Emissao", "Dias_Aberto_OS", 
        "Semáforo_Prazo", "Status_Garantia", "AOL_Protocolo"
    ] if c in df.columns]

    st.dataframe(df[colunas_exibir], use_container_width=True, hide_index=True)
