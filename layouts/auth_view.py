import streamlit as st

from core.auth import (
    autenticar_usuario,
    iniciar_sessao_usuario,
    encerrar_sessao_usuario,
    obter_usuario_logado,
)


def render_login():
    st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Acesso ao sistema</div>", unsafe_allow_html=True)

    col_esq, col_ctr, col_dir = st.columns([1.1, 1.8, 1.1])

    with col_ctr:
        st.markdown(
            """
            <div class="main-command-box">
                <div class="command-kicker">Sistema protegido</div>
                <div class="command-title">CONTROLE METEOROLÓGICO</div>
                <div class="command-subtitle">
                    Acesso restrito por autenticação. Administradores podem lançar, cadastrar e gerenciar usuários.
                    Visitantes possuem consulta em modo leitura.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="command-mini-card">
                <div class="command-mini-label">Login</div>
                <div class="command-mini-line">
                    Use suas credenciais para entrar no painel operacional.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_login"):
            username = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar no sistema", use_container_width=True)

        if entrar:
            usuario = autenticar_usuario(username, senha)
            if usuario:
                iniciar_sessao_usuario(usuario)
                st.success(f"Acesso liberado para {usuario['nome']}.")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos, ou conta inativa.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_usuario_logado_sidebar():
    usuario = obter_usuario_logado()
    if not usuario:
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Sessão ativa")
    st.sidebar.write(f"**Nome:** {usuario['nome']}")
    st.sidebar.write(f"**Usuário:** {usuario['username']}")
    st.sidebar.write(f"**Perfil:** {usuario['perfil'].capitalize()}")

    if usuario["perfil"] == "admin":
        st.sidebar.success("Permissões administrativas liberadas.")
    else:
        st.sidebar.info("Perfil visitante: leitura somente.")

    if st.sidebar.button("Sair do sistema", use_container_width=True):
        encerrar_sessao_usuario()
        st.rerun()