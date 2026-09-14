import streamlit as st
import pandas as pd
import pdfplumber
import re

def extrair_dados_os_pdf(arquivo_pdf, colunas_df):
    texto_completo = ""
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() + "\n"

    def buscar_padrao(padrao, texto, grupo=1):
        match = re.search(padrao, texto, re.IGNORECASE)
        return match.group(grupo).strip() if match else None

    dados = {col: None for col in colunas_df}

    if "Numero" in dados:
        dados["Numero"] = buscar_padrao(r"Nº\s*(\d+)", texto_completo)
    if "Cliente" in dados:
        dados["Cliente"] = buscar_padrao(r"Cadastro\s+([A-Z0-9\s\.\_]+?)(?=\nRODOVIA|\nAV|\nBairro)", texto_completo) or "CLIENTE NÃO IDENTIFICADO"
    if "Modelo" in dados:
        dados["Modelo"] = buscar_padrao(r"Produto\/Modelo:\s*([^\r\n]+)", texto_completo) or ("MOMENTUM 4" if "MOMENTUM" in texto_completo.upper() else "TRATOR T250")
    if "Serie" in dados:
        dados["Serie"] = buscar_padrao(r"Nr\.Fab\s*([A-Z0-9]+)", texto_completo)
    if "Chassi" in dados:
        dados["Chassi"] = buscar_padrao(r"Nr\.Fab\s*([A-Z0-9]+)", texto_completo)
    if "Emissao" in dados:
        dados["Emissao"] = buscar_padrao(r"Entrada:\s*([\d\/]+\s+as\s+[\d\:]+)", texto_completo)
    if "Marca" in dados:
        dados["Marca"] = "VALTRA"
    if "Unidade" in dados:
        dados["Unidade"] = "VALTRA BALSAS"
    if "Operacao" in dados:
        dados["Operacao"] = "Balsas"
    if "Status_Garantia" in dados:
        dados["Status_Garantia"] = "Em Análise"

    return dados

def render(df):
    st.subheader("📋 Carteira Completa de Ordens de Serviço")

    # Inicia a base limpa (sem carregar os dados antigos da planilha anterior)
    if "df_os_global" not in st.session_state:
        st.session_state["df_os_global"] = pd.DataFrame(columns=df.columns)

    # Botão para zerar/limpar a base a qualquer momento
    col_reset, _ = st.columns()
    with col_reset:
        if st.button("🗑️ Limpar Base"):
            st.session_state["df_os_global"] = pd.DataFrame(columns=df.columns)
            st.rerun()

    # --- ÁREA DE UPLOAD E LEITURA AUTOMÁTICA DE PDF ---
    with st.expander("📥 Importar Nova O.S. via PDF", expanded=True):
        arquivo_submetido = st.file_uploader("Anexar arquivo PDF da Ordem de Serviço", type=["pdf"], label_visibility="collapsed")
        
        if arquivo_submetido is not None:
            try:
                # Guarda temporariamente na memória da sessão sem renderizar tabelas poluidoras
                st.session_state["temp_pdf_dados"] = extrair_dados_os_pdf(arquivo_submetido, df.columns)
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

    # Filtros rápidos
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
