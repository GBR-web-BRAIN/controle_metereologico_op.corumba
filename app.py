import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from config import (
    configure_page,
    ANO_PADRAO,
    MES_PADRAO,
    LAT_OBRA,
    LON_OBRA,
)
from core.helpers import safe_float, safe_int, formatar_iso_para_datahora
from core.database import (
    init_db,
    criar_backup_banco,
    listar_frentes_servico,
    carregar_status_frentes_dia,
)
from core.auth import (
    init_auth_db,
    obter_usuario_logado,
    usuario_esta_logado,
    usuario_e_admin,
)
from core.clima import (
    obter_previsao,
    obter_previsao_alerta,
    obter_risco_frente,
    descricao_tempo,
    recomendacao_operacional,
    analisar_alerta_chuva,
)
from core.operacao import (
    status_alerta,
    calcular_condicao_operacional,
    projetar_tendencia_72h,
    consolidar_frentes,
    gerar_decisao_operacional,
    cor_status_card,
)
from core.frentes import gerar_inteligencia_frentes
from core.inmet import (
    obter_avisos_inmet_rss,
    filtrar_avisos_por_regioes,
    filtrar_avisos_vigentes,
    resumir_nivel_avisos,
    ajustar_decisao_por_aviso_inmet,
    formatar_datahora_inmet,
)
from ui.styles import (
    carregar_css_externo,
    carregar_imagem_base64,
    render_icon_html,
    get_bg_css,
    get_global_css,
)
from ui.components import card_situacao_frentes_html
from ui.map_view import criar_mapa_obra, radar_windy_embed
from layouts.sidebar import (
    init_modo_exibicao,
    render_modo_selector,
    init_periodo_sessao,
    render_sidebar_operacional,
    render_sidebar_visitante,
    get_contexto_modo_comando,
)
from layouts.auth_view import render_login, render_usuario_logado_sidebar
from layouts.topo import render_saida_modo_comando, render_topo
from layouts.painel_principal import render_painel_principal
from layouts.painel_frentes import render_inteligencia_frentes
from layouts.previsao import render_previsao
from layouts.observacoes import render_observacoes
from layouts.relatorio import render_relatorio
from layouts.banco_view import render_banco_view


configure_page()

init_db()
init_auth_db()

BG_B64 = carregar_imagem_base64("bg_ceunuvens.png")
st.markdown(get_global_css(False, get_bg_css(BG_B64)), unsafe_allow_html=True)
carregar_css_externo()

if not usuario_esta_logado():
    render_login()
    st.stop()

usuario_logado = obter_usuario_logado()
admin_logado = usuario_e_admin(usuario_logado)

init_modo_exibicao()
modo_comando = render_modo_selector(usuario_logado=usuario_logado)
render_usuario_logado_sidebar()

ICON_CAL = render_icon_html("icon_calendario.png", "📅", 34)
ICON_CHUVA = render_icon_html("icon_chuva.png", "🌧️", 34)
ICON_GOTA = render_icon_html("icon_gota.png", "💧", 34)

st.markdown(get_global_css(modo_comando, get_bg_css(BG_B64)), unsafe_allow_html=True)
carregar_css_externo()

if "backup_inicial_realizado" not in st.session_state:
    criar_backup_banco()
    st.session_state.backup_inicial_realizado = True

init_periodo_sessao(ANO_PADRAO, MES_PADRAO)

if not modo_comando:
    if admin_logado:
        contexto = render_sidebar_operacional(usuario_logado=usuario_logado)
    else:
        contexto = render_sidebar_visitante(usuario_logado=usuario_logado)
else:
    contexto = get_contexto_modo_comando()

ano = contexto["ano"]
mes = contexto["mes"]
drenagem = contexto["drenagem"]
evidencia_campo = contexto["evidencia_campo"]
dia_selecionado = contexto["dia_selecionado"]

df = st.session_state.df.copy()
df["Chuva (mm)"] = pd.to_numeric(df["Chuva (mm)"], errors="coerce")
df["Acumulado"] = df["Chuva (mm)"].fillna(0.0).cumsum()

