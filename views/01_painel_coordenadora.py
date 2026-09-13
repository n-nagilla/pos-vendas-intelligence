import streamlit as st

def render(df):
    st.subheader("🔴 Atenção da Coordenadora Hoje")
    if df.empty:
        st.info("Sem dados disponíveis.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    criticas = len(df[df.get("Semáforo_Prazo", "") == "🔴 Crítico (>60d)"])
    atencao = len(df[df.get("Semáforo_Prazo", "") == "🟡 Atenção"])
    bo_pecas = len(df[df.get("Peca_BO", "") == "Sim"])
    em_fabrica = len(df[df.get("Status_Garantia", "") == "Em análise fábrica"])
    saldo_parado = df["Valor_Liquido"].sum() if "Valor_Liquido" in df else 0

    c1.metric("🔴 O.S. Ultrapassando Prazo", f"{criticas} O.S.")
    c2.metric("🟡 Alerta (30 a 50d)", f"{atencao} O.S.")
    c3.metric("📦 Peças em B.O.", f"{bo_pecas} O.S.")
    c4.metric("🏭 Em Análise Fábrica", f"{em_fabrica} O.S.")
    c5.metric("💵 Saldo Parado", f"R$ {saldo_parado:,.2f}")
