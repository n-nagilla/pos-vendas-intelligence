import streamlit as st

def render(df):
    st.subheader("👥 Performance da Carteira por Consultora")
    
    if df.empty:
        st.info("Nenhum dado disponível na base de O.S.")
        return

    if "Consultor_Responsavel" in df.columns:
        resumo_cons = df.groupby("Consultor_Responsavel", dropna=False).agg(
            OS_Abertas=("Numero", "count"),
            Valor_Total=("Valor_Liquido", "sum") if "Valor_Liquido" in df.columns else ("Numero", "count")
        ).reset_index()
        st.dataframe(resumo_cons, use_container_width=True, hide_index=True)
    else:
        st.info("Coluna de consultor responsável não localizada no arquivo.")
