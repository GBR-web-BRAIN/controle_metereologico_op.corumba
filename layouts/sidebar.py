import sqlite3
import pandas as pd
import streamlit as st

from config import (
    APP_TITLE,
    LAT_OBRA,
    LON_OBRA,
    SERVICOS,
    IMPACTOS,
    TIPOS_DRENAGEM,
    TIPOS_EVIDENCIA,
    STATUS_FRENTE,
)
from core.helpers import safe_float, safe_int
from core.database import (
    criar_backup_banco,
    carregar_parametros_dia,
    salvar_parametros_dia,
    listar_frentes_servico,
    salvar_frente_servico,
    excluir_frente_servico,
    carregar_status_frentes_dia,
    salvar_lancamento_diario,
    salvar_status_frente_dia,
    gerar_mes,
    excluir_mes,
    carregar_lancamentos_mes,
)
from core.operacao import obter_ultimo_dia_referencia
from core.auth import (
    criar_usuario,
    listar_usuarios,
    alterar_status_usuario,
    redefinir_senha_usuario,
    alterar_senha_proprio_usuario,
    usuario_e_admin,
)


def init_modo_exibicao():
    if "modo_exibicao" not in st.session_state:
        st.session_state.modo_exibicao = "Operacional"


def on_change_modo_exibicao():
    st.session_state.modo_exibicao = st.session_state.modo_exibicao_radio


def render_modo_selector(usuario_logado=None):
    opcoes = ["Operacional", "Sala de Comando"]

    if usuario_logado and usuario_logado.get("perfil") != "admin":
        st.sidebar.radio(
            "Modo do painel",
            opcoes,
            key="modo_exibicao_radio",
            index=1 if st.session_state.modo_exibicao == "Sala de Comando" else 0,
            disabled=True,
        )
        st.session_state.modo_exibicao = "Sala de Comando"
        return True

    st.sidebar.radio(
        "Modo do painel",
        opcoes,
        key="modo_exibicao_radio",
        index=0 if st.session_state.modo_exibicao == "Operacional" else 1,
        on_change=on_change_modo_exibicao,
    )
    return st.session_state.modo_exibicao == "Sala de Comando"


def init_periodo_sessao(ano_padrao, mes_padrao):
    if "ano_atual" not in st.session_state:
        st.session_state.ano_atual = ano_padrao

    if "mes_atual" not in st.session_state:
        st.session_state.mes_atual = mes_padrao

    if "df" not in st.session_state:
        st.session_state.df = carregar_lancamentos_mes(
            st.session_state.ano_atual,
            st.session_state.mes_atual,
        )


def _render_seletor_periodo(titulo="Controle operacional"):
    st.sidebar.title(titulo)
    st.sidebar.caption(APP_TITLE)

    ano = st.sidebar.number_input(
        "Ano",
        min_value=2020,
        max_value=2100,
        value=st.session_state.ano_atual,
        step=1,
    )
    mes = st.sidebar.number_input(
        "Mês",
        min_value=1,
        max_value=12,
        value=st.session_state.mes_atual,
        step=1,
    )

    if (ano != st.session_state.ano_atual) or (mes != st.session_state.mes_atual):
        st.session_state.ano_atual = ano
        st.session_state.mes_atual = mes
        st.session_state.df = carregar_lancamentos_mes(ano, mes)
        st.rerun()

    col_btn1, col_btn2 = st.sidebar.columns(2)

    with col_btn1:
        if st.button("Carregar mês", use_container_width=True):
            st.session_state.df = carregar_lancamentos_mes(ano, mes)
            st.rerun()

    with col_btn2:
        if st.button("Atualizar tela", use_container_width=True):
            st.rerun()

    return ano, mes


def _montar_contexto_basico(ano, mes):
    df_sidebar = st.session_state.df.copy()
    dia_selecionado = st.sidebar.selectbox(
        "Selecionar dia",
        options=df_sidebar["Dia"].tolist(),
    )

    parametros_dia = carregar_parametros_dia(ano, mes, safe_int(dia_selecionado))
    drenagem = parametros_dia["drenagem"]
    evidencia_campo = parametros_dia["evidencia_campo"]

    chuva_sidebar = pd.to_numeric(st.session_state.df["Chuva (mm)"], errors="coerce")
    total_sidebar = safe_float(chuva_sidebar.fillna(0).sum())
    max_sidebar = safe_float(chuva_sidebar.fillna(0).max())
    dias_sidebar = safe_int((chuva_sidebar.fillna(0) > 0).sum())

    st.sidebar.metric("Total do mês", f"{total_sidebar:.0f} mm")
    st.sidebar.metric("Maior chuva", f"{max_sidebar:.0f} mm")
    st.sidebar.metric("Dias com chuva", f"{dias_sidebar}")

    return {
        "ano": ano,
        "mes": mes,
        "drenagem": drenagem,
        "evidencia_campo": evidencia_campo,
        "dia_selecionado": dia_selecionado,
        "df_frentes_sidebar": listar_frentes_servico(),
    }


