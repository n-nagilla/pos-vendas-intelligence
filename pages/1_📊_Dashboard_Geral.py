import streamlit as st
import pandas as pd
import plotly.express as px
from data.repository import obter_dados_ativos

st.set_page_config(
    page_title="Dashboard Geral | Pós-Vendas Mardisa",
    page_icon="📊",
    layout="wide"
)
if not st.session_state.get("usuario_autenticado", False):
    st.warning("🔒 Acesso restrito! Por favor, realize o login na tela inicial.")
    st.stop()
    
def formatar_moeda_brl(val):
    if pd.isna(val):
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# -------------------------------------------------------------
# 1. CARREGAMENTO E TRATAMENTO SEGURO DE DATAS
# -------------------------------------------------------------
df = obter_dados_ativos()

if df.empty:
    st.warning("⚠️ Nenhuma base carregada. Vá até a aba 'Auditoria e Upload' para processar a planilha.")
    st.stop()

# Garante a existência da coluna Lancamento_Mes
if "Lancamento_Mes" not in df.columns:
    if "Lancamento_Data" in df.columns:
        df["Lancamento_Data"] = pd.to_datetime(df["Lancamento_Data"], errors="coerce")
        df["Lancamento_Mes"] = df["Lancamento_Data"].dt.strftime("%m - %b").str.capitalize()
    elif "Mes_Ano" in df.columns:
        df["Lancamento_Mes"] = df["Mes_Ano"].astype(str)
    elif "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Lancamento_Mes"] = df["Data"].dt.strftime("%m - %b").str.capitalize()
    else:
        df["Lancamento_Mes"] = "Período Único"

# Garante a coluna Valor_Liquido
if "Valor_Liquido" not in df.columns:
    deb = df["Debito"] if "Debito" in df.columns else 0
    cred = df["Credito"] if "Credito" in df.columns else 0
    df["Valor_Liquido"] = deb - cred

st.title("📊 Dashboard Geral de Despesas Operacionais")
st.caption("Visão Consolidada de Custos e Despesas do Pós-Vendas Mardisa Agro")

# Barra de Filtros
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    marcas = ["TODAS"] + sorted(df["Marca"].dropna().unique().tolist()) if "Marca" in df.columns else ["TODAS"]
    marca_sel = st.selectbox("🚜 Marca", marcas)

with col_f2:
    filiais_disp = df["Empresa_NomeFantasia"].dropna().unique().tolist() if "Empresa_NomeFantasia" in df.columns else []
    if marca_sel != "TODAS" and "Marca" in df.columns:
        filiais_disp = df[df["Marca"] == marca_sel]["Empresa_NomeFantasia"].dropna().unique().tolist()
    filial_sel = st.selectbox("🏢 Filial", ["TODAS"] + sorted(filiais_disp))

with col_f3:
    meses_disp = [m for m in df["Lancamento_Mes"].dropna().unique().tolist() if pd.notna(m)]
    meses_ordenados = sorted(meses_disp)
    meses_sel = st.multiselect("📅 Meses", meses_ordenados, default=meses_ordenados)

with col_f4:
    col_dre = "Dre" if "Dre" in df.columns else ("DRE" if "DRE" in df.columns else None)
    if col_dre:
        dres = ["TODAS AS DESPESAS"] + sorted(df[col_dre].dropna().unique().tolist())
    else:
        dres = ["TODAS AS DESPESAS"]
    dre_sel = st.selectbox("📁 Macro Categoria (DRE)", dres)

# Aplicação dos Filtros
df_filtrado = df.copy()

if marca_sel != "TODAS" and "Marca" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Marca"] == marca_sel]

if filial_sel != "TODAS" and "Empresa_NomeFantasia" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Empresa_NomeFantasia"] == filial_sel]

if meses_sel:
    df_filtrado = df_filtrado[df_filtrado["Lancamento_Mes"].isin(meses_sel)]

if dre_sel != "TODAS AS DESPESAS" and col_dre:
    df_filtrado = df_filtrado[df_filtrado[col_dre] == dre_sel]

