import streamlit as st
import hmac
import pandas as pd
import plotly.express as px

# 1. Configuração de página OBRIGATORIAMENTE no topo
st.set_page_config(
    page_title="Pós-Vendas Intelligence | Mardisa Agro",
    page_icon="🚜",
    layout="wide"
)

# 2. Estado de autenticação inicial
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# ----------------------------------------------------------------------
# 3. TELA DE LOGIN (EXECUTA ENQUANTO NÃO AUTENTICADO)
# ----------------------------------------------------------------------
if not st.session_state["autenticado"]:
    # Oculta completamente barra lateral e navegação nativa
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] { display: none !important; }
            [data-testid="stSidebar"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("## 🔒 Acesso Restrito")
        st.caption("Pós-Vendas Intelligence | Mardisa Agro")

        with st.form("form_seguranca"):
            input_usuario = st.text_input("Usuário").strip().lower()
            input_senha = st.text_input("Senha", type="password").strip()
            botao_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)

            if botao_entrar:
                # Dicionário de credenciais válidas
                usuarios_validos = {
                    "admin": "Mardisa@2026",
                    "nagilla": "Agro#Nagilla2026",
                    "diretoria": "Parvi@PosVendas2026",
                    "coordenacao": "Garantia#2026"
                }

                # Incorpora secrets caso configurados
                if hasattr(st, "secrets") and "users" in st.secrets:
                    usuarios_validos.update(dict(st.secrets["users"]))

                if input_usuario in usuarios_validos and hmac.compare_digest(
                    input_senha, str(usuarios_validos[input_usuario])
                ):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_conectado"] = input_usuario.capitalize()
                    st.success("✅ Acesso autorizado!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

    # Interrompe o script para não carregar nada além do login
    st.stop()

# ----------------------------------------------------------------------
# 4. CONTEÚDO PRINCIPAL (SÓ CARREGA APÓS LOGIN)
# ----------------------------------------------------------------------
from data.repository import obter_dados_ativos
from analytics.indicators import MetricasFinanceiras
from components.navbar import renderizar_filtros_superiores

with st.sidebar:
    st.markdown(f"👤 Conectado: **{st.session_state.get('usuario_conectado', 'Operador')}**")
    if st.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_conectado"] = None
        st.rerun()

st.title("🚜 Central de Inteligência do Pós-Vendas")
st.caption("Visão Executiva Consolidada de Custos e Despesas Operacionais")

# Carregamento dos dados
df_completo = obter_dados_ativos()

if df_completo.empty:
    st.error("Planilha padrão não encontrada em `data/raw/` ou sem dados válidos.")
    st.stop()

# Barra de Filtros Globais
df_filtrado = renderizar_filtros_superiores(df_completo)

# Métricas Executivas
kpis = MetricasFinanceiras.calcular_kpis_gerais(df_filtrado)

def fmt_brl(v):
    if v is None or pd.isna(v):
        return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Total de Despesas", fmt_brl(kpis["total"]))
c2.metric(
    "👥 Despesas Pessoal",
    fmt_brl(kpis["total_pessoal"]),
    delta=f"{(kpis['total_pessoal']/kpis['total']*100):.1f}% do total" if kpis["total"] > 0 else None
)
c3.metric(
    "🏢 Administrativo",
    fmt_brl(kpis["total_adm"]),
    delta=f"{(kpis['total_adm']/kpis['total']*100):.1f}% do total" if kpis["total"] > 0 else None
)
c4.metric(
    "🚜 Vendas / Campo",
    fmt_brl(kpis["total_vendas"]),
    delta=f"{(kpis['total_vendas']/kpis['total']*100):.1f}% do total" if kpis["total"] > 0 else None
)

st.markdown("<br>", unsafe_allow_html=True)

# Abas Analíticas
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
            df_evo,
            x="Competencia",
            y="Valor_Liquido",
            color="Dre",
            markers=True,
            title="Evolução Mensal por Categoria DRE",
            template="plotly_dark",
            labels={"Valor_Liquido": "Valor (R$)", "Competencia": "Mês"}
        )
        fig_evo.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_evo, use_container_width=True)

    with col_g2:
        col_loja = "Unidade_Completa" if "Unidade_Completa" in df_filtrado.columns else (
            "Empresa_NomeFantasia" if "Empresa_NomeFantasia" in df_filtrado.columns else "Filial"
        )
        df_filial = df_filtrado.groupby(col_loja)["Valor_Liquido"].sum().reset_index()
        fig_pie = px.pie(
            df_filial,
            names=col_loja,
            values="Valor_Liquido",
            hole=0.45,
            title="Distribuição por Loja",
            template="plotly_dark"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with tab_ofensores:
    st.subheader("Contas que Mais Pressionam o Custo")
    df_top = MetricasFinanceiras.ranking_ofensores(df_filtrado, top_n=10)
    fig_bar = px.bar(
        df_top,
        x="Valor_Liquido",
        y="Conta",
        orientation="h",
        color="Dre",
        text_auto=".2s",
        title="Top 10 Contas com Maior Desembolso",
        template="plotly_dark"
    )
    fig_bar.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_bar, use_container_width=True)

with tab_matriz:
    st.subheader("Matriz Dinâmica (Contas x Meses)")
    col_mes = "Mes_Ano" if "Mes_Ano" in df_filtrado.columns else "Lancamento_Mes"
    pivot = df_filtrado.pivot_table(
        index=["Dre", "Conta"],
        columns=col_mes,
        values="Valor_Liquido",
        aggfunc="sum",
        fill_value=0
    )
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot = pivot.sort_values(by="TOTAL", ascending=False)

    st.dataframe(
        pivot.style.format(fmt_brl).background_gradient(cmap="Reds", subset=["TOTAL"]),
        use_container_width=True
    )
