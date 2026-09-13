import streamlit as st

def render(df):
    st.subheader("📦 Devolução de Peças à Fábrica")
    st.caption("Solicitações abertas | NF pendente | Peças aguardando envio | Peças enviadas | Processos aguardando encerramento")
    
    if df.empty:
        st.info("Nenhuma Ordem de Serviço na base.")
        return

    colunas = [c for c in [
        "Numero", "Cliente", "Modelo", "Codigo_Descricao_Peca", 
        "Status_Garantia", "AOL_Protocolo"
    ] if c in df.columns]

    st.dataframe(df[colunas], use_container_width=True, hide_index=True)
