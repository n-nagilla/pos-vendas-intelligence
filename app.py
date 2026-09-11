import streamlit as st
import plotly.express as px
from data.repository import obter_dados_ativos
from analytics.indicators import MetricasFinanceiras
from components.navbar import renderizar_filtros_superiores

st.set_page_config(
    page_title="Pós-Vendas Intelligence | Mardisa Agro",
    page_icon="🚜",
    layout="wide"
)

st.title("🚜 Central de Inteligência do Pós-Vendas")
st.caption("Visão Executiva Consolidada de Custos e Despesas Operacionais")

# 1. Carregamento dos dados
df_completo = obter_dados_ativos()

if df_completo.empty:
    st.error("Planilha padrão não encontrada em `data/raw/` ou sem dados válidos.")
    st.stop()

# 2. Barra de Filtros Globais
df_filtrado = renderizar_filtros_superiores(df_completo)

# 3. Métricas Executivas
kpis = MetricasFinanceiras.calcular_kpis_gerais(df_filtrado)

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Total de Despesas", fmt_brl(kpis["total"]))
c2.metric("👥 Despesas Pessoal", fmt_brl(kpis["total_pessoal"]), 
          delta=f"{(kpis['total_pessoal']/kpis['total']*100):.1f}% do total" if kpis["total"] > 0 else None)
c3.metric("🏢 Administrativo", fmt_brl(kpis["total_adm"]), 
          delta=f"{(kpis['total_adm']/kpis['total']*100):.1f}% do total" if kpis["total"] > 0 else None)
c4.metric("🚜 Vendas / Campo", fmt_brl(kpis["total_vendas"]), 
          delta=f"{(kpis['total_vendas']/kpis['total']*100):.1f}% do total" if kpis["total"] > 0 else None)

st.markdown("<br>", unsafe_allow_html=True)

# 4. Gráficos de Tomada de Decisão
tab_visao, tab_ofensores, tab_matriz = st.tabs([
    "📈 Evolução & Tendência", 
    "🚨 Ranking de Ofensores (Top 10)", 
    "📋 Visão DRE Matricial"
])

with tab_visao:
    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        df_evo = MetricasFinanceiras.calcular_evolucao_mensal(df_filtrado)
        fig_evo = px.line(
            df_evo, x="Competencia", y="Valor_Liquido", color="Dre",
            markers=True, title="Evolução Mensal por Categoria DRE",
            template="plotly_white",
            labels={"Valor_Liquido": "Valor (R$)", "Competencia": "Mês"}
        )
        fig_evo.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_evo, use_container_width=True)
        
    with col_g2:
        df_filial = df_filtrado.groupby("Unidade_Completa")["Valor_Liquido"].sum().reset_index()
        fig_pie = px.pie(
            df_filial, names="Unidade_Completa", values="Valor_Liquido", hole=0.45,
            title="Distribuição por Loja", template="plotly_white"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with tab_ofensores:
    st.subheader("Contas que Mais Pressionam o Custo")
    df_top = MetricasFinanceiras.ranking_ofensores(df_filtrado, top_n=10)
    fig_bar = px.bar(
        df_top, x="Valor_Liquido", y="Conta", orientation="h", color="Dre",
        text_auto=".2s", title="Top 10 Contas com Maior Desembolso",
        template="plotly_white"
    )
    fig_bar.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_bar, use_container_width=True)

with tab_matriz:
    st.subheader("Matriz Dinâmica (Contas x Meses)")
    pivot = df_filtrado.pivot_table(
        index=["Dre", "Conta"],
        columns="Mes_Ano",
        values="Valor_Liquido",
        aggfunc="sum",
        fill_value=0
    )
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.sort_values(by="TOTAL", ascending=False)
    
    st.dataframe(
        pivot.style.format("R$ {:,.2f}").background_gradient(cmap="Reds", subset=["TOTAL"]),
        use_container_width=True
    )