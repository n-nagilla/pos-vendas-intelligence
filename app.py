import streamlit as st
if not st.session_state.get("usuario_autenticado", False):
    st.warning("🔒 Acesso restrito! Por favor, realize o login na tela inicial.")
    st.stop()
import hmac
import plotly.express as px
import pandas as pd
from data.repository import obter_dados_ativos
from analytics.indicators import MetricasFinanceiras
from components.navbar import renderizar_filtros_superiores

st.set_page_config(
    page_title="Pós-Vendas Intelligence | Mardisa Agro",
    page_icon="🚜",
    layout="wide"
)

# -------------------------------------------------------------
# PORTAL DE AUTENTICAÇÃO SEGURO (USUÁRIO + SENHA)
# -------------------------------------------------------------
def sistema_login():
    # 1. Verifica se já está logado
    if st.session_state.get("usuario_autenticado", False):
        with st.sidebar:
            st.markdown(f"👤 Usuário conectado:")
            st.info(f"**{st.session_state.get('nome_usuario', 'Operador')}**")
            if st.button("🚪 Encerrar Sessão", use_container_width=True):
                st.session_state["usuario_autenticado"] = False
                st.session_state["nome_usuario"] = None
                st.rerun()
        return True

    # 2. Se NÃO está logado, esconde menu lateral e abas
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {display: none !important;}
            [data-testid="stSidebar"] {display: none !important;}
        </style>
        """,
        unsafe_allow_html=True
    )

    # 3. Card visual de Login
    col_esq, col_card, col_dir = st.columns([1, 1.2, 1])

    with col_card:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🔒 Acesso Restrito")
        st.caption("Central de Inteligência do Pós-Vendas | Mardisa Agro")

        with st.form("form_autenticacao"):
            input_user = st.text_input("Nome de Usuário", placeholder="Ex: nagilla ou diretoria").strip().lower()
            input_pass = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            btn_entrar = st.form_submit_button("Acessar Painel", use_container_width=True)

            if btn_entrar:
                # Busca a lista de usuários cadastrada nos Secrets
                usuarios_validos = st.secrets.get("users", {})

                if not input_user or not input_pass:
                    st.warning("⚠️ Preencha usuário e senha.")
                elif input_user in usuarios_validos and hmac.compare_digest(input_pass, str(usuarios_validos[input_user])):
                    st.session_state["usuario_autenticado"] = True
                    st.session_state["nome_usuario"] = input_user.capitalize()
                    st.success(f"✅ Bem-vindo(a), {input_user.capitalize()}! Acessando...")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

    # Interrompe o carregamento do restante do app até que o login seja validado
    st.stop()

# Executa a trava
sistema_login()

# =============================================================
# CONTEÚDO PRINCIPAL (SÓ APARECE APÓS LOGIN VÁLIDO)
# =============================================================

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
