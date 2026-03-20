import streamlit as st

from core.helpers import safe_int


def render_observacoes(modo_comando, df, df_frentes_mapa, ano, mes):
    if modo_comando:
        return

    st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Observações de campo</div>", unsafe_allow_html=True)

    with st.expander("Abrir observações gerais", expanded=False):
        obs = df[
            df["Observação"].fillna("").astype(str).str.strip() != ""
        ][["Dia", "Serviço principal", "Observação"]].copy()

        if len(obs) == 0:
            st.info("Sem observações registradas.")
        else:
            obs["Data"] = obs["Dia"].apply(lambda x: f"{safe_int(x):02d}/{safe_int(mes):02d}/{safe_int(ano) % 100:02d}")
            obs = obs[["Data", "Serviço principal", "Observação"]]
            st.dataframe(obs, use_container_width=True, hide_index=True)

    with st.expander("Abrir observações das frentes", expanded=False):
        if df_frentes_mapa.empty:
            st.info("Nenhuma frente cadastrada.")
        else:
            obs_frentes = df_frentes_mapa.copy()
            obs_frentes = obs_frentes[obs_frentes["Observação da frente"].astype(str).str.strip() != ""]
            if obs_frentes.empty:
                st.info("Sem observações de frentes registradas para o dia selecionado.")
            else:
                exibir = obs_frentes[["Nome", "Status do dia", "Observação da frente", "Atualizado"]]
                exibir.columns = ["Frente", "Status", "Observação", "Atualizado em"]
                st.dataframe(exibir, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)