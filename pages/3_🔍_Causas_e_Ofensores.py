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

# -------------------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO LOCAL
# -------------------------------------------------------------
def formatar_moeda_brl(val):
    if pd.isna(val):
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.title("🔍 Diagnóstico de Causas & Contas Ofensoras")
st.caption("Identifique os principais responsáveis por variações de custo e concentração de desembolso.")

# -------------------------------------------------------------
# 1. CARREGAMENTO DOS DADOS
# -------------------------------------------------------------
df = obter_dados_ativos()

if df.empty:
    st.error("Nenhuma base de dados encontrada. Carregue uma planilha em Auditoria e Upload.")
    st.stop()

# Garantia de colunas essenciais
if "Valor_Liquido" not in df.columns:
    deb = df["Debito"] if "Debito" in df.columns else 0
    cred = df["Credito"] if "Credito" in df.columns else 0
    df["Valor_Liquido"] = deb - cred

# -------------------------------------------------------------
# 2. FILTROS SUPERIORES
# -------------------------------------------------------------
c_f1, c_f2 = st.columns([2, 2])

col_unidade = "Unidade_Completa" if "Unidade_Completa" in df.columns else "Empresa_NomeFantasia"

with c_f1:
    unidades_disp = ["TODAS"] + sorted(df[col_unidade].dropna().unique().tolist()) if col_unidade in df.columns else ["TODAS"]
    unidade_sel = st.selectbox("🏢 Filtrar Unidade:", unidades_disp)

with c_f2:
    dres_disp = ["TODAS"] + sorted(df["Dre"].dropna().unique().tolist()) if "Dre" in df.columns else ["TODAS"]
    dre_sel = st.selectbox("📁 Categoria DRE:", dres_disp)

df_base = df.copy()
if unidade_sel != "TODAS" and col_unidade in df_base.columns:
    df_base = df_base[df_base[col_unidade] == unidade_sel]
if dre_sel != "TODAS" and "Dre" in df_base.columns:
    df_base = df_base[df_base["Dre"] == dre_sel]

st.markdown("---")

# -------------------------------------------------------------
# SEÇÃO 1: VARIAÇÃO MÊS A MÊS (MoM)
# -------------------------------------------------------------
st.subheader("⚡ O que Provocou a Variação? (Análise de Causas)")
st.caption("Compare dois meses consecutivos para descobrir exatamente quais contas geraram aumento ou economia.")

col_mes = "Mes_Ano" if "Mes_Ano" in df_base.columns else ("Lancamento_Mes" if "Lancamento_Mes" in df_base.columns else None)
meses_lista = sorted(df_base[col_mes].dropna().unique().tolist()) if col_mes else []

if len(meses_lista) >= 2:
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        mes_anterior = st.selectbox("Mês de Referência (Base):", meses_lista, index=len(meses_lista)-2)
    with c_m2:
        mes_atual = st.selectbox("Mês de Comparação (Atual):", meses_lista, index=len(meses_lista)-1)

    # Agrupamento de valores
    df_ant = df_base[df_base[col_mes] == mes_anterior].groupby(["Dre", "Conta"])["Valor_Liquido"].sum().reset_index()
    df_atu = df_base[df_base[col_mes] == mes_atual].groupby(["Dre", "Conta"])["Valor_Liquido"].sum().reset_index()

    df_comp = pd.merge(df_ant, df_atu, on=["Dre", "Conta"], how="outer", suffixes=("_Ant", "_Atu")).fillna(0)
    df_comp["Variacao_R$"] = df_comp["Valor_Liquido_Atu"] - df_comp["Valor_Liquido_Ant"]
    df_comp["Variacao_%"] = df_comp.apply(
        lambda r: (r["Variacao_R$"] / r["Valor_Liquido_Ant"] * 100) if r["Valor_Liquido_Ant"] > 0 else 100.0, axis=1
    )

    total_ant = df_comp["Valor_Liquido_Ant"].sum()
    total_atu = df_comp["Valor_Liquido_Atu"].sum()
    dif_total = total_atu - total_ant
    pct_total = (dif_total / total_ant * 100) if total_ant > 0 else 0

    k1, k2, k3 = st.columns(3)
    k1.metric(f"Total em {mes_anterior}", formatar_moeda_brl(total_ant))
    k2.metric(f"Total em {mes_atual}", formatar_moeda_brl(total_atu))
    k3.metric(
        "Variação Líquida",
        formatar_moeda_brl(dif_total),
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
                template="plotly_dark"
            )
            fig_subiu.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
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
                template="plotly_dark"
            )
            fig_desceu.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
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

total_despesas_base = df_base["Valor_Liquido"].sum()

pareto_df = df_base.groupby("Conta")["Valor_Liquido"].sum().reset_index()
pareto_df = pareto_df.sort_values(by="Valor_Liquido", ascending=False).reset_index(drop=True)
pareto_df["Acumulado"] = pareto_df["Valor_Liquido"].cumsum()
pareto_df["Acumulado_%"] = (pareto_df["Acumulado"] / total_despesas_base * 100) if total_despesas_base > 0 else 0

