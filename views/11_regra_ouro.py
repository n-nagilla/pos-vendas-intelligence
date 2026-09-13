import streamlit as st
from data.db_manager import atualizar_os_completa

def render(df):
    st.subheader("⚠️ Regra de Ouro — Validação de O.S. Sem Controle")
    st.warning("Toda O.S. aberta obrigatoriamente precisa ter: Status Atual, Gargalo, Responsável, Próxima Ação e Data da Próxima Ação.")
    
    if df.empty or "Numero" not in df.columns:
        st.info("Nenhuma Ordem de Serviço disponível para validação.")
        return

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
