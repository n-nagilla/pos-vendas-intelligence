import streamlit as st
import pandas as pd

def render(df):
    st.subheader("📦 Controle de Peças Pendentes & B.O.")
    
    if df.empty:
        st.info("Nenhuma Ordem de Serviço na base.")
        return

    df_pecas = df[df.get("Necessita_Peca", "") == "Sim"] if "Necessita_Peca" in df.columns else df
    
    st.markdown("### Peças Pendentes")
    colunas_pecas = [c for c in [
        "Numero", "Cliente", "Modelo", "Codigo_Descricao_Peca", 
        "Data_Pedido", "Previsao_Peca", "Peca_BO", "Gargalo_Atual"
    ] if c in df.columns]
    
    st.dataframe(df_pecas[colunas_pecas] if not df_pecas.empty else df_pecas, use_container_width=True, hide_index=True)

    st.markdown("### 🚨 Maiores Atrasos de Peças (Ranking)")
    if "Peca_BO" in df.columns:
        bo_df = df[df["Peca_BO"] == "Sim"]
        if not bo_df.empty:
            st.warning(f"Identificados {len(bo_df)} itens críticos em B.O. aguardando posicionamento da AGCO Parts.")
            st.dataframe(bo_df[["Numero", "Cliente", "Codigo_Descricao_Peca", "Data_Pedido"]], use_container_width=True, hide_index=True)
        else:
            st.success("Nenhuma peça em B.O. registrada no momento.")
    else:
        st.info("Coluna de B.O. não encontrada na base.")
