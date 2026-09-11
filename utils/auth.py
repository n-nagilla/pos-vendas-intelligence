import streamlit as st
import hmac

def autenticar():
    """
    Bloqueia a execução da página enquanto o usuário não estiver autenticado.
    Retorna True se estiver autenticado, ou interrompe o Streamlit com st.stop().
    """
    if st.session_state.get("usuario_autenticado", False):
        # Exibe um botão discreto de Logout no menu lateral
        with st.sidebar:
            st.markdown(f"👤 **Logado como:** `{st.session_state.get('usuario_ativo', 'Usuário')}`")
            if st.button("🚪 Sair (Logout)"):
                st.session_state["usuario_autenticado"] = False
                st.session_state["usuario_ativo"] = None
                st.rerun()
        return True

    # Formulário visual de Login centralizado
    col_vazia1, col_login, col_vazia2 = st.columns([1, 1.2, 1])

    with col_login:
        st.markdown("### 🔒 Acesso Restrito")
        st.caption("Pós-Vendas Intelligence | Mardisa Agro")

        with st.form("form_login"):
            usuario = st.text_input("Usuário").strip()
            senha = st.text_input("Senha", type="password").strip()
            entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)

            if entrar:
                senhas_validas = st.secrets.get("passwords", {})
                if (
                    usuario in senhas_validas
                    and hmac.compare_digest(senha, str(senhas_validas[usuario]))
                ):
                    st.session_state["usuario_autenticado"] = True
                    st.session_state["usuario_ativo"] = usuario
                    st.success("✅ Acesso autorizado! Carregando...")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

    # Interrompe qualquer código abaixo de ser renderizado
    st.stop()
