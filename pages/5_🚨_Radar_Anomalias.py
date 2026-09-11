import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from data.repository import obter_dados_ativos

st.set_page_config(
    page_title="Radar de Anomalias | Mardisa Agro",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 Radar de Anomalias & Desvios Estatísticos")
st.caption("Identificação automática de contas operando fora do padrão histórico de desembolso.")

# 1. Carregamento dos dados
df = obter_dados_ativos()

if df.empty:
    st.error("Nenhuma base de dados encontrada. Carregue uma planilha em Auditoria e Upload.")
    st.stop()

# 2. Filtros Superiores
c_f1, c_f2 = st.columns([2, 2])
with c_f1:
    unidades_disp = ["TODAS"] + sorted(df["Unidade_Completa"].unique().tolist())
    unidade_sel = st.selectbox("🏢 Filtrar por Unidade:", unidades_disp)

with c_f2:
    dres_disp = ["TODAS"] + sorted(df["Dre"].unique().tolist())
    dre_sel = st.selectbox("📁 Filtrar por Categoria DRE:", dres_disp)

df_base = df.copy()
if unidade_sel != "TODAS":
    df_base = df_base[df_base["Unidade_Completa"] == unidade_sel]
if dre_sel != "TODAS":
    df_base = df_base[df_base["Dre"] == dre_sel]

st.markdown("---")

# -------------------------------------------------------------
# 3. MOTOR DE DETECÇÃO DE DESVIOS (HISTÓRICO VS. ÚLTIMO MÊS)
# -------------------------------------------------------------
meses_ordenados = sorted(df_base["Mes_Ano"].unique().tolist())

if len(meses_ordenados) < 2:
    st.info("São necessários dados de pelo menos dois meses para calcular médias históricas e desvios.")
    st.stop()

ultimo_mes = meses_ordenados[-1]
meses_historicos = meses_ordenados[:-1]

# Matriz agregada: Conta x Mes_Ano
pivot_contas = df_base.pivot_table(
    index=["Dre", "Conta"],
    columns="Mes_Ano",
    values="Valor_Liquido",
    aggfunc="sum",
    fill_value=0
)

# Cálculos estatísticos
pivot_contas["Media_Historica"] = pivot_contas[meses_historicos].mean(axis=1)
pivot_contas["Desvio_Padrao"] = pivot_contas[meses_historicos].std(axis=1).fillna(0)
pivot_contas["Ultimo_Mes_Valor"] = pivot_contas[ultimo_mes]

pivot_contas["Delta_Absoluto"] = pivot_contas["Ultimo_Mes_Valor"] - pivot_contas["Media_Historica"]
pivot_contas["Delta_%"] = np.where(
    pivot_contas["Media_Historica"] > 0,
    (pivot_contas["Delta_Absoluto"] / pivot_contas["Media_Historica"]) * 100,
    np.where(pivot_contas["Ultimo_Mes_Valor"] > 0, 100.0, 0.0)
)

# Filtra contas com relevância financeira (ignora contas residuais < R$ 500)
anomalias = pivot_contas[
    (pivot_contas["Ultimo_Mes_Valor"] >= 500) | (pivot_contas["Media_Historica"] >= 500)
].reset_index()

# Classificação Semafórica
def classificar_status(row):
    if row["Delta_%"] >= 50 and row["Delta_Absoluto"] >= 2000:
        return "🔴 Crítico (Alta Severa)"
    elif row["Delta_%"] >= 20 and row["Delta_Absoluto"] >= 1000:
        return "🟡 Atenção (Acima da Média)"
    elif row["Delta_%"] <= -20 and row["Delta_Absoluto"] <= -1000:
        return "🟢 Favorável (Redução)"
    return "⚪ Em Linha com o Histórico"

anomalias["Status"] = anomalias.apply(classificar_status, axis=1)

# -------------------------------------------------------------
# 4. CARDS EXECUTIVOS DO RADAR
# -------------------------------------------------------------
qtd_criticos = (anomalias["Status"] == "🔴 Crítico (Alta Severa)").sum()
qtd_atencao = (anomalias["Status"] == "🟡 Atenção (Acima da Média)").sum()
qtd_reducao = (anomalias["Status"] == "🟢 Favorável (Redução)").sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Mês sob Análise", ultimo_mes)
k2.metric("Alertas Críticos", f"{qtd_criticos} contas", delta="Necessita Auditoria", delta_color="inverse")
k3.metric("Sob Atenção", f"{qtd_atencao} contas", delta="Variação moderada", delta_color="off")
k4.metric("Com Redução", f"{qtd_reducao} contas", delta="Evolução favorável")

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. GRÁFICO DE DISPERSÃO: IMPACTO FINANCEIRO X DESVIO %
# -------------------------------------------------------------
st.subheader("🎯 Matriz de Severidade (Impacto Financeiro x Desvio Percentual)")
st.caption("O quadrante superior direito concentra as contas mais críticas: alto valor absoluto somado a forte alta percentual.")

color_map = {
    "🔴 Crítico (Alta Severa)": "#dc3545",
    "🟡 Atenção (Acima da Média)": "#ffc107",
    "🟢 Favorável (Redução)": "#28a745",
    "⚪ Em Linha com o Histórico": "#6c757d"
}

fig_disp = px.scatter(
    anomalias,
    x="Delta_%",
    y="Delta_Absoluto",
    color="Status",
    color_discrete_map=color_map,
    size="Ultimo_Mes_Valor",
    hover_data=["Conta", "Dre", "Media_Historica", "Ultimo_Mes_Valor"],
    title=f"Desvio Percentual vs. Desvio em Reais (Mês: {ultimo_mes})",
    template="plotly_white",
    labels={
        "Delta_%": "Variação sobre a Média Histórica (%)",
        "Delta_Absoluto": "Diferença em R$ (Realizado - Média)",
        "Ultimo_Mes_Valor": "Valor Atual (R$)"
    }
)
fig_disp.add_vline(x=0, line_dash="dash", line_color="gray")
fig_disp.add_hline(y=0, line_dash="dash", line_color="gray")
fig_disp.update_layout(yaxis=dict(tickformat="~s"))
st.plotly_chart(fig_disp, use_container_width=True)

# -------------------------------------------------------------
# 6. TABELA AUDITÁVEL DOS ALERTAS
# -------------------------------------------------------------
st.subheader("📋 Tabela Gerencial de Contas Fora do Padrão")

# Ordena por gravidade do desvio absoluto
tabela_exibir = anomalias[anomalias["Status"] != "⚪ Em Linha com o Histórico"].sort_values(
    by="Delta_Absoluto", ascending=False
)

colunas_view = [
    "Status", "Dre", "Conta", "Media_Historica", 
    "Ultimo_Mes_Valor", "Delta_Absoluto", "Delta_%"
]

# Funções auxiliares para formatação segura em BRL
def fmt_moeda(val):
    if pd.isna(val):
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_diferenca(val):
    if pd.isna(val):
        return "R$ 0,00"
    sinal = "+" if val > 0 else ""
    formatado = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sinal}R$ {formatado}"

st.dataframe(
    tabela_exibir[colunas_view].rename(columns={
        "Dre": "Categoria DRE",
        "Media_Historica": "Média Histórica (R$)",
        "Ultimo_Mes_Valor": f"Realizado em {ultimo_mes} (R$)",
        "Delta_Absoluto": "Diferença (R$)",
        "Delta_%": "Desvio (%)"
    }).style.format({
        "Média Histórica (R$)": fmt_moeda,
        f"Realizado em {ultimo_mes} (R$)": fmt_moeda,
        "Diferença (R$)": fmt_diferenca,
        "Desvio (%)": lambda x: f"{x:+.1f}%" if pd.notna(x) else "0.0%"
    }),
    use_container_width=True,
    height=400
)