import streamlit as st
import pandas as pd

def render(df):
    st.subheader("📋 Carteira Completa de Ordens de Serviço")
    
    if df.empty:
        st.info("Nenhuma Ordem de Serviço registrada no momento.")
        return

    # Filtros rápidos para a consultora/coordenadora
    col1, col2, col3 = st.columns(3)
    with col1:
        marca_sel = st.selectbox("Filtrar por Marca", ["Todas"] + list(df["Marca"].dropna().unique()) if "Marca" in df.columns else ["Todas"])
    with col2:
        unidade_sel = st.selectbox("Filtrar por Unidade", ["Todas"] + list(df["Unidade"].dropna().unique()) if "Unidade" in df.columns else ["Todas"])
    with col3:
        status_sel = st.selectbox("Filtrar por Status", ["Todos"] + list(df["Status_Garantia"].dropna().unique()) if "Status_Garantia" in df.columns else ["Todos"])

    df_filtrado = df.copy()
    if marca_sel != "Todas" and "Marca" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Marca"] == marca_sel]
    if unidade_sel != "Todas" and "Unidade" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Unidade"] == unidade_sel]
    if status_sel != "Todos" and "Status_Garantia" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Status_Garantia"] == status_sel]

    st.caption(f"Exibindo {len(df_filtrado)} de {len(df)} O.S. cadastradas")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
