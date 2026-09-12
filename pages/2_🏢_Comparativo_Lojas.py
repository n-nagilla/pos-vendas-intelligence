import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Benchmarking de Unidades | Mardisa Agro",
    page_icon="🏢",
    layout="wide"
)

# -------------------------------------------------------------
# 0. TRAVA DE SEGURANÇA (COMPATÍVEL COM app.py)
# -------------------------------------------------------------
if not st.session_state.get("autenticado", False):
    st.warning("🔒 Acesso restrito! Por favor, realize o login na tela inicial.")
    st.stop()

from data.repository import obter_dados_ativos

def formatar_moeda_brl(val):
    if val is None or pd.isna(val):
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.title("🏢 Benchmarking & Comparativo entre Lojas")
st.caption("Análise de eficiência de custos entre Fendt Balsas, Valtra Balsas, Imperatriz e Alto Alegre")

# -------------------------------------------------------------
# 1. CARREGAMENTO DOS DADOS E TRATAMENTO
# -------------------------------------------------------------
df = obter_dados_ativos()

if df.empty:
    st.error("Nenhuma base de dados encontrada. Carregue uma planilha em Auditoria e Upload.")
    st.stop()

# Detecção segura de colunas
col_unidade = "Unidade_Completa" if "Unidade_Completa" in df.columns else (
    "Empresa_NomeFantasia" if "Empresa_NomeFantasia" in df.columns else "Filial"
)
col_mes = "Mes_Ano" if "Mes_Ano" in df.columns else ("Lancamento_Mes" if "Lancamento_Mes" in df.columns else None)

if "Valor_Liquido" not in df.columns:
    deb = df["Debito"] if "Debito" in df.columns else 0
    cred = df["Credito"] if "Credito" in df.columns else 0
    df["Valor_Liquido"] = deb - cred

# -------------------------------------------------------------
# 2. FILTRO DE PERÍODO SUPERIOR
# -------------------------------------------------------------
col_f1, col_f2 = st.columns([3, 1])
with col_f1:
    meses_disponiveis = sorted(df[col_mes].dropna().unique().tolist()) if col_mes else []
    meses_selecionados = st.multiselect(
        "📅 Filtrar Período (Meses):",
        options=meses_disponiveis,
        default=meses_disponiveis
    )

if meses_selecionados and col_mes:
    df_f = df[df[col_mes].isin(meses_selecionados)]
else:
    df_f = df.copy()

st.markdown("---")

# -------------------------------------------------------------
# 3. SCORECARD GERAL DAS LOJAS (BENCHMARKING)
# -------------------------------------------------------------
st.subheader("📊 Raio-X Consolidado por Unidade")

resumo_lojas = df_f.groupby(col_unidade).agg(
    Total_Gasto=("Valor_Liquido", "sum"),
    Qtd_Lancamentos=("Valor_Liquido", "count"),
    Ticket_Medio_Lancamento=("Valor_Liquido", "mean")
).reset_index()

total_rede = resumo_lojas["Total_Gasto"].sum()
resumo_lojas["Participacao_%"] = (resumo_lojas["Total_Gasto"] / total_rede * 100).round(1) if total_rede > 0 else 0
resumo_lojas = resumo_lojas.sort_values(by="Total_Gasto", ascending=False)

# Renderiza colunas dinâmicas conforme a quantidade de lojas
if not resumo_lojas.empty:
    cols = st.columns(len(resumo_lojas))
    for idx, (_, row) in enumerate(resumo_lojas.iterrows()):
        with cols[idx]:
            st.metric(
                label=f"📍 {row[col_unidade]}",
                value=formatar_moeda_brl(row["Total_Gasto"]),
                delta=f"{row['Participacao_%']}% da Rede",
                delta_color="off"
            )

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. GRÁFICOS COMPARATIVOS: MACRO-CATEGORIAS (DRE)
# -------------------------------------------------------------
col_g1, col_g2 = st.columns([1.5, 1])

with col_g1:
    st.subheader("Composição de Custos por Filial (DRE)")
    df_dre_loja = df_f.groupby([col_unidade, "Dre"])["Valor_Liquido"].sum().reset_index()
    
    fig_barras = px.bar(
        df_dre_loja,
        x=col_unidade,
        y="Valor_Liquido",
        color="Dre",
        title="Despesas por Categoria (Administrativo x Pessoal x Vendas)",
        barmode="stack",
        template="plotly_dark",
        labels={"Valor_Liquido": "Despesa (R$)", col_unidade: "Unidade"}
    )
    fig_barras.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.2),
        yaxis=dict(tickformat="~s"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_barras, use_container_width=True)

with col_g2:
    st.subheader("Divisão do Desembolso Total")
    fig_donut = px.pie(
        resumo_lojas,
        names=col_unidade,
        values="Total_Gasto",
        hole=0.45,
        title="Participação no Custo da Concessionária",
        template="plotly_dark"
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    fig_donut.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------
# 5. DETALHAMENTO & DRILL-DOWN POR LOJA SELECIONADA
# -------------------------------------------------------------
st.subheader("🔍 Diagnóstico Aprofundado por Unidade")

lojas_lista = resumo_lojas[col_unidade].tolist()

if lojas_lista:
    loja_selecionada = st.selectbox(
        "Escolha uma unidade para auditoria detalhada:",
        options=lojas_lista
    )

    df_loja_drill = df_f[df_f[col_unidade] == loja_selecionada]

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
            template="plotly_dark"
        )
        fig_ofensores_loja.update_layout(
            yaxis=dict(autorange="reversed"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_ofensores_loja, use_container_width=True)

    with col_d2:
        st.markdown(f"**Evolução Mensal em `{loja_selecionada}`**")
        if col_mes:
            evo_loja = df_loja_drill.groupby([col_mes, "Dre"])["Valor_Liquido"].sum().reset_index()
            fig_evo_loja = px.line(
                evo_loja,
                x=col_mes,
                y="Valor_Liquido",
                color="Dre",
                markers=True,
                template="plotly_dark"
            )
            fig_evo_loja.update_layout(
                legend=dict(orientation="h", y=-0.3),
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_evo_loja, use_container_width=True)

    # Tabela matricial de contas da unidade selecionada
    with st.expander(f"📋 Ver todas as contas detalhadas de {loja_selecionada}", expanded=False):
        if col_mes:
            tabela_loja = df_loja_drill.pivot_table(
                index=["Dre", "Conta"],
                columns=col_mes,
                values="Valor_Liquido",
                aggfunc="sum",
                fill_value=0
            )
            tabela_loja["TOTAL"] = tabela_loja.sum(axis=1)
            tabela_loja = tabela_loja.sort_values(by="TOTAL", ascending=False)
            
            st.dataframe(
                tabela_loja.style.format(formatar_moeda_brl),
                use_container_width=True
            )
