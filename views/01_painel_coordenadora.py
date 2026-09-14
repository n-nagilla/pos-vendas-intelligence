import streamlit as pd
import pandas as pd

def render(df):
    # Sincroniza com a base global do session_state
    df = st.session_state.get("df_os_global", df)

    st.subheader("🔴 Painel da Coordenadora — O.S. Atual")
    if df.empty:
        st.info("Nenhuma Ordem de Serviço registrada no momento.")
        return

    # Converte o valor Total (ex: "1.276,48") para numérico com segurança
    df_temp = df.copy()
    if "Total" in df_temp.columns:
        df_temp["Total_num"] = (
            df_temp["Total"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df_temp["Total_num"] = pd.to_numeric(df_temp["Total_num"], errors="coerce").fillna(0)
        valor_total_geral = df_temp["Total_num"].sum()
    else:
        valor_total_geral = 0

    total_os = len(df)
    ultima_os = df.iloc[-1]["Numero"] if not df.empty else "-"
    cliente_atual = df.iloc[-1]["Cliente"] if not df.empty else "-"
    modelo_atual = df.iloc[-1]["Modelo"] if not df.empty else "-"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Total de O.S.", f"{total_os}")
    c2.metric("🔢 Última O.S.", f"{ultima_os}")
    c3.metric("🚜 Modelo", f"{modelo_atual}")
    c4.metric("💵 Valor Total", f"R$ {valor_total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("### O.S. em Exibição")
    st.dataframe(df, use_container_width=True, hide_index=True)
