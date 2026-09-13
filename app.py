import streamlit as st
import hmac
import pandas as pd
import plotly.express as px
from datetime import datetime
import importlib

# Carrega os módulos da pasta views de forma segura
v01_painel_coordenadora = importlib.import_module("views.01_painel_coordenadora")
v02_carteira_os = importlib.import_module("views.02_carteira_os")
v03_processos_prazos = importlib.import_module("views.03_processos_prazos")
v04_controle_pecas = importlib.import_module("views.04_controle_pecas")
v05_controle_fabrica = importlib.import_module("views.05_controle_fabrica")
v06_devolucao_pecas = importlib.import_module("views.06_devolucao_pecas")
v07_campanhas_campo = importlib.import_module("views.07_campanhas_campo")
v08_entrega_tecnica = importlib.import_module("views.08_entrega_tecnica")
v09_acoes_coordenadora = importlib.import_module("views.09_acoes_coordenadora")
v10_carteira_consultora = importlib.import_module("views.10_carteira_consultora")
v11_regra_ouro = importlib.import_module("views.11_regra_ouro")

# Importações dos módulos de Garantia Control
from data.db_manager import carregar_dados_gestao, sincronizar_excel_com_db, atualizar_os_completa
from views import (
    v01_painel_coordenadora,
    v02_carteira_os,
    v03_processos_prazos,
    v04_controle_pecas,
    v05_controle_fabrica,
    v06_devolucao_pecas,
    v07_campanhas_campo,
    v08_entrega_tecnica,
    v09_acoes_coordenadora,
    v10_carteira_consultora,
    v11_regra_ouro
)

st.set_page_config(
    page_title="Pós-Vendas Intelligence | Mardisa Agro",
    page_icon="🚜",
    layout="wide"
)

# 1. Trava inicial de sessão
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# 2. Tela de Login se não estiver autenticado
if not st.session_state["autenticado"]:
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"], [data-testid="stSidebar"] { display: none !important; }
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
                usuarios_validos = {
                    "admin": "Mardisa@2026",
                    "nagilla": "Agro#Nagilla2026",
                    "diretoria": "Parvi@PosVendas2026",
                    "coordenacao": "Garantia#2026"
                }

                if hasattr(st, "secrets") and "users" in st.secrets:
                    usuarios_validos.update(dict(st.secrets["users"]))

                if input_usuario in usuarios_validos and hmac.compare_digest(
                    input_senha, str(usuarios_validos[input_usuario])
                ):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_conectado"] = input_usuario.lower()
                    st.session_state["usuario_nome"] = input_usuario.capitalize()
                    st.success("✅ Acesso autorizado!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

    st.stop()

# Captura o identificador do usuário conectado
usuario_atual = st.session_state.get("usuario_conectado", "").lower()

with st.sidebar:
    st.markdown(f"👤 Conectado: **{st.session_state.get('usuario_nome', 'Operador')}**")
    if st.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_conectado"] = None
        st.session_state["usuario_nome"] = None
        st.rerun()

def calcular_criticidade_e_prazos(df):
    if df.empty:
        return df
    
    hoje = datetime.now()
    dias_os = []
    semaforo_os = []
    
    for _, row in df.iterrows():
        dt_emissao = pd.to_datetime(row.get("Emissao"), format="%d/%m/%Y", errors="coerce")
        dias = 0 if pd.isna(dt_emissao) else (hoje - dt_emissao).days
        dias_os.append(dias)
        
        if dias <= 30:
            semaforo_os.append("🟢 Dentro do Prazo")
        elif dias <= 50:
            semaforo_os.append("🟡 Atenção")
        else:
            semaforo_os.append("🔴 Crítico (>60d)")
            
    df["Dias_Aberto_OS"] = dias_os
    df["Semáforo_Prazo"] = semaforo_os
    return df

# =========================================================================
# FLUXO EXCLUSIVO PARA A USUÁRIA: NAGILLA (Garantia Control - 11 Abas)
# =========================================================================
if usuario_atual == "nagilla":
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚜 Garantia Control | Mardisa Agro")
    st.caption("Central de Inteligência e Gestão de Garantias — Fendt & Valtra (Grupo Parvi)")

    col_sync, _ = st.columns([1, 4])
    with col_sync:
        if st.button("🔄 Sincronizar Base", use_container_width=True):
            sincronizar_excel_com_db()
            st.toast("Base sincronizada com sucesso!")
            st.rerun()

    df = carregar_dados_gestao()
    if not df.empty:
        df = calcular_criticidade_e_prazos(df)

    abas = st.tabs([
        "🚦 1. Painel da Coordenadora",
        "📋 2. Carteira de O.S.",
        "⏱️ 3. Processos & Prazos",
        "📦 4. Controle de Peças",
        "💰 5. Controle Fábrica",
        "📦 6. Devolução de Peças",
        "🚜 7. Campanhas de Campo",
        "📑 8. Entrega Técnica",
        "🔴 9. Ações da Coordenadora",
        "👥 10. Carteira da Consultora",
        "⚠️ 11. Regra de Ouro"
    ])

    with abas[0]:
        v01_painel_coordenadora.render(df)
    with abas[1]:
        v02_carteira_os.render(df)
    with abas[2]:
        v03_processos_prazos.render(df)
    with abas[3]:
        v04_controle_pecas.render(df)
    with abas[4]:
        v05_controle_fabrica.render(df)
    with abas[5]:
        v06_devolucao_pecas.render(df)
    with abas[6]:
        v07_campanhas_campo.render(df)
    with abas[7]:
        v08_entrega_tecnica.render(df)
    with abas[8]:
        v09_acoes_coordenadora.render(df)
    with abas[9]:
        v10_carteira_consultora.render(df)
    with abas[10]:
        v11_regra_ouro.render(df)

# =========================================================================
# FLUXO ORIGINAL PARA DEMAIS USUÁRIOS (Diretoria, Admin, Coordenação)
# =========================================================================
else:
    from data.repository import obter_dados_ativos
    from analytics.indicators import MetricasFinanceiras
    from components.navbar import renderizar_filtros_superiores

    st.title("🚜 Central de Inteligência do Pós-Vendas")
    st.caption("Visão Executiva Consolidada de Custos e Despesas Operacionais")

    df_completo = obter_dados_ativos()

    if df_completo.empty:
        st.error("Planilha padrão não encontrada em `data/raw/` ou sem dados válidos.")
        st.stop()

    df_filtrado = renderizar_filtros_superiores(df_completo)
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