previsao_df = obter_previsao()
previsao_alerta = obter_previsao_alerta(LAT_OBRA, LON_OBRA)

if previsao_alerta:
    alerta_auto = analisar_alerta_chuva(previsao_alerta)
else:
    alerta_auto = {
        "nivel": "SEM_DADOS",
        "titulo": "Consulta meteorológica indisponível",
        "mensagem": "Não foi possível consultar a regra automática de aproximação de chuva neste momento.",
        "detalhes": [],
        "pico_prob": 0.0,
        "pico_chuva": 0.0,
        "pico_precip": 0.0,
        "hora_critica": None,
    }

AREAS_INMET_CANTEIRO = [
    "Pantanais Sul Mato-grossense",
    "Centro Norte de Mato Grosso do Sul",
    "Leste de Mato Grosso do Sul",
    "Centro-Sul Mato-grossense",
]

avisos_inmet_df = obter_avisos_inmet_rss()
avisos_inmet_area_df = filtrar_avisos_por_regioes(avisos_inmet_df, AREAS_INMET_CANTEIRO)
avisos_inmet_vigentes_df = filtrar_avisos_vigentes(avisos_inmet_area_df)
resumo_inmet = resumir_nivel_avisos(avisos_inmet_vigentes_df)

condicao_operacional, detalhamento_operacional = calcular_condicao_operacional(
    df=df,
    drenagem=drenagem,
    evidencia_campo=evidencia_campo,
)

tendencia_72h, texto_72h, classe_72h = projetar_tendencia_72h(
    previsao_df=previsao_df,
    condicao_atual=condicao_operacional,
    drenagem=drenagem,
    evidencia_campo=evidencia_campo,
)

maximo = safe_float(df["Chuva (mm)"].fillna(0).max())
total = safe_float(df["Chuva (mm)"].fillna(0).sum())
dias_chuva = safe_int((df["Chuva (mm)"].fillna(0) > 0).sum())
alerta, classe_alerta = status_alerta(maximo)

df_frentes = listar_frentes_servico()
status_dia_df = carregar_status_frentes_dia(ano, mes, safe_int(dia_selecionado))

if not df_frentes.empty:
    df_frentes_mapa = df_frentes.merge(
        status_dia_df,
        left_on="id",
        right_on="frente_id",
        how="left",
    )
else:
    df_frentes_mapa = pd.DataFrame(
        columns=[
            "id",
            "Nome",
            "Latitude",
            "Longitude",
            "frente_id",
            "status_frente",
            "observacao_frente",
            "atualizado_em",
        ]
    )

if not df_frentes_mapa.empty:
    df_frentes_mapa["Status do dia"] = df_frentes_mapa["status_frente"].fillna("Sem atualização")
    df_frentes_mapa["Observação da frente"] = df_frentes_mapa["observacao_frente"].fillna("")
    df_frentes_mapa["Atualizado"] = df_frentes_mapa["atualizado_em"].apply(formatar_iso_para_datahora)

    riscos_auto = []
    for _, row in df_frentes_mapa.iterrows():
        risco = obter_risco_frente(safe_float(row["Latitude"]), safe_float(row["Longitude"]))
        riscos_auto.append(risco)

    df_frentes_mapa["Risco automático"] = [item["risco"] for item in riscos_auto]
    df_frentes_mapa["Pico prob. chuva"] = [item["pico_prob"] for item in riscos_auto]
    df_frentes_mapa["Pico chuva"] = [item["pico_chuva"] for item in riscos_auto]
else:
    df_frentes_mapa["Status do dia"] = []
    df_frentes_mapa["Observação da frente"] = []
    df_frentes_mapa["Atualizado"] = []
    df_frentes_mapa["Risco automático"] = []
    df_frentes_mapa["Pico prob. chuva"] = []
    df_frentes_mapa["Pico chuva"] = []

resumo_frentes = consolidar_frentes(df_frentes_mapa)

