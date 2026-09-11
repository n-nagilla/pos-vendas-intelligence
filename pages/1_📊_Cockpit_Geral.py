import streamlit as st
import pandas as pd
import plotly.express as px
from data.repository import obter_dados_ativos
from utils.formatting import format_currency_brl

st.set_page_config(
    page_title="Cockpit Geral | Pós-Vendas Mardisa",
    page_icon="📊",
    layout="wide"
)

# -------------------------------------------------------------
# 1. CARREGAMENTO E FILTROS GLOBAIS
# -------------------------------------------------------------
df = obter_dados_ativos()

if df.empty:
    st.warning("⚠️ Nenhuma base carregada. Vá até a aba 'Auditoria e Upload' para processar a planilha.")
    st.stop()

st.title("📊 Cockpit Geral de Despesas Operacionais")
st.caption("Visão Consolidada de Custos e Despesas do Pós-Vendas Mardisa Agro")

# Barra de Filtros
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    marcas = ["TODAS"] + sorted(df["Marca"].dropna().unique().tolist()) if "Marca" in df.columns else ["TODAS"]
    marca_sel = st.selectbox("🚜 Marca", marcas)

with col_f2:
    filiais_disp = df["Empresa_NomeFantasia"].dropna().unique().tolist()
    if marca_sel != "TODAS" and "Marca" in df.columns:
        filiais_disp = df[df["Marca"] == marca_sel]["Empresa_NomeFantasia"].dropna().unique().tolist()
    filial_sel = st.selectbox("🏢 Filial", ["TODAS"] + sorted(filiais_disp))

with col_f3:
    meses_ordenados = sorted(df["Lancamento_Mes"].dropna().unique().tolist())
    meses_sel = st.multiselect("📅 Meses", meses_ordenados, default=meses_ordenados)

with col_f4:
    dres = ["TODAS AS DESPESAS"] + sorted(df["Dre"].dropna().unique().tolist())
    dre_sel = st.selectbox("📁 Macro Categoria (DRE)", dres)

# Aplicação dos Filtros
df_filtrado = df.copy()

if marca_sel != "TODAS" and "Marca" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Marca"] == marca_sel]

if filial_sel != "TODAS":
    df_filtrado = df_filtrado[df_filtrado["Empresa_NomeFantasia"] == filial_sel]

if meses_sel:
    df_filtrado = df_filtrado[df_filtrado["Lancamento_Mes"].isin(meses_sel)]

if dre_sel != "TODAS AS DESPESAS":
    df_filtrado = df_filtrado[df_filtrado["Dre"] == dre_sel]

if df_filtrado.empty:
    st.info("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

# -------------------------------------------------------------
# 2. CARDS DE KPI EXECUTIVOS
# -------------------------------------------------------------
total_despesas = df_filtrado["Valor_Liquido"].sum()

# Segmentação por Macro DRE
dp_total = df_filtrado[df_filtrado["Dre"].str.contains("Pessoal", case=False, na=False)]["Valor_Liquido"].sum()
da_total = df_filtrado[df_filtrado["Dre"].str.contains("Administrativ", case=False, na=False)]["Valor_Liquido"].sum()
dv_total = df_filtrado[df_filtrado["Dre"].str.contains("Venda", case=False, na=False)]["Valor_Liquido"].sum()

pct_dp = (dp_total / total_despesas * 100) if total_despesas > 0 else 0
pct_da = (da_total / total_despesas * 100) if total_despesas > 0 else 0
pct_dv = (dv_total / total_despesas * 100) if total_despesas > 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("💰 Total de Despesas", format_currency_brl(total_despesas))
kpi2.metric("👥 Despesas com Pessoal", format_currency_brl(dp_total), f"{pct_dp:.1f}% do total")
kpi3.metric("🏛️ Administrativo", format_currency_brl(da_total), f"{pct_da:.1f}% do total")
kpi4.metric("🚛 Vendas & Campo", format_currency_brl(dv_total), f"{pct_dv:.1f}% do total")

st.divider()

# -------------------------------------------------------------
# 3. GRÁFICOS EXECUTIVOS PRINCIPAIS
# -------------------------------------------------------------
col_graf1, col_graf2 = st.columns([1.4, 1])

with col_graf1:
    st.subheader("📈 Evolução Mensal por Categoria DRE")
    df_tempo = df_filtrado.groupby(["Lancamento_Mes", "Dre"])["Valor_Liquido"].sum().reset_index()
    
    fig_tempo = px.line(
        df_tempo,
        x="Lancamento_Mes",
        y="Valor_Liquido",
        color="Dre",
        markers=True,
        template="plotly_dark"
    )
    fig_tempo.update_layout(
        xaxis_title="",
        yaxis_title="Total (R$)",
        legend_title="",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_tempo, use_container_width=True)

with col_graf2:
    st.subheader("🏢 Distribuição por Filial")
    df_loja = df_filtrado.groupby("Empresa_NomeFantasia")["Valor_Liquido"].sum().reset_index()
    
    fig_pizza = px.pie(
        df_loja,
        names="Empresa_NomeFantasia",
        values="Valor_Liquido",
        hole=0.45,
        template="plotly_dark"
    )
    fig_pizza.update_layout(
        legend_title="",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_pizza, use_container_width=True)

# -------------------------------------------------------------
# 4. RANKING DOS MAIORES OFENSORES
# -------------------------------------------------------------
st.subheader("⚠️ Top 10 Maiores Contas de Despesa do Período")

top_contas = (
    df_filtrado.groupby(["Dre", "Conta"])["Valor_Liquido"]
    .sum()
    .reset_index()
    .sort_values(by="Valor_Liquido", ascending=False)
    .head(10)
)

top_contas["Participação (%)"] = (top_contas["Valor_Liquido"] / total_despesas * 100).map("{:.2f}%".format)
top_contas["Total Acumulado (R$)"] = top_contas["Valor_Liquido"].apply(format_currency_brl)

st.dataframe(
    top_contas[["Dre", "Conta", "Total Acumulado (R$)", "Participação (%)"]].rename(
        columns={"Dre": "Categoria DRE", "Conta": "Descrição da Conta"}
    ),
    use_container_width=True,
    hide_index=True
)
