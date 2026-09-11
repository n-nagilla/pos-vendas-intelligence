import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.repository import obter_dados_ativos

st.set_page_config(
    page_title="Causas & Ofensores | Mardisa Agro",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Diagnóstico de Causas & Contas Ofensoras")
st.caption("Identifique os principais responsáveis por variações de custo e concentração de desembolso.")

# 1. Carregamento dos dados
df = obter_dados_ativos()

if df.empty:
    st.error("Nenhuma base de dados encontrada. Carregue uma planilha em Auditoria e Upload.")
    st.stop()

# 2. Filtros Superiores
c_f1, c_f2 = st.columns([2, 2])
with c_f1:
    unidades_disp = ["TODAS"] + sorted(df["Unidade_Completa"].unique().tolist())
    unidade_sel = st.selectbox("🏢 Filtrar Unidade:", unidades_disp)
with c_f2:
    dres_disp = ["TODAS"] + sorted(df["Dre"].unique().tolist())
    dre_sel = st.selectbox("📁 Categoria DRE:", dres_disp)

df_base = df.copy()
if unidade_sel != "TODAS":
    df_base = df_base[df_base["Unidade_Completa"] == unidade_sel]
if dre_sel != "TODAS":
    df_base = df_base[df_base["Dre"] == dre_sel]

st.markdown("---")

# -------------------------------------------------------------
# SEÇÃO 1: "POR QUE AUMENTOU?" (VARIAÇÃO MÊS A MÊS - MoM)
# -------------------------------------------------------------
st.subheader("⚡ O que Provocou a Variação? (Análise de Causas)")
st.caption("Compare dois meses consecutivos para descobrir exatamente quais contas geraram aumento ou economia.")

meses_lista = sorted(df_base["Mes_Ano"].unique().tolist())

if len(meses_lista) >= 2:
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        mes_anterior = st.selectbox("Mês de Referência (Base):", meses_lista, index=len(meses_lista)-2)
    with c_m2:
        mes_atual = st.selectbox("Mês de Comparação (Atual):", meses_lista, index=len(meses_lista)-1)

    # Agrupa valores por conta em cada mês
    df_ant = df_base[df_base["Mes_Ano"] == mes_anterior].groupby(["Dre", "Conta"])["Valor_Liquido"].sum().reset_index()
    df_atu = df_base[df_base["Mes_Ano"] == mes_atual].groupby(["Dre", "Conta"])["Valor_Liquido"].sum().reset_index()

    df_comp = pd.merge(df_ant, df_atu, on=["Dre", "Conta"], how="outer", suffixes=("_Ant", "_Atu")).fillna(0)
    df_comp["Variacao_R$"] = df_comp["Valor_Liquido_Atu"] - df_comp["Valor_Liquido_Ant"]
    df_comp["Variacao_%"] = df_comp.apply(
        lambda r: (r["Variacao_R$"] / r["Valor_Liquido_Ant"] * 100) if r["Valor_Liquido_Ant"] > 0 else 100.0, axis=1
    )

    total_ant = df_comp["Valor_Liquido_Ant"].sum()
    total_atu = df_comp["Valor_Liquido_Atu"].sum()
    dif_total = total_atu - total_ant
    pct_total = (dif_total / total_ant * 100) if total_ant > 0 else 0

    # Cards comparativos do período
    k1, k2, k3 = st.columns(3)
    k1.metric(f"Total em {mes_anterior}", f"R$ {total_ant:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k2.metric(f"Total em {mes_atual}", f"R$ {total_atu:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k3.metric(
        "Variação Líquida",
        f"R$ {dif_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        delta=f"{pct_total:+.1f}%",
        delta_color="inverse"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col_subiu, col_desceu = st.columns(2)
    
    with col_subiu:
        st.markdown(f"**🔺 Maiores Aumentos ({mes_atual} vs {mes_anterior})**")
        df_subiu = df_comp[df_comp["Variacao_R$"] > 0].sort_values(by="Variacao_R$", ascending=False).head(5)
        if not df_subiu.empty:
            fig_subiu = px.bar(
                df_subiu,
                x="Variacao_R$",
                y="Conta",
                orientation="h",
                color="Variacao_R$",
                color_continuous_scale="Reds",
                text_auto=".2s",
                template="plotly_white"
            )
            fig_subiu.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig_subiu, use_container_width=True)
        else:
            st.info("Nenhuma conta apresentou aumento no período selecionado.")

    with col_desceu:
        st.markdown(f"**🔻 Maiores Reduções ({mes_atual} vs {mes_anterior})**")
        df_desceu = df_comp[df_comp["Variacao_R$"] < 0].sort_values(by="Variacao_R$", ascending=True).head(5)
        if not df_desceu.empty:
            df_desceu["Reducao_Abs"] = df_desceu["Variacao_R$"].abs()
            fig_desceu = px.bar(
                df_desceu,
                x="Reducao_Abs",
                y="Conta",
                orientation="h",
                color="Reducao_Abs",
                color_continuous_scale="Greens",
                text_auto=".2s",
                template="plotly_white"
            )
            fig_desceu.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig_desceu, use_container_width=True)
        else:
            st.info("Nenhuma conta apresentou redução no período selecionado.")

else:
    st.info("Necessário pelo menos dois meses na base para calcular variações.")

st.markdown("---")

# -------------------------------------------------------------
# SEÇÃO 2: CURVA DE PARETO (PRINCÍPIO 80/20)
# -------------------------------------------------------------
st.subheader("📊 Curva de Pareto (80/20 das Despesas)")
st.caption("Descubra a minoria de contas responsáveis pela ampla maioria dos gastos.")

pareto_df = df_base.groupby("Conta")["Valor_Liquido"].sum().reset_index()
pareto_df = pareto_df.sort_values(by="Valor_Liquido", ascending=False).reset_index(drop=True)
pareto_df["Acumulado"] = pareto_df["Valor_Liquido"].cumsum()
pareto_df["Acumulado_%"] = (pareto_df["Acumulado"] / pareto_df["Valor_Liquido"].sum()) * 100

# Top 15 contas para melhor legibilidade
pareto_view = pareto_df.head(15)

fig_pareto = go.Figure()

# Barras: Valor Individual
fig_pareto.add_trace(go.Bar(
    x=pareto_view["Conta"],
    y=pareto_view["Valor_Liquido"],
    name="Valor da Despesa (R$)",
    marker_color="#1f77b4"
))

# Linha: Percentual Acumulado
fig_pareto.add_trace(go.Scatter(
    x=pareto_view["Conta"],
    y=pareto_view["Acumulado_%"],
    name="% Acumulado",
    yaxis="y2",
    mode="lines+markers",
    line=dict(color="#d62728", width=2)
))

# Linha de corte nos 80%
fig_pareto.add_shape(
    type="line",
    x0=-0.5, x1=len(pareto_view)-0.5,
    y0=80, y1=80,
    yref="y2",
    line=dict(color="orange", width=2, dash="dash")
)

fig_pareto.update_layout(
    title="Top 15 Contas e Impacto Acumulado no Orçamento",
    xaxis=dict(tickangle=-45),
    yaxis=dict(title="Valor Total (R$)", tickformat="~s"),
    yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 105]),
    template="plotly_white",
    legend=dict(orientation="h", y=1.15)
)

st.plotly_chart(fig_pareto, use_container_width=True)

# Tabela detalhada da Curva de Pareto
with st.expander("📋 Ver Tabela Completa de Pareto", expanded=False):
    st.dataframe(
        pareto_df.style.format({
            "Valor_Liquido": "R$ {:,.2f}",
            "Acumulado": "R$ {:,.2f}",
            "Acumulado_%": "{:.1f}%"
        }),
        use_container_width=True
    )