decisao_titulo, decisao_texto, decisao_tipo = gerar_decisao_operacional(
    condicao_operacional=condicao_operacional,
    tendencia_72h=tendencia_72h,
    maximo=maximo,
    evidencia_campo=evidencia_campo,
    alerta_auto=alerta_auto,
    resumo_frentes=resumo_frentes,
)

decisao_titulo, decisao_texto, decisao_tipo = ajustar_decisao_por_aviso_inmet(
    decisao_titulo=decisao_titulo,
    decisao_texto=decisao_texto,
    decisao_tipo=decisao_tipo,
    resumo_inmet=resumo_inmet,
)

frentes_inteligentes = gerar_inteligencia_frentes(df_frentes_mapa)

servico_ref = (
    df["Serviço principal"].mode()[0]
    if not df["Serviço principal"].mode().empty
    else "Terraplanagem"
)

parecer = (
    f"O diagnóstico operacional foi baseado na leitura de campo registrada na obra. "
    f"Foram considerados os volumes de chuva das últimas 24h e 72h, "
    f"o nível de drenagem ({drenagem.lower()}), a evidência observada ({evidencia_campo.lower()}), "
    f"a situação diária das frentes de serviço e os avisos oficiais vigentes do INMET para áreas associadas ao canteiro. "
    f"A tendência operacional para as próximas 72 horas é {tendencia_72h.lower()}. "
    f"A decisão operacional recomendada é {decisao_titulo.lower()}. "
    + (
        "Há necessidade de contenção imediata das atividades sensíveis."
        if decisao_titulo in ["Operação suspensa", "Operação com restrição"]
        else "A operação pode seguir com rotina compatível à condição observada."
    )
)

if not previsao_df.empty:
    previsao_df["Condição"] = previsao_df["Código"].apply(descricao_tempo)
    previsao_df["Data_fmt"] = pd.to_datetime(previsao_df["Data"], errors="coerce").dt.strftime("%d/%m/%y")
    previsao_df[["Decisão", "Orientação", "Classe"]] = previsao_df.apply(
        lambda row: pd.Series(
            recomendacao_operacional(row["Chuva Prevista (mm)"], row["Condição"])
        ),
        axis=1,
    )

render_saida_modo_comando(modo_comando)

st.caption(
    f"Usuário logado: {usuario_logado['nome']} | Perfil: {usuario_logado['perfil'].capitalize()}"
)

render_topo(
    modo_comando=modo_comando,
    alerta_auto=alerta_auto,
    decisao_titulo=decisao_titulo,
    decisao_texto=decisao_texto,
    decisao_tipo=decisao_tipo,
    condicao_operacional=condicao_operacional,
    tendencia_72h=tendencia_72h,
    dot_class=cor_status_card(decisao_tipo),
)


