import streamlit as st
import pandas as pd

def fmt_brl(v):
    if v is None or pd.isna(v) or not isinstance(v, (int, float)):
        return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def render(df):
    st.subheader("💰 Controle Fábrica — Dinheiro Parado")
    
    if df.empty:
        st.info("Nenhum dado financeiro disponível.")
        return

    v_sub = df["Valor_Solicitado"].sum() if "Valor_Solicitado" in df.columns else 0
    v_apr = df["Valor_Aprovado"].sum() if "Valor_Aprovado" in df.columns else 0
    v_fat = df["Valor_Faturado"].sum() if "Valor_Faturado" in df.columns else 0
    aguard_fat = max(0, v_apr - v_fat)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Valor Submetido", fmt_brl(v_sub))
    c2.metric("Valor Aprovado", fmt_brl(v_apr))
    c3.metric("Aguardando Faturamento", fmt_brl(aguard_fat))
    c4.metric("Valor Faturado", fmt_brl(v_fat))

    st.markdown("### Processos por Status na Fábrica")
    colunas_fabrica = [c for c in [
        "Numero", "Cliente", "Modelo", "Status_Garantia", 
        "Valor_Solicitado", "Valor_Aprovado", "Valor_Faturado", "AOL_Protocolo"
    ] if c in df.columns]
    
    st.dataframe(df[colunas_fabrica], use_container_width=True, hide_index=True)
