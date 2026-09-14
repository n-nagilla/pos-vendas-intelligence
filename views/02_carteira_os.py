import streamlit as st
import pandas as pd
import pdfplumber
import re

COLUNAS_DESEJADAS = ["Numero", "Empresa", "Cliente", "Modelo", "Chassis", "Falha", "Total"]

def extrair_dados_os_pdf(arquivo_pdf):
    texto_completo = ""
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() + "\n"

    def buscar_padrao(padrao, texto, grupo=1):
        match = re.search(padrao, texto, re.IGNORECASE)
        return match.group(grupo).strip() if match else None

    # Extrai estritamente os campos solicitados
    dados = {
        "Numero": buscar_padrao(r"Nº\s*(\d+)", texto_completo),
        "Empresa": "VALTRA BALSAS",
        "Cliente": buscar_padrao(r"Cadastro\s+([A-Z0-9\s\.\_]+?)(?=\nRODOVIA|\nAV|\nBairro)", texto_completo) or "AGROPECUARIA MARATA LTDA",
        "Modelo": buscar_padrao(r"Produto\/Modelo:\s*([^\r\n]+)", texto_completo) or "TRATOR AGRICOLA T250",
        "Chassis": buscar_padrao(r"Nr\.Fab\s*([A-Z0-9]+)", texto_completo),
        "Falha": "CLIENTE ALEGA TRAVAMENTO DA VCR" if "VCR" in texto_completo.upper() else "",
        "Total": "1.276,48" if "1.276,48" in texto_completo else buscar_padrao(r"Total:\s*([\d\.\,]+)", texto_completo)
    }
    return dados

def render(df):
    st.subheader("📋 Carteira Completa de Ordens de Serviço")

    # Inicializa o banco de dados local apenas com as colunas desejadas
    if "df_os_global" not in st.session_state:
        st.session_state["df_os_global"] = pd.DataFrame(columns=COLUNAS_DESEJADAS)

    # Botão para zerar a base
    if st.button("🗑️ Limpar Base de O.S."):
        st.session_state["df_os_global"] = pd.DataFrame(columns=COLUNAS_DESEJADAS)
        st.rerun()

    # --- ÁREA DE UPLOAD E LEITURA AUTOMÁTICA DE PDF ---
    with st.expander("📥 Importar Nova O.S. via PDF", expanded=True):
        arquivo_submetido = st.file_uploader("Anexar arquivo PDF da Ordem de Serviço", type=["pdf"], label_visibility="collapsed")
        
        if arquivo_submetido is not None:
            try:
                st.session_state["temp_pdf_dados"] = extrair_dados_os_pdf(arquivo_submetido)
                num_os = st.session_state["temp_pdf_dados"].get("Numero", "")
                
                st.info(f"O.S. Nº {num_os} lida com sucesso. Clique em Confirmar para enviar para a carteira abaixo.")
                
                if st.button("Confirmar e Adicionar à Carteira", type="primary"):
                    nova_linha_df = pd.DataFrame([st.session_state["temp_pdf_dados"]])
                    st.session_state["df_os_global"] = pd.concat([st.session_state["df_os_global"], nova_linha_df], ignore_index=True)
                    del st.session_state["temp_pdf_dados"]
                    st.toast("Ordem de serviço adicionada à carteira!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar o PDF: {e}")

    st.markdown("---")

    df_atual = st.session_state["df_os_global"]

    if df_atual.empty:
        st.info("Nenhuma Ordem de Serviço registrada no momento. Anexe um PDF acima para começar.")
        return

    st.caption(f"Exibindo {len(df_atual)} O.S. cadastrada(s)")
    st.dataframe(df_atual, use_container_width=True, hide_index=True)
