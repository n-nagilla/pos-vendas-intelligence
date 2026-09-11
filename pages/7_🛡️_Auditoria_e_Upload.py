import streamlit as st
import pandas as pd
from data.ingestion import ERPDataPipeline

st.set_page_config(page_title="Compilador ERP - Mardisa Agro", layout="wide")

st.title("📂 Compilador de Despesas do ERP Mardisa Agro")
st.markdown("Insira o arquivo exportado da loja (`.xlsx`) para processar e consolidar as 4 unidades.")

arquivo_enviado = st.file_uploader(
    "Arraste a planilha de despesas (DA DP DV)", 
    type=["xlsx", "xls"],
    help="Selecione o arquivo extraído do NBS/ERP"
)

if arquivo_enviado is not None:
    pipeline = ERPDataPipeline()
    with st.spinner("Compilando e auditando lançamentos..."):
        df_processado = pipeline.processar_arquivo(arquivo_enviado)
        # Salva o DataFrame na sessão para todas as outras páginas consumirem
        st.session_state["dados_despesas"] = df_processado

    st.success(f"Arquivo processado com sucesso! {len(df_processado):,} lançamentos identificados.")

    # Resumo Gerencial Imediato
    st.subheader("📌 Resumo Consolidado por Unidade e Macro-Categoria")
    
    tabela_resumo = df_processado.pivot_table(
        index="Unidade_Completa",
        columns="Dre",
        values="Valor_Liquido",
        aggfunc="sum",
        margins=True,
        margins_name="TOTAL GERAL"
    )

    # Exibe formatado em Real (R$)
    st.dataframe(
        tabela_resumo.style.format("R$ {:,.2f}"),
        use_container_width=True
    )