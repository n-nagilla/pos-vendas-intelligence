import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.repository import obter_dados_ativos

st.set_page_config(
    page_title="Simulador de Cenários | Mardisa Agro",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Simulador de Decisão e Sensibilidade Financeira")
st.caption("Projete o impacto financeiro de metas de redução de despesas sobre o orçamento do Pós-Vendas.")

# 1. Carregamento dos dados
df = obter_dados_ativos()

if df.empty:
    st.error("Nenhuma base de dados encontrada. Carregue uma planilha em Auditoria e Upload.")
    st.stop()

# 2. Filtro de Escopo da Simulação
col_escopo1, col_escopo2 = st.columns(2)
with col_escopo1:
    unidades_disp = ["TODAS AS UNIDADES"] + sorted(df["Unidade_Completa"].unique().tolist())
    unidade_sim = st.selectbox("🏢 Selecione o Escopo da Simulação:", unidades_disp)

with col_escopo2:
    meses_disp = sorted(df["Mes_Ano"].unique().tolist())
    meses_sim = st.multiselect("📅 Período Base para a Projeção:", meses_disp, default=meses_disp)

df_base = df.copy()
if unidade_sim != "TODAS AS UNIDADES":
    df_base = df_base[df_base["Unidade_Completa"] == unidade_sim]
if meses_sim:
    df_base = df_base[df_base["Mes_Ano"].isin(meses_sim)]

total_base = df_base["Valor_Liquido"].sum()
total_adm = df_base[df_base["Dre"] == "DESPESAS ADMINISTRATIVAS"]["Valor_Liquido"].sum()
total_pes = df_base[df_base["Dre"] == "DESPESAS COM PESSOAL"]["Valor_Liquido"].sum()
total_ven = df_base[df_base["Dre"] == "DESPESAS COM VENDAS"]["Valor_Liquido"].sum()

st.markdown("---")

# -------------------------------------------------------------
# 3. PAINEL DE CONTROLE DE PARÂMETROS (SLIDERS DE REDUÇÃO)
# -------------------------------------------------------------
st.subheader("⚙️ Parâmetros de Redução de Despesas (%)")
st.caption("Ajuste as metas percentuais de redução para cada categoria e simule a liberação de margem.")

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    st.markdown(f"**🏢 Administrativo** (Base: R$ {total_adm:,.0f})")
    corte_adm = st.slider("Redução Administrativa (%):", min_value=0, max_value=30, value=5, step=1, key="s_adm")

with col_s2:
    st.markdown(f"**👥 Pessoal** (Base: R$ {total_pes:,.0f})")
    corte_pes = st.slider("Otimização em Pessoal (%):", min_value=0, max_value=20, value=0, step=1, key="s_pes")

with col_s3:
    st.markdown(f"**🚜 Vendas / Campo** (Base: R$ {total_ven:,.0f})")
    corte_ven = st.slider("Redução Vendas/Campo (%):", min_value=0, max_value=30, value=10, step=1, key="s_ven")

# Cálculos do Cenário Simulado
econ_adm = total_adm * (corte_adm / 100)
econ_pes = total_pes * (corte_pes / 100)
econ_ven = total_ven * (corte_ven / 100)

economia_total = econ_adm + econ_pes + econ_ven
total_projetado = total_base - economia_total
pct_economia_geral = (economia_total / total_base * 100) if total_base > 0 else 0

# Anualização da Economia (com base nos meses filtrados)
qtd_meses = len(meses_sim) if meses_sim else 8
economia_anualizada = (economia_total / qtd_meses) * 12 if qtd_meses > 0 else 0

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. PLACAR DO RESULTADO SIMULADO
# -------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

k1.metric("Orçamento Base Atual", fmt_brl(total_base))
k2.metric("Orçamento Projetado", fmt_brl(total_projetado), delta=f"-{pct_economia_geral:.1f}%", delta_color="normal")
k3.metric("Economia no Período", fmt_brl(economia_total), delta="Margem Liberada")
k4.metric("Potencial Anualizado (12M)", fmt_brl(economia_anualizada), delta="Projeção Ano Fechado")

st.markdown("---")

# -------------------------------------------------------------
# 5. GRÁFICO EM CASCATA (WATERFALL) DE IMPACTO
# -------------------------------------------------------------
col_w1, col_w2 = st.columns([1.6, 1])

with col_w1:
    st.subheader("📊 Decomposição do Desembolso: Atual vs. Projetado")
    
    fig_waterfall = go.Figure(go.Waterfall(
        name="Impacto",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Custo Atual", "Econ. ADM", "Econ. Pessoal", "Econ. Vendas", "Custo Projetado"],
        y=[total_base, -econ_adm, -econ_pes, -econ_ven, total_projetado],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#28a745"}},
        totals={"marker": {"color": "#0d6efd"}},
        textposition="outside",
        text=[f"R$ {total_base/1e3:.0f}k", f"-R$ {econ_adm/1e3:.0f}k", f"-R$ {econ_pes/1e3:.0f}k", f"-R$ {econ_ven/1e3:.0f}k", f"R$ {total_projetado/1e3:.0f}k"]
    ))
    
    fig_waterfall.update_layout(
        template="plotly_white",
        yaxis=dict(title="Valor (R$)", tickformat="~s"),
        showlegend=False
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

with col_w2:
    st.subheader("📋 Matriz de Cenários Rápidos")
    st.caption("Comparativo pré-configurado de sensibilidade orçamentária:")

    cenarios = pd.DataFrame([
        {
            "Cenário": "Conservador (-5% Geral)",
            "Economia (R$)": total_base * 0.05,
            "Custo Projetado (R$)": total_base * 0.95
        },
        {
            "Cenário": "Base (-10% Geral)",
            "Economia (R$)": total_base * 0.10,
            "Custo Projetado (R$)": total_base * 0.90
        },
        {
            "Cenário": "Agressivo (-15% Geral)",
            "Economia (R$)": total_base * 0.15,
            "Custo Projetado (R$)": total_base * 0.85
        },
        {
            "Cenário": "Customizado (Sliders)",
            "Economia (R$)": economia_total,
            "Custo Projetado (R$)": total_projetado
        }
    ])

    st.dataframe(
        cenarios.style.format({
            "Economia (R$)": "R$ {:,.2f}",
            "Custo Projetado (R$)": "R$ {:,.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")

# -------------------------------------------------------------
# 6. SIMULAÇÃO POR CONTA ESPECÍFICA (EX: COMBUSTÍVEL, ALUGUEL)
# -------------------------------------------------------------
st.subheader("🔬 Simulação Focada em Conta Individual")
st.caption("Simule o impacto de renegociação em um fornecedor ou contrato específico.")

col_c1, col_c2, col_c3 = st.columns([2, 1, 1])

with col_c1:
    contas_lista = df_base.groupby("Conta")["Valor_Liquido"].sum().sort_values(ascending=False).index.tolist()
    conta_alvo = st.selectbox("Escolha a conta a ser renegociada:", options=contas_lista)

gasto_conta_alvo = df_base[df_base["Conta"] == conta_alvo]["Valor_Liquido"].sum()

with col_c2:
    st.metric(f"Desembolso Atual", fmt_brl(gasto_conta_alvo))

with col_c3:
    pct_alvo = st.number_input(f"Meta de Redução em {conta_alvo[:15]} (%):", min_value=0, max_value=100, value=10, step=5)
    econ_alvo = gasto_conta_alvo * (pct_alvo / 100)
    st.metric("Economia Direta", fmt_brl(econ_alvo), delta=f"-{pct_alvo}%")
