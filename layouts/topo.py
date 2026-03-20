import streamlit as st

from config import APP_TITLE
from core.helpers import formatar_datahora_local
from ui.components import (
    command_mini_card_html,
    alerta_meteo_card_html,
    alerta_piscando_html,
)


def render_saida_modo_comando(modo_comando):
    if modo_comando:
        col_exit_1, col_exit_2 = st.columns([1.2, 8])
        with col_exit_1:
            if st.button("Sair da sala de comando", use_container_width=True):
                st.session_state.modo_exibicao = "Operacional"
                st.rerun()


def render_topo(
    modo_comando,
    alerta_auto,
    decisao_titulo,
    decisao_texto,
    decisao_tipo,
    condicao_operacional,
    tendencia_72h,
    dot_class,
):
    modo_texto = "SALA DE COMANDO / TV" if modo_comando else "OPERAÇÃO INTERATIVA"

    st.markdown(
        f"""
        <div class="main-command-box">
            <div class="command-kicker">Centro de Operações · {modo_texto}</div>
            <div class="command-title">{APP_TITLE}</div>
            <div class="command-subtitle">
                Acompanhamento meteorológico, leitura operacional de campo, radar em tempo real, mapa por frentes de serviço e apoio à decisão ·
                Atualizado em {formatar_datahora_local()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if alerta_auto["nivel"] == "CRITICO":
        hora_alerta_piscando = (
            alerta_auto["hora_critica"].strftime("%H:%M")
            if alerta_auto.get("hora_critica") is not None
            else "-"
        )
        st.markdown(alerta_piscando_html(hora_alerta_piscando), unsafe_allow_html=True)

    topo1, topo2 = st.columns([1, 1])

    with topo1:
        st.markdown(
            command_mini_card_html(
                decisao_titulo=decisao_titulo,
                condicao_operacional=condicao_operacional,
                tendencia_72h=tendencia_72h,
                dot_class=dot_class,
            ),
            unsafe_allow_html=True,
        )

    with topo2:
        hora_alerta_ref = (
            alerta_auto["hora_critica"].strftime("%H:%M")
            if alerta_auto.get("hora_critica") is not None
            else "-"
        )
        st.markdown(
            alerta_meteo_card_html(
                titulo=alerta_auto["titulo"],
                mensagem=alerta_auto["mensagem"],
                nivel=alerta_auto["nivel"],
                pico_prob=alerta_auto.get("pico_prob", 0.0),
                pico_chuva=alerta_auto.get("pico_chuva", 0.0),
                pico_precip=alerta_auto.get("pico_precip", 0.0),
                hora_ref=hora_alerta_ref,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("### Decisão operacional recomendada")

    mensagem_decisao = f"""
Situação: **{decisao_titulo}**

{decisao_texto}
"""

    if decisao_tipo == "error":
        st.markdown(
            f"<div class='alerta-piscando'>{mensagem_decisao}</div>",
            unsafe_allow_html=True
        )
    elif decisao_tipo == "warning":
        st.warning(mensagem_decisao)
    elif decisao_tipo == "info":
        st.info(mensagem_decisao)
    else:
        st.success(mensagem_decisao)

    if alerta_auto["nivel"] == "CRITICO":
        st.error("🚨 Alerta automático: chuva forte aproximando da obra.")
    elif alerta_auto["nivel"] == "ATENCAO":
        st.warning("⚠️ Alerta automático: possibilidade relevante de precipitação nas próximas horas.")
    elif alerta_auto["nivel"] == "NORMAL":
        st.success("✅ Alerta automático: sem aproximação crítica de chuva na janela monitorada.")
    else:
        st.info("ℹ️ Alerta automático: leitura momentaneamente indisponível.")