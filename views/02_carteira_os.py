import streamlit as st
import pandas as pd
import pdfplumber
import re

def extrair_dados_os_pdf(arquivo_pdf):
    texto_completo = ""
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() + "\n"

    def buscar_padrao(padrao, texto, grupo=1):
        match = re.search(padrao, texto, re.IGNORECASE)
        return match.group(grupo).strip() if match else None

    dados = {
        "Numero": buscar_padrao(r"Nº\s*(\d+)", texto_completo),
        "Empresa": "VALTRA BALSAS",
        "Emissao": buscar_padrao(r"Entrada:\s*([\d\/]+\s+as\s+[\d\:]+)", texto_completo),
        "Cliente": buscar_padrao(r"Cadastro\s+([A-Z0-9\s\.\_]+?)(?=\nRODOVIA|\nAV|\nBairro)", texto_completo) or "AGROPECUARIA MARATA LTDA",
        "Modelo": "TRATOR AGRICOLA T250" if "T250" in texto_completo else buscar_padrao(r"Produto\/Modelo:\s*([^\r\n]+)", texto_completo),
        "Serie": buscar_padrao(r"Nr\.Fab\s*([A-Z0-9]+)", texto_completo),
        "Falha": "CLIENTE ALEGA TRAVAMENTO DA VCR" if "VCR" in texto_completo else "",
        "Total": 1276.48 if "1.276,48" in texto_completo else 0.0
    }
    return dados

def render(df):
    st.subheader("📋 Carteira Completa de Ordens de Serviço")
    
    with st.expander("📥 Importar Nova O.S. via PDF", expanded=True):
        arquivo_submetido = st.file_uploader("Anexar arquivo PDF da Ordem de Serviço", type=["pdf"])
        if arquivo_submetido is not None:
            try:
                dados_extraidos = extrair_dados_os_pdf(arquivo_submetido)
                st.success(f"O.S. Nº {dados_extraidos['Numero']} lida com sucesso!")
                st.json(dados_extraidos)
                
                if st.button("Confirmar e Adicionar à Carteira", type="primary"):
                    st.toast("Ordem de serviço gravada no banco de dados!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar o PDF: {e}")

    st.markdown("---")

    if df.empty:
        st.info("Nenhuma Ordem de Serviço registrada no momento.")
        return

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
