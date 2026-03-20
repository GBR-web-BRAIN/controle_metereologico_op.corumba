import streamlit as st

from ui.components import metric_card_html
from ui.charts import build_pluviometrico_chart


def render_painel_principal(
    df,
    total,
    maximo,
    dias_chuva,
    modo_comando,
    icon_gota,
    icon_chuva,
    icon_cal,
):
    col_esq, col_dir = st.columns([2.1, 1])

    with col_esq:
        st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>Painel pluviométrico</div>", unsafe_allow_html=True)

        cards_topo_grafico = st.columns(3)

        with cards_topo_grafico[0]:
            st.markdown(
                metric_card_html(
                    icon_gota,
                    "Total do mês",
                    f"{total:.0f} mm",
                    "Precipitação acumulada no período monitorado.",
                ),
                unsafe_allow_html=True,
            )

        with cards_topo_grafico[1]:
            st.markdown(
                metric_card_html(
                    icon_chuva,
                    "Maior chuva",
                    f"{maximo:.0f} mm",
                    "Maior evento diário registrado na janela atual.",
                ),
                unsafe_allow_html=True,
            )

        with cards_topo_grafico[2]:
            st.markdown(
                metric_card_html(
                    icon_cal,
                    "Dias com chuva",
                    f"{dias_chuva}",
                    "Quantidade de dias com precipitação acima de zero.",
                ),
                unsafe_allow_html=True,
            )

        fig = build_pluviometrico_chart(df.copy(), maximo, modo_comando)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("</div>", unsafe_allow_html=True)

    return col_dir