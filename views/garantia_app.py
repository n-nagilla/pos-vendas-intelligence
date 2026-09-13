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
        if pd.isna(dt_emissao):
            dias = 0
        else:
            dias = (hoje - dt_emissao).days
            
        dias_os.append(dias)
        
        # Regra de prazo: até 30 dias normal, 31-50 atenção, >50 crítico
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
    st.title("🚜 Garantia Control | Mardisa Agro")
    st.caption("Central de Inteligência e Gestão de Garantias — Fendt & Valtra (Grupo Parvi)")

    # Barra de Ações Rápidas no Topo
    col_sync, col_info = st.columns([1, 4])
    with col_sync:
        if st.button("🔄 Sincronizar Planilha", use_container_width=True):
            sincronizar_excel_com_db()
            st.toast("Base sincronizada com sucesso!")
            st.rerun()

    df = carregar_dados_gestao()
    if df.empty:
        st.warning("Nenhuma Ordem de Serviço encontrada no banco de dados. Clique em 'Sincronizar Planilha'.")
        return

    df = calcular_criticidade_e_prazos(df)

    # Filtros Globais por Unidade / Filial
    st.sidebar.subheader("🎯 Filtros de Operação")
    filiais_disponiveis = ["Todas"] + list(df["Operacao"].dropna().unique())
    filial_selecionada = st.sidebar.selectbox("Filial / Unidade", filiais_disponiveis)

    if filial_selecionada != "Todas":
        df = df[df["Operacao"] == filial_selecionada]

    # Abas Principais do Escopo
    aba_painel, aba_carteira, aba_processos, aba_pecas, aba_fabrica, aba_consultor = st.tabs([
        "🚦 1. Painel da Coordenadora",
        "📋 2. Carteira Completa de O.S.",
        "⏱️ 3. Controle de Processos & Prazos",
        "📦 4. Controle de Peças & B.O.",
        "💰 5. Controle Fábrica & Dinheiro Parado",
        "👥 6. Performance da Carteira"
    ])

    with aba_painel:
        st.subheader("🔴 Atenção da Coordenadora Hoje")
        
        # KPIs de Saúde por Filial
        c1, c2, c3, c4, c5 = st.columns(5)
        criticas = len(df[df["Semáforo_Prazo"] == "🔴 Crítico (>60d)"])
        atencao = len(df[df["Semáforo_Prazo"] == "🟡 Atenção"])
        bo_pecas = len(df[df.get("Peca_BO", "") == "Sim"])
        em_fabrica = len(df[df.get("Status_Garantia", "") == "Em análise fábrica"])
        saldo_parado = df["Valor_Liquido"].sum()

        c1.metric("🔴 O.S. Críticas (>60d)", f"{criticas} O.S.")
        c2.metric("🟡 Alerta (30 a 60 dias)", f"{atencao} O.S.")
        c3.metric("📦 Peças em B.O.", f"{bo_pecas} O.S.")
        c4.metric("🏭 Em Análise Fábrica", f"{em_fabrica} O.S.")
        c5.metric("💵 Saldo Total Parado", fmt_brl(saldo_parado))

        st.divider()

        # Bloco de 10 Ações Prioritárias da Coordenadora (Regra de Ouro / Pendências)
        st.markdown("### ⚡ Top Ações Prioritárias para a Coordenadora")
        df_pendentes = df[
            (df["Gargalo_Atual"] != "") | 
            (df["Proxima_Acao"] == "") | 
            (df["Semáforo_Prazo"].isin(["🔴 Crítico (>60d)", "🟡 Atenção"]))
        ].head(10)

        if not df_pendentes.empty:
            st.dataframe(
                df_pendentes[[
                    "Numero", "Operacao", "Cliente", "Modelo", "Dias_Aberto_OS", 
                    "Semáforo_Prazo", "Gargalo_Atual", "Proxima_Acao", "Responsavel"
                ]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("🎉 Todas as O.S. estão em dia sem gargalos pendentes!")

    with aba_carteira:
        st.subheader("📋 Carteira Completa de Ordens de Serviço (Regra de Ouro)")
        st.info("⚠️ Regra de Ouro: Toda O.S. deve conter obrigatoriamente: Status Atual, Gargalo, Responsável, Próxima Ação e Prazo.")

        # Selecionar O.S. para editar
        lista_os = df["Numero"].tolist()
        os_selecionada = st.selectbox("Selecione o Nº da O.S. para Atualizar", lista_os)

        os_row = df[df["Numero"] == os_selecionada].iloc[0]

        with st.form("form_atualizar_os"):
            cols = st.columns(3)
            with cols[0]:
                status_atual = st.selectbox(
                    "Status da Garantia",
                    ["Aberta na Oficina", "Aguardando Peças", "Aguardando Atendimento", "Aguardando Submissão", "Em análise fábrica", "Aprovada", "Rejeitada", "Faturada"],
                    index=["Aberta na Oficina", "Aguardando Peças", "Aguardando Atendimento", "Aguardando Submissão", "Em análise fábrica", "Aprovada", "Rejeitada", "Faturada"].index(os_row.get("Status_Garantia", "Aberta na Oficina")) if os_row.get("Status_Garantia") in ["Aberta na Oficina", "Aguardando Peças", "Aguardando Atendimento", "Aguardando Submissão", "Em análise fábrica", "Aprovada", "Rejeitada", "Faturada"] else 0
                )
                gargalo = st.selectbox(
                    "Gargalo Atual",
                    ["", "Peça", "Fábrica", "Serviço", "Administrativo"],
                    index=["", "Peça", "Fábrica", "Serviço", "Administrativo"].index(os_row.get("Gargalo_Atual", "")) if os_row.get("Gargalo_Atual") in ["", "Peça", "Fábrica", "Serviço", "Administrativo"] else 0
                )
            with cols[1]:
                responsavel = st.text_input("Responsável pela Ação", value=os_row.get("Responsavel", ""))
                proxima_acao = st.text_input("Próxima Ação", value=os_row.get("Proxima_Acao", ""))
            with cols[2]:
                prazo_acao = st.text_input("Prazo da Próxima Ação (DD/MM/AAAA)", value=os_row.get("Prazo_Acao", ""))
                aol_proto = st.text_input("Nº Protocolo AOL / Fábrica", value=os_row.get("AOL_Protocolo", ""))

            obs = st.text_area("Observações / Justificativas", value=os_row.get("Observacoes", ""))

            btn_salvar = st.form_submit_button("💾 Salvar Atualização da O.S.", use_container_width=True)
            if btn_salvar:
                atualizar_os_completa(os_selecionada, {
                    "Status_Garantia": status_atual,
                    "Gargalo_Atual": gargalo,
                    "Responsavel": responsavel,
                    "Proxima_Acao": proxima_acao,
                    "Prazo_Acao": prazo_acao,
                    "AOL_Protocolo": aol_proto,
                    "Observacoes": obs
                })
                st.success(f"O.S. {os_selecionada} atualizada com sucesso!")
                st.rerun()

        st.dataframe(df, use_container_width=True, hide_index=True)

    with aba_processos:
        st.subheader("⏱️ Controle de Prazos (Manual de Garantia: 30d O.S. / 60d FleetScan)")
        st.dataframe(
            df[["Numero", "Cliente", "Modelo", "Emissao", "Dias_Aberto_OS", "Semáforo_Prazo", "Status_Garantia"]],
            use_container_width=True,
            hide_index=True
        )

    with aba_pecas:
        st.subheader("📦 Controle de Peças Pendentes & B.O.")
        df_pecas = df[df.get("Necessita_Peca", "Não") == "Sim"]
        if df_pecas.empty:
            st.info("Nenhuma peça pendente registrada.")
        else:
            st.dataframe(df_pecas[["Numero", "Cliente", "Pedido_Peca", "Data_Pedido_Peca", "Previsao_Peca", "Peca_BO"]], use_container_width=True)

    with aba_fabrica:
        st.subheader("💰 Controle Fábrica & Dinheiro Parado")
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("Valor Solicitado", fmt_brl(df["Valor_Solicitado"].sum() if "Valor_Solicitado" in df else 0))
        col_f2.metric("Valor Aprovado", fmt_brl(df["Valor_Aprovado"].sum() if "Valor_Aprovado" in df else 0))
        col_f3.metric("Valor Faturado", fmt_brl(df["Valor_Faturado"].sum() if "Valor_Faturado" in df else 0))

    with aba_consultor:
        st.subheader("👥 Performance por Consultora / Estagiária")
        st.dataframe(
            df.groupby("Consultor_Responsavel", dropna=False)["Numero"].count().reset_index(name="Total O.S."),
            use_container_width=True
        )
