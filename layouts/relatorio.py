import streamlit as st

from core.relatorios import gerar_relatorio_pdf_bytes


def render_relatorio(ano, mes, resumo_pdf, parecer, previsao_df, permitir_download=True):
    st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Relatório oficial</div>", unsafe_allow_html=True)

    if not permitir_download:
        st.info("Download do relatório PDF disponível apenas para administrador.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    pdf_bytes = gerar_relatorio_pdf_bytes(ano, mes, resumo_pdf, parecer, previsao_df)

    if pdf_bytes is None:
        st.warning("Para gerar PDF, instale a biblioteca reportlab: python -m pip install reportlab")
    else:
        st.download_button(
            "Baixar relatório PDF oficial",
            data=pdf_bytes,
            file_name=f"relatorio_meteorologico_{ano}_{mes:02d}.pdf",
            mime="application/pdf",
        )

    st.markdown("</div>", unsafe_allow_html=True)