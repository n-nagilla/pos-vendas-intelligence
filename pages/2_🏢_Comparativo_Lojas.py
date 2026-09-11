import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.repository import obter_dados_ativos

st.set_page_config(
    page_title="Benchmarking de Unidades | Mardisa Agro",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Benchmarking & Comparativo entre Lojas")
st.caption("Análise de eficiência de custos entre Fendt Balsas, Valtra Balsas, Imperatriz e Alto Alegre")

# 1. Carregamento dos dados
df = obter_dados_ativos()

if df.empty:
    st.error("Nenhuma base de dados encontrada. Carregue uma planilha em Auditoria e Upload.")
    st.stop()

# 2. Filtro de Período Superior
col_f1, col_f2 = st.columns([3, 1])
with col_f1:
    meses_disponiveis = sorted(df["Mes_Ano"].unique().tolist())
    meses_selecionados = st.multiselect(
        "📅 Filtrar Período (Meses):",
        options=meses_disponiveis,
        default=meses_disponiveis
    )

if meses_selecionados:
    df_f = df[df["Mes_Ano"].isin(meses_selecionados)]
else:
    df_f = df.copy()

st.markdown("---")

# -------------------------------------------------------------
# 3. SCORECARD GERAL DAS 4 LOJAS (BENCHMARKING)
# -------------------------------------------------------------
st.subheader("📊 Raio-X Consolidado por Unidade")

resumo_lojas = df_f.groupby("Unidade_Completa").agg(
    Total_Gasto=("Valor_Liquido", "sum"),
    Qtd_Lancamentos=("Valor_Liquido", "count"),
    Ticket_Medio_Lancamento=("Valor_Liquido", "mean")
).reset_index()

total_rede = resumo_lojas["Total_Gasto"].sum()
resumo_lojas["Participacao_%"] = (resumo_lojas["Total_Gasto"] / total_rede * 100).round(1)
resumo_lojas = resumo_lojas.sort_values(by="Total_Gasto", ascending=False)

# Renderiza 4 colunas com cards de cada loja
cols = st.columns(len(resumo_lojas))
for idx, (_, row) in enumerate(resumo_lojas.iterrows()):
    with cols[idx]:
        st.metric(
            label=f"📍 {row['Unidade_Completa']}",
            value=f"R$ {row['Total_Gasto']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            delta=f"{row['Participacao_%']}% da Rede"
        )

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. GRÁFICOS COMPARATIVOS: MACRO-CATEGORIAS (DRE)
# -------------------------------------------------------------
col_g1, col_g2 = st.columns([1.5, 1])

with col_g1:
    st.subheader("Composição de Custos por Filial (DRE)")
    df_dre_loja = df_f.groupby(["Unidade_Completa", "Dre"])["Valor_Liquido"].sum().reset_index()
    
    fig_barras = px.bar(
        df_dre_loja,
        x="Unidade_Completa",
        y="Valor_Liquido",
        color="Dre",
        title="Despesas por Categoria (Administrativo x Pessoal x Vendas)",
        barmode="stack",
        template="plotly_white",
        labels={"Valor_Liquido": "Despesa (R$)", "Unidade_Completa": "Unidade"}
    )
    fig_barras.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.2),
        yaxis=dict(tickformat="~s")
    )
    st.plotly_chart(fig_barras, use_container_width=True)

with col_g2:
    st.subheader("Divisão do Desembolso Total")
    fig_donut = px.pie(
        resumo_lojas,
        names="Unidade_Completa",
        values="Total_Gasto",
        hole=0.45,
        title="Participação no Custo da Concessionária",
        template="plotly_white"
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------
# 5. DETALHAMENTO & DRILL-DOWN POR LOJA SELECIONADA
# -------------------------------------------------------------
st.subheader("🔍 Diagnóstico Aprofundado por Unidade")

loja_selecionada = st.selectbox(
    "Escolha uma unidade para auditoria detalhada:",
    options=resumo_lojas["Unidade_Completa"].tolist()
)

df_loja_drill = df_f[df_f["Unidade_Completa"] == loja_selecionada]

col_d1, col_d2 = st.columns([1.5, 1])

with col_d1:
    st.markdown(f"**Top 10 Contas Ofensoras em `{loja_selecionada}`**")
    top_contas_loja = df_loja_drill.groupby(["Conta", "Dre"])["Valor_Liquido"].sum().reset_index()
    top_contas_loja = top_contas_loja.sort_values(by="Valor_Liquido", ascending=False).head(10)
    
    fig_ofensores_loja = px.bar(
        top_contas_loja,
        x="Valor_Liquido",
        y="Conta",
        orientation="h",
        color="Dre",
        text_auto=".2s",
        template="plotly_white"
    )
    fig_ofensores_loja.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_ofensores_loja, use_container_width=True)

with col_d2:
    st.markdown(f"**Evolução Mensal em `{loja_selecionada}`**")
    evo_loja = df_loja_drill.groupby(["Mes_Ano", "Dre"])["Valor_Liquido"].sum().reset_index()
    fig_evo_loja = px.line(
        evo_loja,
        x="Mes_Ano",
        y="Valor_Liquido",
        color="Dre",
        markers=True,
        template="plotly_white"
    )
    fig_evo_loja.update_layout(legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig_evo_loja, use_container_width=True)

# Tabela matricial de contas da unidade selecionada
with st.expander(f"📋 Ver todas as contas detalhadas de {loja_selecionada}", expanded=False):
    tabela_loja = df_loja_drill.pivot_table(
        index=["Dre", "Conta"],
        columns="Mes_Ano",
        values="Valor_Liquido",
        aggfunc="sum",
        fill_value=0
    )
    tabela_loja["TOTAL"] = tabela_loja.sum(axis=1)
    tabela_loja = tabela_loja.sort_values(by="TOTAL", ascending=False)
    
    st.dataframe(
        tabela_loja.style.format("R$ {:,.2f}"),
        use_container_width=True
    )