import streamlit as st
import pandas as pd

def renderizar_filtros_superiores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        st.warning("Nenhum dado carregado.")
        return df

    # Filtros em 4 colunas horizontais
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 2, 2])
    
    with col1:
        marcas = ["TODAS"] + sorted(df["Marca"].unique().tolist())
        marca_sel = st.selectbox("🚜 Marca", marcas, index=0)

    with col2:
        df_base_filial = df if marca_sel == "TODAS" else df[df["Marca"] == marca_sel]
        filiais = ["TODAS"] + sorted(df_base_filial["Filial"].unique().tolist())
        filial_sel = st.selectbox("🏢 Filial", filiais, index=0)

    with col3:
        meses_disp = sorted(df["Mes_Ano"].unique().tolist())
        meses_sel = st.multiselect("📅 Meses", meses_disp, default=meses_disp)

    with col4:
        categorias = ["TODAS AS DESPESAS"] + sorted(df["Dre"].unique().tolist())
        cat_sel = st.selectbox("📁 Macro Categoria", categorias, index=0)

    # Aplicação estrita dos filtros
    df_f = df.copy()
    if marca_sel != "TODAS":
        df_f = df_f[df_f["Marca"] == marca_sel]
    if filial_sel != "TODAS":
        df_f = df_f[df_f["Filial"] == filial_sel]
    if meses_sel:
        df_f = df_f[df_f["Mes_Ano"].isin(meses_sel)]
    if cat_sel != "TODAS AS DESPESAS":
        df_f = df_f[df_f["Dre"] == cat_sel]

    st.markdown("---")
    return df_f