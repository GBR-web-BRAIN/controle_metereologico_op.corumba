import streamlit as st

from core.clima import descricao_tempo, recomendacao_operacional
from ui.components import forecast_card_html


def render_previsao(previsao_df):
    st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Previsão meteorológica para próximos dias</div>", unsafe_allow_html=True)

    if previsao_df.empty:
        st.warning("Não foi possível carregar a previsão do tempo no momento.")
    else:
        preview = previsao_df.copy()
        preview["Condição"] = preview["Código"].apply(descricao_tempo)

        if "Decisão" not in preview.columns:
            preview[["Decisão", "Orientação", "Classe"]] = preview.apply(
                lambda row: __import__("pandas").Series(
                    recomendacao_operacional(row["Chuva Prevista (mm)"], row["Condição"])
                ),
                axis=1,
            )

        primeira_linha = preview.head(4)
        cols = st.columns(len(primeira_linha))

        for i, (_, row) in enumerate(primeira_linha.iterrows()):
            with cols[i]:
                st.markdown(
                    forecast_card_html(
                        row["Data_fmt"],
                        row["Código"],
                        row["Chuva Prevista (mm)"],
                        row["Condição"],
                        row["Temp. Máx (°C)"],
                        row["Temp. Mín (°C)"],
                        row["Decisão"],
                    ),
                    unsafe_allow_html=True,
                )

        restante = preview.iloc[4:7]
        if not restante.empty:
            cols2 = st.columns(len(restante))
            for j, (_, row) in enumerate(restante.iterrows()):
                with cols2[j]:
                    st.markdown(
                        forecast_card_html(
                            row["Data_fmt"],
                            row["Código"],
                            row["Chuva Prevista (mm)"],
                            row["Condição"],
                            row["Temp. Máx (°C)"],
                            row["Temp. Mín (°C)"],
                            row["Decisão"],
                        ),
                        unsafe_allow_html=True,
                    )

    st.markdown("</div>", unsafe_allow_html=True)