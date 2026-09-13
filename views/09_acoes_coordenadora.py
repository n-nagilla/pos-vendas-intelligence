import streamlit as st

def render(df):
    st.subheader("🔴 10 Ações Prioritárias da Coordenadora Hoje")
    
    if df.empty:
        st.info("Nenhuma ação pendente identificada.")
        return

    df_prioridades = df[
        (df.get("Gargalo_Atual", "") != "") | 
        (df.get("Semáforo_Prazo", "").isin(["🔴 Crítico (>60d)", "🟡 Atenção"]))
    ] if "Gargalo_Atual" in df.columns else df

    colunas = [c for c in [
        "Numero", "Unidade", "Cliente", "Modelo", "Gargalo_Atual", 
        "Proxima_Acao", "Responsavel", "Prazo_Acao"
    ] if c in df.columns]

    st.dataframe(df_prioridades[colunas].head(10) if not df_prioridades.empty else df.head(10), use_container_width=True, hide_index=True)
