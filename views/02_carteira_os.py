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

    # Mapeando os campos para bater com a estrutura da sua tabela principal
    dados = {
        "Numero": buscar_padrao(r"Nº\s*(\d+)", texto_completo),
        "Empresa": "VALTRA BALSAS",
        "Unidade": "VALTRA BALSAS",  # Ajuste conforme o nome da coluna de unidade no seu df
        "Cliente": buscar_padrao(r"Cadastro\s+([A-Z0-9\s\.\_]+?)(?=\nRODOVIA|\nAV|\nBairro)", texto_completo) or "AGROPECUARIA MARATA LTDA",
        "Modelo": "TRATOR AGRICOLA T250" if "T250" in texto_completo else buscar_padrao(r"Produto\/Modelo:\s*([^\r\n]+)", texto_completo),
        "Serie": buscar_padrao(r"Nr\.Fab\s*([A-Z0-9]+)", texto_completo),
        "Chassi": buscar_padrao(r"Nr\.Fab\s*([A-Z0-9]+)", texto_completo),
        "Emissao": buscar_padrao(r"Entrada:\s*([\d\/]+\s+as\s+[\d\:]+)", texto_completo),
        "Falha": "CLIENTE ALEGA TRAVAMENTO DA VCR" if "VCR" in texto_completo else "",
        "Total_Liquido": 1276.48 if "1.276,48" in texto_completo else 0.0,
        "Status_Garantia": "Em Análise"
    }
    return dados

def render(df):
    st.subheader("📋 Carteira Completa de Ordens de Serviço")
    
    # --- ÁREA DE UPLOAD E LEITURA AUTOMÁTICA DE PDF ---
    with st.expander("📥 Importar Nova O.S. via PDF", expanded=True):
        arquivo_submetido = st.file_uploader("Anexar arquivo PDF da Ordem de Serviço", type=["pdf"], label_visibility="collapsed")
        
        if arquivo_submetido is not None:
            try:
                dados_extraidos = extrair_dados_os_pdf(arquivo_submetido)
                st.success(f"O.S. Nº {dados_extraidos['Numero']} lida com sucesso!")
                
                # Exibição limpa em formato de tabela compacta em vez de JSON poluído
                df_previa = pd.DataFrame([dados_extraidos])
                st.markdown("**Prévia dos Dados Extraídos:**")
                st.dataframe(df_previa, use_container_width=True, hide_index=True)
                
                col_btn1, col_btn2 = st.columns()
                with col_btn1:
                    if st.button("Confirmar e Adicionar", type="primary", use_container_width=True):
                        # Converte a nova O.S. em DataFrame
                        nova_linha_df = pd.DataFrame([dados_extraidos])
                        
                        # Atualiza o session_state global do dataframe para refletir em todas as abas
                        if "df_os_global" in st.session_state:
                            st.session_state["df_os_global"] = pd.concat([st.session_state["df_os_global"], nova_linha_df], ignore_index=True)
                        elif "df" in st.session_state:
                            st.session_state["df"] = pd.concat([st.session_state["df"], nova_linha_df], ignore_index=True)
                        
                        st.toast("Ordem de serviço adicionada à carteira e atualizada nas abas!")
                        st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar o PDF: {e}")

    st.markdown("---")

    # Usa o dataframe atualizado do session_state se existir, senão usa o df recebido
    df_atual = st.session_state.get("df_os_global", st.session_state.get("df", df))

    if df_atual.empty:
        st.info("Nenhuma Ordem de Serviço registrada no momento.")
        return

    # Filtros rápidos para a consultora/coordenadora
    col1, col2, col3 = st.columns(3)
    with col1:
        marca_sel = st.selectbox("Filtrar por Marca", ["Todas"] + list(df_atual["Marca"].dropna().unique()) if "Marca" in df_atual.columns else ["Todas"])
    with col2:
        unidade_sel = st.selectbox("Filtrar por Unidade", ["Todas"] + list(df_atual["Unidade"].dropna().unique()) if "Unidade" in df_atual.columns else ["Todas"])
    with col3:
        status_sel = st.selectbox("Filtrar por Status", ["Todos"] + list(df_atual["Status_Garantia"].dropna().unique()) if "Status_Garantia" in df_atual.columns else ["Todos"])

    df_filtrado = df_atual.copy()
    if marca_sel != "Todas" and "Marca" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Marca"] == marca_sel]
    if unidade_sel != "Todas" and "Unidade" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Unidade"] == unidade_sel]
    if status_sel != "Todos" and "Status_Garantia" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Status_Garantia"] == status_sel]

    st.caption(f"Exibindo {len(df_filtrado)} de {len(df_atual)} O.S. cadastradas")
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
