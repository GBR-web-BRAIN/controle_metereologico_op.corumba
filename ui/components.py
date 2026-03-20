from core.helpers import safe_float
from core.clima import icone_tempo


def metric_card_html(icon_html, titulo, valor, subtitulo):
    return f"""
    <div class="metric-card">
        <div class="metric-card-head">
            {icon_html}
            <div class="metric-card-label">{titulo}</div>
        </div>
        <div class="metric-card-value">{valor}</div>
        <div class="metric-card-sub">{subtitulo}</div>
    </div>
    """


def forecast_card_html(data_fmt, codigo, chuva, condicao, tmax, tmin, decisao):
    return f"""
    <div class="forecast-box">
        <div class="forecast-day">{icone_tempo(codigo)} {data_fmt}</div>
        <div class="forecast-main">{safe_float(chuva):.1f} mm</div>
        <div class="forecast-cond">{condicao}</div>
        <div class="forecast-temp">Máx {safe_float(tmax):.0f}°C · Mín {safe_float(tmin):.0f}°C</div>
        <div class="forecast-decision">{decisao}</div>
    </div>
    """


def badge_html(condicao_operacional):
    if condicao_operacional == "Normal":
        return "<span class='tactical-badge badge-green'>NORMAL</span>"
    if condicao_operacional == "Úmido":
        return "<span class='tactical-badge badge-blue'>ÚMIDO</span>"
    if condicao_operacional == "Restrito":
        return "<span class='tactical-badge badge-yellow'>RESTRITO</span>"
    return "<span class='tactical-badge badge-red'>CRÍTICO</span>"


def command_mini_card_html(decisao_titulo, condicao_operacional, tendencia_72h, dot_class):
    return f"""
    <div class="command-mini-card">
        <div class="command-mini-label">Status da obra</div>
        <div class="command-mini-status">
            <span class="command-mini-dot {dot_class}"></span>{decisao_titulo}
        </div>
        <div class="command-mini-line"><b>Campo:</b> {condicao_operacional}</div>
        <div class="command-mini-line"><b>Tendência 72h:</b> {tendencia_72h}</div>
    </div>
    """


def alerta_meteo_card_html(
    titulo, mensagem, nivel, pico_prob=0, pico_chuva=0.0, pico_precip=0.0, hora_ref="-"
):
    badge_class = "badge-green"
    dot_class = "dot-green"

    if nivel == "CRITICO":
        badge_class = "badge-red"
        dot_class = "dot-red"
    elif nivel == "ATENCAO":
        badge_class = "badge-yellow"
        dot_class = "dot-yellow"
    elif nivel == "SEM_DADOS":
        badge_class = "badge-blue"
        dot_class = "dot-blue"

    texto_badge = nivel.replace("_", " ")

    return f"""
    <div class="alert-auto-box">
        <div class="command-mini-label">Alerta meteorológico automático</div>
        <div class="alert-auto-title">
            <span class="command-mini-dot {dot_class}"></span>{titulo}
        </div>
        <div class="tactical-badge {badge_class}">{texto_badge}</div>
        <div class="alert-auto-text">{mensagem}</div>
        <div class="alert-auto-metrics">
            <b>Hora crítica:</b> {hora_ref}<br>
            <b>Pico prob. chuva:</b> {safe_float(pico_prob):.0f}%<br>
            <b>Pico chuva (mm/h):</b> {safe_float(pico_chuva):.1f}<br>
            <b>Pico precipitação:</b> {safe_float(pico_precip):.1f} mm
        </div>
    </div>
    """


def front_card_html(nome, status, impacto, recomendacao, risco_auto):
    badge = "badge-gray"
    dot = "dot-gray"

    if status == "Operando normal":
        badge = "badge-green"
        dot = "dot-green"
    elif status == "Monitoramento":
        badge = "badge-blue"
        dot = "dot-blue"
    elif status == "Operando com restrição":
        badge = "badge-yellow"
        dot = "dot-yellow"
    elif status == "Paralisada":
        badge = "badge-red"
        dot = "dot-red"

    return f"""
    <div class="front-risk-card">
        <div class="front-risk-title">
            <span class="command-mini-dot {dot}"></span>{nome}
        </div>
        <div class="tactical-badge {badge}">{status}</div>
        <div class="front-risk-text">
            <b>Risco automático:</b> {risco_auto}<br>
            <b>Impacto provável:</b> {impacto}<br>
            <b>Recomendação:</b> {recomendacao}
        </div>
    </div>
    """


def card_situacao_frentes_html(resumo_frentes):
    total = int(resumo_frentes.get("total", 0))
    sem_atualizacao = int(resumo_frentes.get("sem_atualizacao", 0))
    normal = int(resumo_frentes.get("normal", 0))
    monitoramento = int(resumo_frentes.get("monitoramento", 0))
    restricao = int(resumo_frentes.get("restricao", 0))
    paralisada = int(resumo_frentes.get("paralisada", 0))

    return f"""
    <div class="command-mini-card">
        <div class="command-mini-label">Situação das frentes</div>
        <div class="command-mini-status">
            <span class="command-mini-dot dot-blue"></span>{total} cadastradas
        </div>
        <div class="command-mini-line"><b>Operando normal:</b> {normal}</div>
        <div class="command-mini-line"><b>Monitoramento:</b> {monitoramento}</div>
        <div class="command-mini-line"><b>Com restrição:</b> {restricao}</div>
        <div class="command-mini-line"><b>Paralisadas:</b> {paralisada}</div>
        <div class="command-mini-line"><b>Sem atualização:</b> {sem_atualizacao}</div>
    </div>
    """


def inmet_status_card_html(
    titulo,
    subtitulo,
    badge_texto,
    badge_class,
    linha1,
    linha2="",
    linha3="",
):
    linhas = "".join(
        f"<div class='command-mini-line'>{linha}</div>"
        for linha in [linha1, linha2, linha3]
        if linha
    )

    return f"""
    <div class="command-mini-card">
        <div class="command-mini-label">Observação oficial INMET</div>
        <div class="alert-auto-title">{titulo}</div>
        <div class="tactical-badge {badge_class}">{badge_texto}</div>
        <div class="alert-auto-text">{subtitulo}</div>
        <div style="margin-top:10px;">
            {linhas}
        </div>
    </div>
    """


def inmet_metric_card_html(titulo, valor, subtitulo="", dot_class="dot-blue"):
    return f"""
    <div class="metric-card">
        <div class="metric-card-head">
            <span class="command-mini-dot {dot_class}"></span>
            <div class="metric-card-label">{titulo}</div>
        </div>
        <div class="metric-card-value">{valor}</div>
        <div class="metric-card-sub">{subtitulo}</div>
    </div>
    """


def alerta_piscando_html(hora_ref: str):
    return f"""
    <div class="alerta-piscando">
        <div class="alerta-piscando-titulo">⚠️ ALERTA METEOROLÓGICO CRÍTICO</div>
        <div class="alerta-piscando-texto">
            CHUVA FORTE APROXIMANDO DA OBRA<br>
            Janela crítica estimada: <b>{hora_ref}</b><br>
            Recomenda-se restrição imediata de mobilidade e suspensão de atividades sensíveis.
        </div>
    </div>
    """