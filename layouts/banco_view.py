import pandas as pd
import streamlit as st

from core.database import get_conn, listar_frentes_servico
from core.helpers import safe_int, formatar_iso_para_datahora


def render_banco_view(modo_comando):
    if modo_comando:
        return

    with st.expander("Visualizar banco de dados", expanded=False):
        aba1, aba2, aba3, aba4, aba5 = st.tabs(
            [
                "Lançamentos diários",
                "Parâmetros diários",
                "Cadastro de frentes",
                "Status diário das frentes",
                "Resumo do banco",
            ]
        )

        with aba1:
            with get_conn() as conn:
                anos_db = pd.read_sql_query(
                    "SELECT DISTINCT ano FROM lancamentos_diarios ORDER BY ano DESC",
                    conn,
                )["ano"].tolist()

                if len(anos_db) == 0:
                    st.info("Nenhum lançamento registrado ainda.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        ano_filtro = st.selectbox("Ano", anos_db, key="db_ano_filtro")

                    meses_db = pd.read_sql_query(
                        "SELECT DISTINCT mes FROM lancamentos_diarios WHERE ano = ? ORDER BY mes",
                        conn,
                        params=(ano_filtro,),
                    )["mes"].tolist()

                    with col2:
                        mes_filtro = st.selectbox("Mês", meses_db, key="db_mes_filtro")

                    df_db = pd.read_sql_query(
                        """
                        SELECT
                            ano AS Ano,
                            mes AS Mes,
                            dia AS Dia,
                            chuva_mm AS 'Chuva (mm)',
                            servico_principal AS 'Serviço principal',
                            impacto_obra AS 'Impacto na obra',
                            observacao AS Observação,
                            atualizado_em AS Atualizado
                        FROM lancamentos_diarios
                        WHERE ano = ? AND mes = ?
                        ORDER BY dia
                        """,
                        conn,
                        params=(ano_filtro, mes_filtro),
                    )

                    if not df_db.empty:
                        df_db["Data"] = df_db.apply(
                            lambda row: f"{safe_int(row['Dia']):02d}/{safe_int(row['Mes']):02d}/{safe_int(row['Ano']) % 100:02d}",
                            axis=1,
                        )
                        df_db["Atualizado"] = df_db["Atualizado"].apply(formatar_iso_para_datahora)
                        df_db = df_db[
                            ["Data", "Chuva (mm)", "Serviço principal", "Impacto na obra", "Observação", "Atualizado"]
                        ]

                    st.dataframe(df_db, use_container_width=True, hide_index=True)

        with aba2:
            with get_conn() as conn:
                df_param = pd.read_sql_query(
                    """
                    SELECT
                        ano AS Ano,
                        mes AS Mes,
                        dia AS Dia,
                        drenagem AS Drenagem,
                        evidencia_campo AS 'Evidência de campo',
                        atualizado_em AS Atualizado
                    FROM parametros_diarios
                    ORDER BY ano DESC, mes DESC, dia DESC
                    """,
                    conn,
                )

                if df_param.empty:
                    st.info("Nenhum parâmetro diário registrado.")
                else:
                    df_param["Data"] = df_param.apply(
                        lambda row: f"{safe_int(row['Dia']):02d}/{safe_int(row['Mes']):02d}/{safe_int(row['Ano']) % 100:02d}",
                        axis=1,
                    )
                    df_param["Atualizado"] = df_param["Atualizado"].apply(formatar_iso_para_datahora)
                    df_param = df_param[
                        ["Data", "Drenagem", "Evidência de campo", "Atualizado"]
                    ]
                    st.dataframe(df_param, use_container_width=True, hide_index=True)

        with aba3:
            df_frentes_view = listar_frentes_servico()
            if df_frentes_view.empty:
                st.info("Nenhuma frente cadastrada.")
            else:
                st.dataframe(
                    df_frentes_view.drop(columns=["id"]),
                    use_container_width=True,
                    hide_index=True,
                )

        with aba4:
            with get_conn() as conn:
                df_status = pd.read_sql_query(
                    """
                    SELECT
                        s.ano AS Ano,
                        s.mes AS Mes,
                        s.dia AS Dia,
                        f.nome AS Frente,
                        s.status_frente AS Status,
                        COALESCE(s.observacao_frente, '') AS Observação,
                        s.atualizado_em AS Atualizado
                    FROM status_frentes_diario s
                    JOIN frentes_servico f ON f.id = s.frente_id
                    ORDER BY s.ano DESC, s.mes DESC, s.dia DESC, f.nome
                    """,
                    conn,
                )

                if df_status.empty:
                    st.info("Nenhum status diário de frente registrado.")
                else:
                    df_status["Data"] = df_status.apply(
                        lambda row: f"{safe_int(row['Dia']):02d}/{safe_int(row['Mes']):02d}/{safe_int(row['Ano']) % 100:02d}",
                        axis=1,
                    )
                    df_status["Atualizado"] = df_status["Atualizado"].apply(formatar_iso_para_datahora)
                    df_status = df_status[
                        ["Data", "Frente", "Status", "Observação", "Atualizado"]
                    ]
                    st.dataframe(df_status, use_container_width=True, hide_index=True)

        with aba5:
            with get_conn() as conn:
                total_lanc = pd.read_sql_query(
                    "SELECT COUNT(*) AS total FROM lancamentos_diarios",
                    conn,
                )["total"][0]

                total_param = pd.read_sql_query(
                    "SELECT COUNT(*) AS total FROM parametros_diarios",
                    conn,
                )["total"][0]

                total_frentes = pd.read_sql_query(
                    "SELECT COUNT(*) AS total FROM frentes_servico",
                    conn,
                )["total"][0]

                total_status = pd.read_sql_query(
                    "SELECT COUNT(*) AS total FROM status_frentes_diario",
                    conn,
                )["total"][0]

                meses_reg = pd.read_sql_query(
                    "SELECT COUNT(DISTINCT ano || '-' || mes) AS total FROM lancamentos_diarios",
                    conn,
                )["total"][0]

                ultimo_update = pd.read_sql_query(
                    """
                    SELECT MAX(atualizado_em) AS ultimo
                    FROM (
                        SELECT atualizado_em FROM lancamentos_diarios
                        UNION
                        SELECT atualizado_em FROM parametros_diarios
                        UNION
                        SELECT atualizado_em FROM status_frentes_diario
                    )
                    """,
                    conn,
                )["ultimo"][0]

                resumo = pd.DataFrame(
                    {
                        "Indicador": [
                            "Total de lançamentos diários",
                            "Parâmetros diários registrados",
                            "Frentes cadastradas",
                            "Status diários de frentes",
                            "Meses registrados",
                            "Última atualização",
                        ],
                        "Valor": [
                            total_lanc,
                            total_param,
                            total_frentes,
                            total_status,
                            meses_reg,
                            formatar_iso_para_datahora(ultimo_update),
                        ],
                    }
                )

                st.dataframe(resumo, use_container_width=True, hide_index=True)