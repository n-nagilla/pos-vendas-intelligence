import streamlit as st

def render(df):
    st.subheader("🚜 Campanhas de Campo (Fendt & Valtra)")
    st.caption("Campanhas abertas | Campanhas concluídas | Campanhas atrasadas")
    
    if df.empty:
        st.info("Nenhum dado de campanhas de campo disponível.")
        return

    colunas = [c for c in [
        "Numero", "Cliente", "Modelo", "Serie", "Servico", "Status_Garantia"
    ] if c in df.columns]

    st.dataframe(df[colunas], use_container_width=True, hide_index=True)
