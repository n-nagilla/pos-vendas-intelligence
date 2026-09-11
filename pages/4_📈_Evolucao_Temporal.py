import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.repository import obter_dados_ativos

st.set_page_config(
    page_title="Evolução Temporal & Tendência | Mardisa Agro",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Análise de Tendência & Evolução Histórica")
st.caption("Acompanhe o comportamento das despesas ao longo dos meses, identifique picos e tendências de alta.")

# 1. Carregamento dos dados
df = obter_dados_ativos()

if df.empty:
    st.error("Nenhuma base de dados encontrada. Carregue uma planilha em Auditoria e Upload.")
    st.stop()

# 2. Filtros Dinâmicos Superiores
col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 2])

with col_f1:
    unidades_disp = ["TODAS"] + sorted(df["Unidade_Completa"].unique().tolist())
    unidade_sel = st.selectbox("🏢 Unidade:", unidades_disp)

with col_f2:
    dres_disp = ["TODAS"] + sorted(df["Dre"].unique().tolist())
    dre_sel = st.selectbox("📁 Categoria DRE:", dres_disp)

# Aplicação dos filtros base
df_base = df.copy()
if unidade_sel != "TODAS":
    df_base = df_base[df_base["Unidade_Completa"] == unidade_sel]
if dre_sel != "TODAS":
    df_base = df_base[df_base["Dre"] == dre_sel]

with col_f3:
    contas_disp = sorted(df_base["Conta"].unique().tolist())
    top_5_contas = (
        df_base.groupby("Conta")["Valor_Liquido"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )
    contas_sel = st.multiselect(
        "🏷️ Selecione as Contas para Comparar a Curva:",
        options=contas_disp,
        default=top_5_contas
    )

st.markdown("---")

# -------------------------------------------------------------
# SEÇÃO 1: CURVA TEMPORAL MULTI-CONTAS COM LINHA DE TENDÊNCIA
# -------------------------------------------------------------
st.subheader("📊 Comparativo de Trajetória Mensal")

if contas_sel:
    df_curva = df_base[df_base["Conta"].isin(contas_sel)]
    df_tempo = (
        df_curva.groupby(["Mes_Ano", "Conta"], as_index=False)["Valor_Liquido"]
        .sum()
        .sort_values(by="Mes_Ano")
    )

    fig_tempo = px.line(
        df_tempo,
        x="Mes_Ano",
        y="Valor_Liquido",
        color="Conta",
        markers=True,
        title="Evolução Mensal das Contas Selecionadas (Identificação de Picos e Inflexões)",
        template="plotly_white",
        labels={"Valor_Liquido": "Despesa (R$)", "Mes_Ano": "Mês"}
    )
    fig_tempo.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.25),
        yaxis=dict(tickformat="~s")
    )
    st.plotly_chart(fig_tempo, use_container_width=True)
else:
    st.warning("Selecione pelo menos uma conta no filtro acima para gerar o gráfico.")

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# SEÇÃO 2: RAIO-X DE CONTA INDIVIDUAL & MÉDIA MÓVEL (3M)
# -------------------------------------------------------------
st.subheader("🔬 Raio-X Individual de Conta")
st.caption("Selecione uma conta específica para auditar seu comportamento contra a média trimestral.")

col_rx1, col_rx2 = st.columns([1, 2])

with col_rx1:
    conta_foco = st.selectbox("Escolha a Conta em Destaque:", options=contas_disp, index=0)
    df_foco = df_base[df_base["Conta"] == conta_foco]
    serie_mensal = df_foco.groupby("Mes_Ano")["Valor_Liquido"].sum().reset_index().sort_values("Mes_Ano")
    
    # Adiciona média móvel de 3 meses se houver dados suficientes
    serie_mensal["Media_Movel_3M"] = serie_mensal["Valor_Liquido"].rolling(window=3, min_periods=1).mean()

    total_conta = df_foco["Valor_Liquido"].sum()
    media_mensal_conta = serie_mensal["Valor_Liquido"].mean()
    max_mes = serie_mensal.loc[serie_mensal["Valor_Liquido"].idxmax()]

    st.metric("Total Acumulado", f"R$ {total_conta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.metric("Média Mensal", f"R$ {media_mensal_conta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.metric("Mês com Maior Gasto", f"{max_mes['Mes_Ano']}", delta=f"R$ {max_mes['Valor_Liquido']:,.2f}".replace(",", "."))

with col_rx2:
    fig_foco = go.Figure()
    
    # Barras de valor realizado no mês
    fig_foco.add_trace(go.Bar(
        x=serie_mensal["Mes_Ano"],
        y=serie_mensal["Valor_Liquido"],
        name="Realizado no Mês",
        marker_color="#0d6efd"
    ))
    
    # Linha de Média Móvel (3M)
    fig_foco.add_trace(go.Scatter(
        x=serie_mensal["Mes_Ano"],
        y=serie_mensal["Media_Movel_3M"],
        name="Média Móvel (3 Meses)",
        mode="lines+markers",
        line=dict(color="#fd7e14", width=3, dash="dash")
    ))

    fig_foco.update_layout(
        title=f"Histórico vs. Média Móvel: {conta_foco}",
        template="plotly_white",
        yaxis=dict(title="Valor (R$)", tickformat="~s"),
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_foco, use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------
# SEÇÃO 3: TABELA DE EVOLUÇÃO PERCENTUAL MÊS A MÊS (MoM)
# -------------------------------------------------------------
with st.expander("📋 Ver Tabela de Variação MoM (%) de Todas as Contas", expanded=False):
    tabela_mom = df_base.pivot_table(
        index="Conta",
        columns="Mes_Ano",
        values="Valor_Liquido",
        aggfunc="sum",
        fill_value=0
    )
    
    # Calcula variação MoM
    pct_change = tabela_mom.pct_change(axis=1) * 100
    
    st.dataframe(
        tabela_mom.style.format("R$ {:,.2f}"),
        use_container_width=True
    )