def render_sidebar_visitante(usuario_logado=None):
    ano, mes = _render_seletor_periodo("Consulta operacional")
    contexto = _montar_contexto_basico(ano, mes)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Consulta do dia")
    st.sidebar.write(f"**Drenagem:** {contexto['drenagem']}")
    st.sidebar.write(f"**Evidência de campo:** {contexto['evidencia_campo']}")

    st.sidebar.warning(
        "Modo visitante ativo. Este perfil não pode cadastrar frentes, salvar lançamentos, "
        "excluir dados, criar backups nem administrar usuários."
    )

    return contexto


def render_sidebar_operacional(usuario_logado=None):
    if not usuario_e_admin(usuario_logado):
        return render_sidebar_visitante(usuario_logado)

    ano, mes = _render_seletor_periodo("Controle operacional")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Segurança da conta")

    with st.sidebar.expander("Trocar minha senha", expanded=False):
        with st.form("form_trocar_senha_admin"):
            senha_atual = st.text_input("Senha atual", type="password")
            nova_senha = st.text_input("Nova senha", type="password")
            confirmar_nova_senha = st.text_input("Confirmar nova senha", type="password")
            trocar = st.form_submit_button("Salvar nova senha", use_container_width=True)

        if trocar:
            try:
                alterar_senha_proprio_usuario(
                    user_id=int(usuario_logado["id"]),
                    senha_atual=senha_atual,
                    nova_senha=nova_senha,
                    confirmar_nova_senha=confirmar_nova_senha,
                )
                st.sidebar.success("Sua senha foi alterada com sucesso.")
                st.rerun()
            except Exception as e:
                st.sidebar.error(str(e))

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Administração do mês")

    col_btn_limpar_1, col_btn_limpar_2 = st.sidebar.columns(2)
    with col_btn_limpar_1:
        if st.button("Limpar mês", use_container_width=True):
            excluir_mes(ano, mes)
            st.session_state.df = gerar_mes(ano, mes)
            st.success(f"Dados de {mes:02d}/{ano} removidos.")
            st.rerun()

    with col_btn_limpar_2:
        if st.button("Backup agora", use_container_width=True):
            arquivo_backup = criar_backup_banco()
            if arquivo_backup:
                st.sidebar.success(f"Backup criado: {arquivo_backup.name}")
            else:
                st.sidebar.error("Não foi possível criar o backup.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Gestão de usuários")

    with st.sidebar.expander("Cadastrar visitante", expanded=False):
        with st.form("form_novo_visitante"):
            nome_usuario = st.text_input("Nome completo")
            username_usuario = st.text_input("Usuário de acesso")
            senha_usuario = st.text_input("Senha inicial", type="password")
            criar = st.form_submit_button("Criar visitante")

        if criar:
            try:
                criar_usuario(
                    nome=nome_usuario,
                    username=username_usuario,
                    senha=senha_usuario,
                    perfil="visitante",
                )
                st.sidebar.success("Visitante criado com sucesso.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.sidebar.error("Já existe um usuário com esse login.")
            except ValueError as e:
                st.sidebar.error(str(e))
            except Exception as e:
                st.sidebar.error(f"Falha ao criar usuário: {e}")

    df_usuarios = listar_usuarios()
    if not df_usuarios.empty:
        with st.sidebar.expander("Gerenciar usuários", expanded=False):
            st.dataframe(
                df_usuarios.drop(columns=["id"], errors="ignore"),
                use_container_width=True,
                hide_index=True,
            )

            visitantes_df = df_usuarios[df_usuarios["Perfil"] == "visitante"].copy()
            if visitantes_df.empty:
                st.info("Nenhum visitante cadastrado.")
            else:
                mapa_visitantes = {
                    f"{row['Nome']} ({row['Usuario']})": int(row["id"])
                    for _, row in visitantes_df.iterrows()
                }

                visitante_sel = st.selectbox(
                    "Selecionar visitante",
                    list(mapa_visitantes.keys()),
                    key="visitante_sel_admin",
                )
                visitante_id = mapa_visitantes[visitante_sel]

                col_user_1, col_user_2 = st.columns(2)

                with col_user_1:
                    if st.button("Desativar", use_container_width=True):
                        try:
                            alterar_status_usuario(visitante_id, False)
                            st.success("Usuário desativado.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                with col_user_2:
                    if st.button("Ativar", use_container_width=True):
                        try:
                            alterar_status_usuario(visitante_id, True)
                            st.success("Usuário ativado.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                nova_senha = st.text_input(
                    "Redefinir senha do visitante",
                    type="password",
                    key="nova_senha_visitante_admin",
                )
                if st.button("Salvar nova senha", use_container_width=True):
                    try:
                        redefinir_senha_usuario(visitante_id, nova_senha)
                        st.success("Senha redefinida com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Cadastro de frentes")

    with st.sidebar.expander("Cadastrar nova frente", expanded=False):
        with st.form("form_frente_nova"):
            nome_frente = st.text_input("Nome da frente")
            lat_frente = st.number_input("Latitude", value=LAT_OBRA, format="%.6f")
            lon_frente = st.number_input("Longitude", value=LON_OBRA, format="%.6f")
            salvar_frente = st.form_submit_button("Salvar frente")

        if salvar_frente:
            if not nome_frente.strip():
                st.sidebar.error("Informe o nome da frente.")
            else:
                try:
                    salvar_frente_servico(
                        nome=nome_frente,
                        latitude=lat_frente,
                        longitude=lon_frente,
                    )
                    st.sidebar.success("Frente cadastrada com sucesso.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.sidebar.error("Já existe uma frente com esse nome.")

    df_frentes_sidebar = listar_frentes_servico()

    if not df_frentes_sidebar.empty:
        with st.sidebar.expander("Excluir frente", expanded=False):
            opcoes_frentes = {
                f"{row['Nome']} | {row['Latitude']:.6f}, {row['Longitude']:.6f}": safe_int(row["id"])
                for _, row in df_frentes_sidebar.iterrows()
            }

            frente_selecionada_label = st.selectbox(
                "Selecionar frente",
                list(opcoes_frentes.keys()),
                key="frente_excluir_label",
            )
            frente_id_sel = opcoes_frentes[frente_selecionada_label]

            if st.button("Excluir frente selecionada", use_container_width=True):
                excluir_frente_servico(frente_id_sel)
                st.sidebar.success("Frente excluída.")
                st.rerun()

    st.sidebar.markdown("### Lançamento diário")

    df_sidebar = st.session_state.df.copy()
    dia_selecionado = st.sidebar.selectbox(
        "Selecionar dia",
        options=df_sidebar["Dia"].tolist(),
        key="dia_selecionado_admin",
    )
    linha = df_sidebar[df_sidebar["Dia"] == dia_selecionado].iloc[0]

    parametros_dia = carregar_parametros_dia(ano, mes, safe_int(dia_selecionado))
    drenagem = parametros_dia["drenagem"]
    evidencia_campo = parametros_dia["evidencia_campo"]

    with st.sidebar.expander("Parâmetros de campo do dia", expanded=False):
        drenagem = st.selectbox(
            "Drenagem",
            TIPOS_DRENAGEM,
            index=TIPOS_DRENAGEM.index(parametros_dia["drenagem"])
            if parametros_dia["drenagem"] in TIPOS_DRENAGEM
            else 1,
        )
        evidencia_campo = st.selectbox(
            "Evidência de campo",
            TIPOS_EVIDENCIA,
            index=TIPOS_EVIDENCIA.index(parametros_dia["evidencia_campo"])
            if parametros_dia["evidencia_campo"] in TIPOS_EVIDENCIA
            else 0,
        )

    salvar_parametros_dia(ano, mes, safe_int(dia_selecionado), drenagem, evidencia_campo)

    status_dia_df = carregar_status_frentes_dia(ano, mes, safe_int(dia_selecionado))
    status_dia_map = {}
    for _, row in status_dia_df.iterrows():
        status_dia_map[safe_int(row["frente_id"])] = {
            "status": row["status_frente"],
            "obs": row["observacao_frente"],
        }

    with st.sidebar.form("form_lancamento"):
        chuva_input = st.number_input(
            "Chuva do dia (mm)",
            min_value=0.0,
            value=safe_float(linha["Chuva (mm)"], 0.0),
            step=1.0,
        )

        servico_input = st.selectbox(
            "Serviço principal",
            options=SERVICOS,
            index=SERVICOS.index(linha["Serviço principal"])
            if linha["Serviço principal"] in SERVICOS
            else 0,
        )

        impacto_input = st.selectbox(
            "Impacto na obra",
            options=IMPACTOS,
            index=IMPACTOS.index(linha["Impacto na obra"])
            if linha["Impacto na obra"] in IMPACTOS
            else 0,
        )

        obs_input = st.text_area("Observação geral", value=str(linha["Observação"]), height=90)

        st.markdown("#### Situação das frentes no dia")

        frentes_form_data = {}
        if df_frentes_sidebar.empty:
            st.info("Cadastre as frentes para lançar a situação diária.")
        else:
            for _, frente in df_frentes_sidebar.iterrows():
                frente_id = safe_int(frente["id"])
                valor_atual = status_dia_map.get(frente_id, {})
                status_atual = valor_atual.get("status", "Sem atualização")
                obs_atual = valor_atual.get("obs", "")

                st.markdown(f"**{frente['Nome']}**")
                status_key = f"status_frente_{frente_id}"
                obs_key = f"obs_frente_{frente_id}"

                status_sel = st.selectbox(
                    f"Status - {frente['Nome']}",
                    STATUS_FRENTE,
                    index=STATUS_FRENTE.index(status_atual) if status_atual in STATUS_FRENTE else 0,
                    key=status_key,
                    label_visibility="collapsed",
                )
                obs_sel = st.text_area(
                    f"Observação - {frente['Nome']}",
                    value=obs_atual,
                    height=70,
                    key=obs_key,
                    label_visibility="collapsed",
                )

                frentes_form_data[frente_id] = {
                    "nome": frente["Nome"],
                    "status": status_sel,
                    "obs": obs_sel,
                }

        salvar = st.form_submit_button("Salvar lançamento diário")

    if salvar:
        idx = st.session_state.df.index[st.session_state.df["Dia"] == dia_selecionado][0]
        st.session_state.df.at[idx, "Chuva (mm)"] = safe_float(chuva_input)
        st.session_state.df.at[idx, "Serviço principal"] = servico_input
        st.session_state.df.at[idx, "Impacto na obra"] = impacto_input
        st.session_state.df.at[idx, "Observação"] = obs_input.strip()
        st.session_state.df.at[idx, "Preenchido"] = True

        salvar_lancamento_diario(
            ano=ano,
            mes=mes,
            dia=safe_int(dia_selecionado),
            chuva_mm=safe_float(chuva_input),
            servico_principal=servico_input,
            impacto_obra=impacto_input,
            observacao=obs_input.strip(),
        )

        salvar_parametros_dia(
            ano=ano,
            mes=mes,
            dia=safe_int(dia_selecionado),
            drenagem=drenagem,
            evidencia_campo=evidencia_campo,
        )

        for frente_id, dados_frente in frentes_form_data.items():
            salvar_status_frente_dia(
                ano=ano,
                mes=mes,
                dia=safe_int(dia_selecionado),
                frente_id=frente_id,
                status_frente=dados_frente["status"],
                observacao_frente=dados_frente["obs"],
            )

        st.sidebar.success(f"Lançamento do dia {dia_selecionado} salvo.")
        st.rerun()

    return {
        "ano": ano,
        "mes": mes,
        "drenagem": drenagem,
        "evidencia_campo": evidencia_campo,
        "dia_selecionado": dia_selecionado,
        "df_frentes_sidebar": df_frentes_sidebar,
    }


def get_contexto_modo_comando():
    ano = st.session_state.ano_atual
    mes = st.session_state.mes_atual

    dia_selecionado = obter_ultimo_dia_referencia(st.session_state.df.copy())
    if dia_selecionado <= 0:
        dia_selecionado = 1

    parametros_dia = carregar_parametros_dia(ano, mes, safe_int(dia_selecionado))
    drenagem = parametros_dia["drenagem"]
    evidencia_campo = parametros_dia["evidencia_campo"]
    df_frentes_sidebar = listar_frentes_servico()

    return {
        "ano": ano,
        "mes": mes,
        "drenagem": drenagem,
        "evidencia_campo": evidencia_campo,
        "dia_selecionado": dia_selecionado,
        "df_frentes_sidebar": df_frentes_sidebar,
    }