import pandas as pd
import streamlit as st

from ui.components import front_card_html


def render_inteligencia_frentes(modo_comando, frentes_inteligentes):
    st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Inteligência das frentes de serviço</div>", unsafe_allow_html=True)

    resumo_frentes_df = pd.DataFrame(
        [
            {
                "Frente": item["nome"],
                "Status do dia": item["status"],
                "Risco automático": item["risco_auto"],
                "Impacto provável": item["impacto"],
                "Recomendação": item["recomendacao"],
            }
            for item in frentes_inteligentes
        ]
    )

    if modo_comando:
        col_tr1, col_tr2 = st.columns([1.15, 1])

        with col_tr1:
            if not frentes_inteligentes:
                st.info("Nenhuma frente cadastrada.")
            else:
                for item in frentes_inteligentes:
                    st.markdown(
                        front_card_html(
                            nome=item["nome"],
                            status=item["status"],
                            impacto=item["impacto"],
                            recomendacao=item["recomendacao"],
                            risco_auto=item["risco_auto"],
                        ),
                        unsafe_allow_html=True,
                    )

        with col_tr2:
            st.markdown("#### Quadro resumido")
            if resumo_frentes_df.empty:
                st.info("Nenhuma frente cadastrada.")
            else:
                st.dataframe(resumo_frentes_df, use_container_width=True, hide_index=True)
    else:
        with st.expander("Abrir inteligência das frentes", expanded=False):
            col_tr1, col_tr2 = st.columns([1.15, 1])

            with col_tr1:
                if not frentes_inteligentes:
                    st.info("Nenhuma frente cadastrada.")
                else:
                    for item in frentes_inteligentes:
                        st.markdown(
                            front_card_html(
                                nome=item["nome"],
                                status=item["status"],
                                impacto=item["impacto"],
                                recomendacao=item["recomendacao"],
                                risco_auto=item["risco_auto"],
                            ),
                            unsafe_allow_html=True,
                        )

            with col_tr2:
                st.markdown("#### Quadro resumido")
                if resumo_frentes_df.empty:
                    st.info("Nenhuma frente cadastrada.")
                else:
                    st.dataframe(resumo_frentes_df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)