if df_filtrado.empty:
    st.info("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

# -------------------------------------------------------------
# 2. CARDS DE KPI EXECUTIVOS
# -------------------------------------------------------------
total_despesas = df_filtrado["Valor_Liquido"].sum()

if col_dre:
    dp_total = df_filtrado[df_filtrado[col_dre].str.contains("Pessoal", case=False, na=False)]["Valor_Liquido"].sum()
    da_total = df_filtrado[df_filtrado[col_dre].str.contains("Administrativ", case=False, na=False)]["Valor_Liquido"].sum()
    dv_total = df_filtrado[df_filtrado[col_dre].str.contains("Venda", case=False, na=False)]["Valor_Liquido"].sum()
else:
    dp_total, da_total, dv_total = 0, 0, 0

pct_dp = (dp_total / total_despesas * 100) if total_despesas > 0 else 0
pct_da = (da_total / total_despesas * 100) if total_despesas > 0 else 0
pct_dv = (dv_total / total_despesas * 100) if total_despesas > 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("💰 Total de Despesas", formatar_moeda_brl(total_despesas))
kpi2.metric("👥 Despesas com Pessoal", formatar_moeda_brl(dp_total), f"{pct_dp:.1f}% do total")
kpi3.metric("🏛️ Administrativo", formatar_moeda_brl(da_total), f"{pct_da:.1f}% do total")
kpi4.metric("🚛 Vendas & Campo", formatar_moeda_brl(dv_total), f"{pct_dv:.1f}% do total")

st.divider()

# -------------------------------------------------------------
# 3. GRÁFICOS EXECUTIVOS PRINCIPAIS
# -------------------------------------------------------------
col_graf1, col_graf2 = st.columns([1.4, 1])

with col_graf1:
    st.subheader("📈 Evolução Mensal")
    agrupador = [c for c in ["Lancamento_Mes", col_dre] if c and c in df_filtrado.columns]
    if agrupador:
        df_tempo = df_filtrado.groupby(agrupador)["Valor_Liquido"].sum().reset_index()
        fig_tempo = px.line(
            df_tempo,
            x="Lancamento_Mes",
            y="Valor_Liquido",
            color=col_dre if col_dre in df_tempo.columns else None,
            markers=True,
            template="plotly_dark"
        )
        fig_tempo.update_layout(xaxis_title="", yaxis_title="Total (R$)", legend_title="", margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_tempo, use_container_width=True)

with col_graf2:
    st.subheader("🏢 Distribuição por Filial")
    if "Empresa_NomeFantasia" in df_filtrado.columns:
        df_loja = df_filtrado.groupby("Empresa_NomeFantasia")["Valor_Liquido"].sum().reset_index()
        fig_pizza = px.pie(
            df_loja,
            names="Empresa_NomeFantasia",
            values="Valor_Liquido",
            hole=0.45,
            template="plotly_dark"
        )
        fig_pizza.update_layout(legend_title="", margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pizza, use_container_width=True)

# -------------------------------------------------------------
# 4. RANKING DOS MAIORES OFENSORES
# -------------------------------------------------------------
st.subheader("⚠️ Top 10 Maiores Contas de Despesa do Período")

col_conta = "Conta" if "Conta" in df_filtrado.columns else None
if col_conta:
    cols_group = [c for c in [col_dre, col_conta] if c and c in df_filtrado.columns]
    top_contas = (
        df_filtrado.groupby(cols_group)["Valor_Liquido"]
        .sum()
        .reset_index()
        .sort_values(by="Valor_Liquido", ascending=False)
        .head(10)
    )

    top_contas["Participação (%)"] = (top_contas["Valor_Liquido"] / total_despesas * 100).map("{:.2f}%".format)
    top_contas["Total Acumulado (R$)"] = top_contas["Valor_Liquido"].apply(formatar_moeda_brl)

    st.dataframe(
        top_contas[[c for c in [col_dre, col_conta, "Total Acumulado (R$)", "Participação (%)"] if c]].rename(
            columns={col_dre: "Categoria DRE", col_conta: "Descrição da Conta"}
        ),
        use_container_width=True,
        hide_index=True
    )
