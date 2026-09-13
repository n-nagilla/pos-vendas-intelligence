import streamlit as st
import pandas as pd
from datetime import datetime
from data.db_manager import carregar_dados_gestao, atualizar_os_completa, sincronizar_excel_com_db

def fmt_brl(v):
    if v is None or pd.isna(v):
        return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

def carregar_garantia_control():
    # Oculta navegação padrão lateral do Streamlit para deixar limpo para a Nagilla
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚜 Garantia Control | Mardisa Agro")
    st.caption("Central de Inteligência e Gestão de Garantias — Fendt & Valtra (Grupo Parvi)")

    col_sync, col_info = st.columns([1, 4])
    with col_sync:
        if st.button("🔄 Sincronizar Base", use_container_width=True):
            sincronizar_excel_com_db()
            st.toast("Base sincronizada com sucesso!")
            st.rerun()

    df = carregar_dados_gestao()
    if df.empty:
        st.warning("⚠️ Nenhuma Ordem de Serviço encontrada no banco de dados. Clique em 'Sincronizar Base'.")
        return

    df = calcular_criticidade_e_prazos(df)

    # Filtro Superior por Filial / Operação
    filiais_disponiveis = ["Todas", "Fendt Balsas", "Valtra Balsas", "Alto Alegre", "Imperatriz"]
    filial_selecionada = st.selectbox("🎯 Filtrar por Filial / Operação", filiais_disponiveis)

    if filial_selecionada != "Todas":
        df = df[df["Operacao"].str.contains(filial_selecionada, case=False, na=False)]

    # 11 Abas do Escopo
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

    # 1. Painel da Coordenadora
    with abas[0]:
        st.subheader("🔴 Atenção da Coordenadora Hoje")
        c1, c2, c3, c4, c5 = st.columns(5)
        criticas = len(df[df["Semáforo_Prazo"] == "🔴 Crítico (>60d)"])
        atencao = len(df[df["Semáforo_Prazo"] == "🟡 Atenção"])
        bo_pecas = len(df[df.get("Peca_BO", "") == "Sim"])
        em_fabrica = len(df[df.get("Status_Garantia", "") == "Em análise fábrica"])
        saldo_parado = df["Valor_Liquido"].sum()

        c1.metric("🔴 O.S. Críticas (>60d)", f"{criticas} O.S.")
        c2.metric("🟡 Alerta (30 a 60d)", f"{atencao} O.S.")
        c3.metric("📦 Peças em B.O.", f"{bo_pecas} O.S.")
        c4.metric("🏭 Em Análise Fábrica", f"{em_fabrica} O.S.")
        c5.metric("💵 Saldo Parado", fmt_brl(saldo_parado))

        st.markdown("### Saúde Operacional por Filial")
        resumo_operacao = df.groupby("Operacao").agg(
            OS_Abertas=("Numero", "count"),
            Em_Atraso=("Semáforo_Prazo", lambda x: (x == "🔴 Crítico (>60d)").sum()),
            Aguardando_Pecas=("Peca_BO", lambda x: (x == "Sim").sum()),
            Valor_Total=("Valor_Liquido", "sum")
        ).reset_index()
        st.dataframe(resumo_operacao, use_container_width=True, hide_index=True)

    # 2. Carteira Completa de O.S.
    with abas[1]:
        st.subheader("📋 Carteira Completa de O.S.")
        st.dataframe(df, use_container_width=True, hide_index=True)

    # 3. Controle do Processo de Garantia (Prazos FleetScan)
    with abas[2]:
        st.subheader("⏱️ Controle do Processo de Garantia & Prazos (30d / 60d)")
        st.dataframe(
            df[["Numero", "Cliente", "Modelo", "Emissao", "Dias_Aberto_OS", "Semáforo_Prazo", "Status_Garantia"]],
            use_container_width=True, hide_index=True
        )

    # 4. Controle de Peças
    with abas[3]:
        st.subheader("📦 Controle de Peças Pendentes & B.O.")
        df_pecas = df[df.get("Necessita_Peca", "Não") == "Sim"]
        st.dataframe(df_pecas, use_container_width=True, hide_index=True)

    # 5. Controle Fábrica (Dinheiro Parado)
    with abas[4]:
        st.subheader("💰 Controle Fábrica — Dinheiro Parado")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        col_f1.metric("Valor Submetido", fmt_brl(df.get("Valor_Solicitado", pd.Series([0])).sum()))
        col_f2.metric("Valor Aprovado", fmt_brl(df.get("Valor_Aprovado", pd.Series([0])).sum()))
        col_f3.metric("Aguardando Faturamento", fmt_brl(0))
        col_f4.metric("Valor Faturado", fmt_brl(df.get("Valor_Faturado", pd.Series([0])).sum()))

    # 6. Devolução de Peças
    with abas[5]:
        st.subheader("📦 Devolução de Peças à Fábrica")
        st.info("Painel de rastreabilidade de NF de devolução, envio e encerramento de peças solicitadas pela fábrica.")
        st.dataframe(df[["Numero", "Cliente", "Modelo", "Codigo_Descricao_Peca"]], use_container_width=True, hide_index=True)

    # 7. Campanhas de Campo
    with abas[6]:
        st.subheader("🚜 Campanhas de Campo (Fendt & Valtra)")
        st.dataframe(df[["Numero", "Cliente", "Modelo", "Serie"]], use_container_width=True, hide_index=True)

    # 8. Entrega Técnica / Novas Máquinas
    with abas[7]:
        st.subheader("📑 Entrega Técnica e Registro de Garantia")
        st.dataframe(df[["Numero", "Cliente", "Modelo", "Serie", "Emissao"]], use_container_width=True, hide_index=True)

    # 9. As 10 Ações da Coordenadora
    with abas[8]:
        st.subheader("🔴 10 Ações Prioritárias da Coordenadora Hoje")
        df_prioridades = df[
            (df["Gargalo_Atual"] != "") | 
            (df["Proxima_Acao"] == "") | 
            (df["Semáforo_Prazo"].isin(["🔴 Crítico (>60d)", "🟡 Atenção"]))
        ].head(10)
        st.dataframe(df_prioridades[["Numero", "Operacao", "Cliente", "Modelo", "Gargalo_Atual", "Proxima_Acao", "Responsavel"]], use_container_width=True, hide_index=True)

    # 10. Carteira da Consultora
    with abas[9]:
        st.subheader("👥 Performance da Carteira por Consultora")
        if "Consultor_Responsavel" in df.columns:
            st.dataframe(
                df.groupby("Consultor_Responsavel", dropna=False).agg(
                    OS_Abertas=("Numero", "count"),
                    Valor_Total=("Valor_Liquido", "sum")
                ).reset_index(),
                use_container_width=True, hide_index=True
            )

    # 11. Regra de Ouro (Validação de O.S. incompletas)
    with abas[10]:
        st.subheader("⚠️ Regra de Ouro — Auditoria de O.S. Sem Controle")
        st.warning("Toda O.S. aberta obrigatoriamente precisa ter: Status Atual, Gargalo, Responsável, Próxima Ação e Data da Próxima Ação.")
        
        lista_os = df["Numero"].tolist()
        os_sel = st.selectbox("Selecione o Nº da O.S. para Editar/Atualizar", lista_os)
        os_row = df[df["Numero"] == os_sel].iloc[0]

        with st.form("form_regra_ouro"):
            c1, c2, c3 = st.columns(3)
            with c1:
                status_u = st.selectbox("Status Atual", ["Aberta na Oficina", "Aguardando Peças", "Em análise fábrica", "Aprovada", "Rejeitada", "Faturada"])
                gargalo_u = st.selectbox("Gargalo Atual", ["", "Peça", "Fábrica", "Serviço", "Administrativo"])
            with c2:
                resp_u = st.text_input("Responsável", value=os_row.get("Responsavel", ""))
                prox_u = st.text_input("Próxima Ação", value=os_row.get("Proxima_Acao", ""))
            with c3:
                data_prox_u = st.text_input("Data da Próxima Ação", value=os_row.get("Prazo_Acao", ""))
                aol_u = st.text_input("Nº Protocolo / AOL", value=os_row.get("AOL_Protocolo", ""))

            obs_u = st.text_area("Observações", value=os_row.get("Observacoes", ""))
            if st.form_submit_button("💾 Salvar Validação da O.S.", use_container_width=True):
                atualizar_os_completa(os_sel, {
                    "Status_Garantia": status_u,
                    "Gargalo_Atual": gargalo_u,
                    "Responsavel": resp_u,
                    "Proxima_Acao": prox_u,
                    "Prazo_Acao": data_prox_u,
                    "AOL_Protocolo": aol_u,
                    "Observacoes": obs_u
                })
                st.success(f"O.S. {os_sel} validada com sucesso!")
                st.rerun()     