# Top 15 contas
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
    line=dict(color="#e74c3c", width=2.5)
))

# Linha de corte nos 80%
fig_pareto.add_shape(
    type="line",
    x0=-0.5, x1=len(pareto_view)-0.5,
    y0=80, y1=80,
    yref="y2",
    line=dict(color="#f1c40f", width=2, dash="dash")
)

fig_pareto.update_layout(
    title="Top 15 Contas e Impacto Acumulado no Orçamento",
    xaxis=dict(tickangle=-45),
    yaxis=dict(title="Valor Total (R$)", tickformat="~s"),
    yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 105]),
    template="plotly_dark",
    legend=dict(orientation="h", y=1.15)
)

st.plotly_chart(fig_pareto, use_container_width=True)

# -------------------------------------------------------------
# CARD EXECUTIVO: AÇÃO CIRÚRGICA (DIRECIONAMENTO ESTRATÉGICO)
# -------------------------------------------------------------
# Filtra dinamicamente as contas principais responsáveis por compor os 80% iniciais
contas_criticas_df = pareto_df[pareto_df["Acumulado_%"] <= 85].head(5)
if contas_criticas_df.empty and not pareto_df.empty:
    contas_criticas_df = pareto_df.head(3)

contas_nomes = contas_criticas_df["Conta"].tolist()

recomendacoes = []
for c in contas_nomes:
    c_upper = c.upper()
    if "COMB" in c_upper or "LUBRIF" in c_upper:
        recomendacoes.append(f"**{c.title()}**: Auditoria de rotas de atendimento em campo, telemetria de veículos e renegociação de postos de combustível credenciados.")
    elif "ALUGUEL" in c_upper or "PREDIO" in c_upper or "MAQ" in c_upper:
        recomendacoes.append(f"**{c.title()}**: Revisão dos contratos de locação das instalações e readequação do parque de frotas e maquinários alugados.")
    elif "PERDA" in c_upper or "INCOBR" in c_upper:
        recomendacoes.append(f"**{c.title()}**: Alinhamento imediato com a equipe de cobrança e endurecimento da régua de concessão de crédito comercial.")
    elif "SALÁRIO" in c_upper or "SALARIO" in c_upper or "COMISS" in c_upper:
        recomendacoes.append(f"**{c.title()}**: Gestão e controle rigoroso de horas extras aliada à revisão do plano de produtividade técnica da oficina.")
    elif "CONSULTORIA" in c_upper or "AUDITORIA" in c_upper:
        recomendacoes.append(f"**{c.title()}**: Reavaliação de escopo e entregáveis de prestadores terceirizados e renegociação de honorários contratuais.")
    elif "VIAGEM" in c_upper or "ESTADA" in c_upper:
        recomendacoes.append(f"**{c.title()}**: Revisão das diárias de hospedagem em campo e planejamento antecipado de rotas para reduzir deslocamentos desnecessários.")
    else:
        recomendacoes.append(f"**{c.title()}**: Renegociação direta de tabelas com fornecedores prioritários e auditoria das autorizações de despesa.")

qtd_criticas = len(contas_criticas_df)
impacto_criticas = contas_criticas_df["Valor_Liquido"].sum()
perc_criticas = (impacto_criticas / total_despesas_base * 100) if total_despesas_base > 0 else 0

st.info(f"""
### 🎯 Ação Cirúrgica: Onde Mover o Ponteiro Financeiro
Apenas **{qtd_criticas} contas** concentram **{perc_criticas:.1f}% de todo o desembolso** ({formatar_moeda_brl(impacto_criticas)}). Economizar em pequenos gastos de rotina (papelaria, cafezinho) não alterará o resultado final da operação. O foco executivo deve ser direcionado prioritariamente para:

""" + "\n".join([f"- {rec}" for rec in recomendacoes]) + f"""

> 💡 **Direcionamento ao Gestor:** Renegociar frotas de combustível, rever contratos de locação e auditar perdas de crédito é o que protege de forma rápida a rentabilidade do Pós-Vendas.
""")

# -------------------------------------------------------------
# TABELA COMPLETA DE PARETO
# -------------------------------------------------------------
with st.expander("📋 Ver Tabela Completa de Pareto", expanded=False):
    tabela_display = pareto_df.copy()
    tabela_display["Valor_Liquido"] = tabela_display["Valor_Liquido"].apply(formatar_moeda_brl)
    tabela_display["Acumulado"] = tabela_display["Acumulado"].apply(formatar_moeda_brl)
    tabela_display["Acumulado_%"] = tabela_display["Acumulado_%"].map("{:.1f}%".format)
    
    st.dataframe(
        tabela_display.rename(columns={
            "Conta": "Conta de Despesa",
            "Valor_Liquido": "Valor Total",
            "Acumulado": "Total Acumulado",
            "Acumulado_%": "% Acumulada"
        }),
        use_container_width=True,
        hide_index=True
    )