def render_bloco_avisos_inmet():
    st.markdown(
        "<div class='map-panel-note'>"
        "Leitura oficial baseada no feed RSS de avisos do INMET, filtrada para regiões associadas ao canteiro "
        "e às frentes de serviço em geral."
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption(
        "Regiões monitoradas: Pantanais Sul Mato-grossense, Centro Norte de Mato Grosso do Sul, "
        "Leste de Mato Grosso do Sul e Centro-Sul Mato-grossense."
    )

    if resumo_inmet["badge"] == "error":
        st.error(f"{resumo_inmet['titulo']} — {resumo_inmet['mensagem']}")
    elif resumo_inmet["badge"] == "warning":
        st.warning(f"{resumo_inmet['titulo']} — {resumo_inmet['mensagem']}")
    elif resumo_inmet["badge"] == "info":
        st.info(f"{resumo_inmet['titulo']} — {resumo_inmet['mensagem']}")
    else:
        st.success(f"{resumo_inmet['titulo']} — {resumo_inmet['mensagem']}")

    resumo_cards = st.columns(4)
    with resumo_cards[0]:
        st.metric("Avisos vigentes", len(avisos_inmet_vigentes_df))
    with resumo_cards[1]:
        st.metric(
            "Maior severidade",
            (
                avisos_inmet_vigentes_df["Severidade"]
                .iloc[avisos_inmet_vigentes_df["Severidade"].apply(
                    lambda x: {"Grande Perigo": 4, "Perigo": 3, "Perigo Potencial": 2}.get(str(x), 1)
                ).idxmax()]
                if not avisos_inmet_vigentes_df.empty
                else "-"
            ),
        )
    with resumo_cards[2]:
        st.metric(
            "Eventos",
            avisos_inmet_vigentes_df["Evento"].nunique() if not avisos_inmet_vigentes_df.empty else 0,
        )
    with resumo_cards[3]:
        st.metric("Áreas monitoradas", len(AREAS_INMET_CANTEIRO))

    if avisos_inmet_vigentes_df.empty:
        st.info("Sem avisos oficiais vigentes do INMET para as áreas monitoradas do canteiro.")
        return

    for _, aviso in avisos_inmet_vigentes_df.iterrows():
        titulo = f"{aviso['Evento']} · {aviso['Severidade']}"
        inicio_fmt = formatar_datahora_inmet(aviso["dt_inicio"])
        fim_fmt = formatar_datahora_inmet(aviso["dt_fim"])

        with st.expander(titulo, expanded=False):
            st.write(f"**Início:** {inicio_fmt}")
            st.write(f"**Fim:** {fim_fmt}")
            st.write(f"**Descrição:** {aviso['Descrição']}")
            st.write(f"**Áreas atingidas:** {', '.join(aviso['Áreas lista'])}")
            if aviso["Link Gráfico"]:
                st.markdown(f"**Link oficial:** {aviso['Link Gráfico']}")

    tabela_avisos = avisos_inmet_vigentes_df[
        ["Evento", "Severidade", "dt_inicio", "dt_fim", "Descrição"]
    ].copy()
    tabela_avisos["Início"] = tabela_avisos["dt_inicio"].apply(formatar_datahora_inmet)
    tabela_avisos["Fim"] = tabela_avisos["dt_fim"].apply(formatar_datahora_inmet)
    tabela_avisos = tabela_avisos[["Evento", "Severidade", "Início", "Fim", "Descrição"]]

    st.markdown("#### Quadro oficial resumido")
    st.dataframe(tabela_avisos, use_container_width=True, hide_index=True)


if modo_comando:
    st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Avisos meteorológicos oficiais · INMET</div>", unsafe_allow_html=True)
    render_bloco_avisos_inmet()
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Avisos meteorológicos oficiais · INMET</div>", unsafe_allow_html=True)
    with st.expander("Abrir avisos meteorológicos oficiais", expanded=False):
        render_bloco_avisos_inmet()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel-shell'>", unsafe_allow_html=True)
st.markdown(
    "<div class='panel-title'>Mapa tático da obra + radar meteorológico real</div>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<div class='map-panel-note'>Mapa baseado em frentes de serviço lançadas para o dia <b>{safe_int(dia_selecionado):02d}/{safe_int(mes):02d}/{safe_int(ano) % 100:02d}</b>.</div>",
    unsafe_allow_html=True,
)

if modo_comando:
    col_mapa, col_radar = st.columns([1.45, 1])

    with col_mapa:
        mapa = criar_mapa_obra(frentes_inteligentes)
        st_folium(mapa, width=None, height=760, returned_objects=[])

    with col_radar:
        camada = "radar"
        st.components.v1.html(
            radar_windy_embed(lat=LAT_OBRA, lon=LON_OBRA, zoom=9, layer=camada),
            height=540,
        )

        st.markdown("#### Quadro das frentes")
        resumo_cmd = pd.DataFrame(
            [{"Frente": item["nome"], "Status": item["status"], "Risco auto.": item["risco_auto"]} for item in frentes_inteligentes]
        )
        if resumo_cmd.empty:
            st.info("Nenhuma frente cadastrada.")
        else:
            st.dataframe(resumo_cmd, use_container_width=True, hide_index=True)
else:
    with st.expander("Mapa tático da obra", expanded=True):
        mapa = criar_mapa_obra(frentes_inteligentes)
        retorno_mapa = st_folium(
            mapa,
            width=None,
            height=700,
            returned_objects=["last_clicked", "bounds", "zoom"],
        )

        if admin_logado and retorno_mapa and retorno_mapa.get("last_clicked"):
            clique = retorno_mapa["last_clicked"]
            st.info(f"Último clique no mapa: Lat {clique['lat']:.6f} | Lon {clique['lng']:.6f}")

    with st.expander("Radar meteorológico real", expanded=False):
        camada = st.selectbox(
            "Camada meteorológica",
            ["radar", "rain", "wind", "clouds", "temp"],
            index=0,
            key="camada_radar",
        )
        st.components.v1.html(
            radar_windy_embed(lat=LAT_OBRA, lon=LON_OBRA, zoom=9, layer=camada),
            height=540,
        )

        with st.expander("Detalhamento do alerta automático", expanded=False):
            if alerta_auto.get("detalhes"):
                for item in alerta_auto["detalhes"]:
                    st.write(
                        f"**{item['hora'].strftime('%d/%m/%y %H:%M')}** | "
                        f"Prob.: {safe_float(item['probabilidade']):.0f}% | "
                        f"Rain: {safe_float(item['chuva']):.1f} mm/h | "
                        f"Precip.: {safe_float(item['precipitacao']):.1f} mm"
                    )
            else:
                st.info("Sem detalhamento disponível no momento.")

st.markdown("</div>", unsafe_allow_html=True)

render_inteligencia_frentes(modo_comando, frentes_inteligentes)

col_dir = render_painel_principal(
    df=df,
    total=total,
    maximo=maximo,
    dias_chuva=dias_chuva,
    modo_comando=modo_comando,
    icon_gota=ICON_GOTA,
    icon_chuva=ICON_CHUVA,
    icon_cal=ICON_CAL,
)

with col_dir:
    st.markdown(
        card_situacao_frentes_html(resumo_frentes),
        unsafe_allow_html=True,
    )

render_previsao(previsao_df)
render_observacoes(modo_comando, df, df_frentes_mapa, ano, mes)

resumo_pdf = {
    "Total do mês": f"{total:.0f} mm",
    "Maior chuva": f"{maximo:.0f} mm",
    "Dias com chuva": dias_chuva,
    "Condição operacional": condicao_operacional,
    "Drenagem": drenagem,
    "Evidência de campo": evidencia_campo,
    "Tendência operacional 72h": tendencia_72h,
    "Decisão operacional": decisao_titulo,
    "Serviço predominante": servico_ref,
    "Status operacional": alerta,
    "Alerta automático": alerta_auto["nivel"],
    "Avisos oficiais INMET vigentes": len(avisos_inmet_vigentes_df),
    "Maior severidade INMET": (
        avisos_inmet_vigentes_df["Severidade"]
        .iloc[avisos_inmet_vigentes_df["Severidade"].apply(
            lambda x: {"Grande Perigo": 4, "Perigo": 3, "Perigo Potencial": 2}.get(str(x), 1)
        ).idxmax()]
        if not avisos_inmet_vigentes_df.empty
        else "Sem avisos"
    ),
    "Frentes cadastradas": resumo_frentes["total"],
    "Frentes sem atualização": resumo_frentes["sem_atualizacao"],
    "Frentes normais": resumo_frentes["normal"],
    "Frentes em monitoramento": resumo_frentes["monitoramento"],
    "Frentes em restrição": resumo_frentes["restricao"],
    "Frentes paralisadas": resumo_frentes["paralisada"],
}

render_relatorio(
    ano,
    mes,
    resumo_pdf,
    parecer,
    previsao_df,
    permitir_download=admin_logado,
)

if admin_logado:
    render_banco_view(modo_comando)

if admin_logado:
    df_export = df.copy()
    df_export["Data"] = df_export["Dia"].apply(lambda x: f"{safe_int(x):02d}/{safe_int(mes):02d}/{safe_int(ano) % 100:02d}")

    st.download_button(
        "Exportar base CSV",
        data=df_export.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"controle_meteorologico_{ano}_{mes:02d}.csv",
    )
else:
    st.info("Exportação CSV disponível apenas para administrador.")