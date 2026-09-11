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
st.caption("Identificação automática de contas operando fora do padrão histórico de desembolso por unidade.")

# 1. Carregamento dos dados
df = obter_dados_ativos()

if df.empty:
    st.error("Nenhuma base de dados encontrada. Carregue uma planilha em Auditoria e Upload.")
    st.stop()

# Detecção dinâmica da coluna de unidade
col_unidade = "Unidade_Completa" if "Unidade_Completa" in df.columns else (
    "Empresa_NomeFantasia" if "Empresa_NomeFantasia" in df.columns else "Filial"
)

# 2. Filtros Superiores
c_f1, c_f2 = st.columns([2, 2])
with c_f1:
    unidades_disp = ["TODAS"] + sorted(df[col_unidade].dropna().unique().tolist()) if col_unidade in df.columns else ["TODAS"]
    unidade_sel = st.selectbox("🏢 Filtrar por Unidade:", unidades_disp)

with c_f2:
    dres_disp = ["TODAS"] + sorted(df["Dre"].dropna().unique().tolist()) if "Dre" in df.columns else ["TODAS"]
    dre_sel = st.selectbox("📁 Filtrar por Categoria DRE:", dres_disp)

df_base = df.copy()
if unidade_sel != "TODAS" and col_unidade in df_base.columns:
    df_base = df_base[df_base[col_unidade] == unidade_sel]
if dre_sel != "TODAS" and "Dre" in df_base.columns:
    df_base = df_base[df_base["Dre"] == dre_sel]

st.markdown("---")

# -------------------------------------------------------------
# 3. MOTOR DE DETECÇÃO DE DESVIOS (HISTÓRICO VS. ÚLTIMO MÊS)
# -------------------------------------------------------------
col_mes = "Mes_Ano" if "Mes_Ano" in df_base.columns else ("Lancamento_Mes" if "Lancamento_Mes" in df_base.columns else None)

if not col_mes:
    st.error("Coluna de competência mensal não identificada na base.")
    st.stop()

meses_ordenados = sorted(df_base[col_mes].dropna().unique().tolist())

if len(meses_ordenados) < 2:
    st.info("São necessários dados de pelo menos dois meses para calcular médias históricas e desvios.")
    st.stop()

ultimo_mes = meses_ordenados[-1]
meses_historicos = meses_ordenados[:-1]

# Agrupamento considerando a Unidade
idx_agrupamento = [col_unidade, "Dre", "Conta"] if col_unidade in df_base.columns else ["Dre", "Conta"]

pivot_contas = df_base.pivot_table(
    index=idx_agrupamento,
    columns=col_mes,
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
k2.metric("Alertas Críticos", f"{qtd_criticos} ocorrências", delta="Necessita Auditoria", delta_color="inverse")
k3.metric("Sob Atenção", f"{qtd_atencao} ocorrências", delta="Variação moderada", delta_color="off")
k4.metric("Com Redução", f"{qtd_reducao} ocorrências", delta="Evolução favorável")

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. GRÁFICO DE DISPERSÃO: IMPACTO FINANCEIRO X DESVIO %
# -------------------------------------------------------------
st.subheader("🎯 Matriz de Severidade (Impacto Financeiro x Desvio Percentual)")
st.caption("O quadrante superior direito concentra as contas mais críticas. Passe o mouse sobre o ponto para ver a unidade.")

color_map = {
    "🔴 Crítico (Alta Severa)": "#dc3545",
    "🟡 Atenção (Acima da Média)": "#ffc107",
    "🟢 Favorável (Redução)": "#28a745",
    "⚪ Em Linha com o Histórico": "#6c757d"
}

hover_cols = [col_unidade, "Dre", "Conta", "Media_Historica", "Ultimo_Mes_Valor"] if col_unidade in anomalias.columns else ["Dre", "Conta", "Media_Historica", "Ultimo_Mes_Valor"]

fig_disp = px.scatter(
    anomalias,
    x="Delta_%",
    y="Delta_Absoluto",
    color="Status",
    color_discrete_map=color_map,
    size="Ultimo_Mes_Valor",
    hover_name=col_unidade if col_unidade in anomalias.columns else "Conta",
    hover_data=hover_cols,
    title=f"Desvio Percentual vs. Desvio em Reais (Mês: {ultimo_mes})",
    template="plotly_dark",
    labels={
        col_unidade: "Unidade",
        "Delta_%": "Variação sobre a Média Histórica (%)",
        "Delta_Absoluto": "Diferença em R$ (Realizado - Média)",
        "Ultimo_Mes_Valor": "Valor Atual (R$)"
    }
)
fig_disp.add_vline(x=0, line_dash="dash", line_color="gray")
fig_disp.add_hline(y=0, line_dash="dash", line_color="gray")
fig_disp.update_layout(yaxis=dict(tickformat="~s"), margin=dict(l=20, r=20, t=40, b=20))
st.plotly_chart(fig_disp, use_container_width=True)

# -------------------------------------------------------------
# 6. TABELA AUDITÁVEL DOS ALERTAS (COM COLUNA DE UNIDADE)
# -------------------------------------------------------------
st.subheader("📋 Tabela Gerencial de Contas Fora do Padrão")

# Ordena por gravidade do desvio absoluto
tabela_exibir = anomalias[anomalias["Status"] != "⚪ Em Linha com o Histórico"].sort_values(
    by="Delta_Absoluto", ascending=False
)

colunas_view = ["Status"]
if col_unidade in tabela_exibir.columns:
    colunas_view.append(col_unidade)
colunas_view += ["Dre", "Conta", "Media_Historica", "Ultimo_Mes_Valor", "Delta_Absoluto", "Delta_%"]

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

format_dict = {
    "Média Histórica (R$)": fmt_moeda,
    f"Realizado em {ultimo_mes} (R$)": fmt_moeda,
    "Diferença (R$)": fmt_diferenca,
    "Desvio (%)": lambda x: f"{x:+.1f}%" if pd.notna(x) else "0.0%"
}

rename_dict = {
    col_unidade: "Unidade / Filial",
    "Dre": "Categoria DRE",
    "Conta": "Conta Contábil",
    "Media_Historica": "Média Histórica (R$)",
    "Ultimo_Mes_Valor": f"Realizado em {ultimo_mes} (R$)",
    "Delta_Absoluto": "Diferença (R$)",
    "Delta_%": "Desvio (%)"
}

st.dataframe(
    tabela_exibir[colunas_view].rename(columns=rename_dict).style.format(format_dict),
    use_container_width=True,
    height=450,
    hide_index=True
)
