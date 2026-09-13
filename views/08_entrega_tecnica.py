import streamlit as st

def render(df):
    st.subheader("📑 Entrega Técnica e Registro de Garantia")
    st.caption("Apresentação do funcionamento, explicação da garantia e conclusão da documentação eletrônica.")
    
    if df.empty:
        st.info("Nenhum registro de entrega técnica encontrado.")
        return

    colunas = [c for c in [
        "Numero", "Cliente", "Modelo", "Serie", "Emissao", "Consultor_Responsavel"
    ] if c in df.columns]

    st.dataframe(df[colunas], use_container_width=True, hide_index=True)
