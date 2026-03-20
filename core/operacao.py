import pandas as pd

from core.helpers import safe_float, safe_int


def status_alerta(valor):
    valor = safe_float(valor)
    if valor >= 50:
        return "CRÍTICO", "critico"
    if valor >= 30:
        return "ATENÇÃO", "atencao"
    return "NORMAL", "normal"


def obter_ultimo_dia_referencia(df: pd.DataFrame) -> int:
    if df.empty or "Dia" not in df.columns:
        return 0

    if "Preenchido" in df.columns:
        dias_validos = df.loc[df["Preenchido"] == True, "Dia"]
    else:
        chuva = pd.to_numeric(df["Chuva (mm)"], errors="coerce")
        dias_validos = df.loc[chuva.notna(), "Dia"]

    if dias_validos.empty:
        return 0

    return safe_int(dias_validos.max(), 0)


def obter_janela_recente(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    ultimo_dia = obter_ultimo_dia_referencia(df)
    if ultimo_dia <= 0:
        return df.iloc[0:0].copy()

    df_filtrado = df[df["Dia"] <= ultimo_dia].copy()
    df_filtrado["Chuva (mm)"] = pd.to_numeric(
        df_filtrado["Chuva (mm)"], errors="coerce"
    ).fillna(0.0)
    return df_filtrado


def calcular_condicao_operacional(df, drenagem, evidencia_campo):
    df_recente = obter_janela_recente(df)

    chuva_24h = (
        safe_float(df_recente["Chuva (mm)"].tail(1).sum())
        if not df_recente.empty
        else 0.0
    )
    chuva_72h = (
        safe_float(df_recente["Chuva (mm)"].tail(3).sum())
        if not df_recente.empty
        else 0.0
    )

    if evidencia_campo == "Encharcado / atolamento crítico":
        classe = "Crítico"
    elif evidencia_campo == "Lama / atolamento leve":
        classe = "Restrito"
    elif evidencia_campo in ["Poças isoladas", "Superfície úmida"]:
        classe = "Úmido"
    else:
        if chuva_72h >= 50 or chuva_24h >= 30:
            classe = "Crítico"
        elif chuva_72h >= 25 or chuva_24h >= 15 or drenagem == "Ruim":
            classe = "Restrito"
        elif chuva_72h >= 10 or chuva_24h >= 5:
            classe = "Úmido"
        else:
            classe = "Normal"

        if drenagem == "Ruim" and chuva_72h >= 35:
            classe = "Crítico"

    detalhamento = {
        "Chuva 24h (mm)": chuva_24h,
        "Chuva 72h (mm)": chuva_72h,
        "Drenagem": drenagem,
        "Evidência de campo": evidencia_campo,
        "Condição operacional": classe,
    }
    return classe, detalhamento


def projetar_tendencia_72h(previsao_df, condicao_atual, drenagem, evidencia_campo):
    if previsao_df.empty:
        return (
            "Indisponível",
            "Não foi possível estimar a tendência operacional para 72h.",
            "normal",
        )

    chuva_prev_72h = safe_float(previsao_df["Chuva Prevista (mm)"].head(3).sum())

    if evidencia_campo == "Encharcado / atolamento crítico" or chuva_prev_72h >= 60:
        return (
            "Crítica",
            "Há forte probabilidade de restrição severa das frentes nas próximas 72 horas.",
            "critico",
        )

    if (
        evidencia_campo in ["Lama / atolamento leve", "Poças isoladas"]
        or drenagem == "Ruim"
        or chuva_prev_72h >= 30
    ):
        return (
            "Atenção",
            "Há tendência de piora operacional nas próximas 72 horas.",
            "atencao",
        )

    if chuva_prev_72h >= 10 or condicao_atual in ["Úmido", "Restrito"]:
        return (
            "Monitoramento",
            "Manter acompanhamento das condições operacionais nas próximas 72 horas.",
            "monitoramento",
        )

    return (
        "Estável",
        "Sem indicativo relevante de agravamento operacional nas próximas 72 horas.",
        "normal",
    )


def consolidar_frentes(df_frentes_mapa: pd.DataFrame):
    total = len(df_frentes_mapa)
    resumo = {
        "total": total,
        "sem_atualizacao": 0,
        "normal": 0,
        "monitoramento": 0,
        "restricao": 0,
        "paralisada": 0,
    }

    if total == 0:
        return resumo

    resumo["sem_atualizacao"] = safe_int(
        (df_frentes_mapa["Status do dia"] == "Sem atualização").sum()
    )
    resumo["normal"] = safe_int(
        (df_frentes_mapa["Status do dia"] == "Operando normal").sum()
    )
    resumo["monitoramento"] = safe_int(
        (df_frentes_mapa["Status do dia"] == "Monitoramento").sum()
    )
    resumo["restricao"] = safe_int(
        (df_frentes_mapa["Status do dia"] == "Operando com restrição").sum()
    )
    resumo["paralisada"] = safe_int(
        (df_frentes_mapa["Status do dia"] == "Paralisada").sum()
    )
    return resumo


def gerar_decisao_operacional(
    condicao_operacional,
    tendencia_72h,
    maximo,
    evidencia_campo,
    alerta_auto,
    resumo_frentes,
):
    maximo = safe_float(maximo)

    total_frentes = safe_int(resumo_frentes.get("total", 0))
    sem_atualizacao = safe_int(resumo_frentes.get("sem_atualizacao", 0))
    paralisadas = safe_int(resumo_frentes.get("paralisada", 0))
    restritas = safe_int(resumo_frentes.get("restricao", 0))
    monitoradas = safe_int(resumo_frentes.get("monitoramento", 0))

    percentual_sem_atualizacao = (
        sem_atualizacao / total_frentes if total_frentes > 0 else 0.0
    )

    if total_frentes > 0 and percentual_sem_atualizacao >= 0.5:
        return (
            "Quadro incompleto / atualização pendente",
            "Mais de 50% das frentes cadastradas estão sem lançamento no dia. Atualize as frentes antes de consolidar a decisão operacional da obra.",
            "warning",
        )

    if (
        evidencia_campo == "Encharcado / atolamento crítico"
        or condicao_operacional == "Crítico"
        or tendencia_72h == "Crítica"
        or alerta_auto["nivel"] == "CRITICO"
        or paralisadas >= 2
        or maximo >= 50
    ):
        return (
            "Operação suspensa",
            "A leitura de campo indica condição crítica. Suspender atividades sensíveis, reavaliar mobilidade e liberar apenas ações indispensáveis sob controle.",
            "error",
        )

    if (
        evidencia_campo == "Lama / atolamento leve"
        or condicao_operacional == "Restrito"
        or tendencia_72h == "Atenção"
        or paralisadas >= 1
        or restritas >= 2
        or maximo >= 30
    ):
        return (
            "Operação com restrição",
            "A operação deve seguir sob controle reforçado, com limitação de circulação pesada e revisão contínua das frentes mais sensíveis.",
            "warning",
        )

    if (
        condicao_operacional == "Úmido"
        or tendencia_72h == "Monitoramento"
        or monitoradas >= 2
        or alerta_auto["nivel"] == "ATENCAO"
    ):
        return (
            "Operação monitorada",
            "A operação pode seguir, porém com observação permanente das frentes e reavaliação ao longo do turno.",
            "info",
        )

    return (
        "Operação normal",
        "Condições favoráveis para execução regular das atividades planejadas.",
        "success",
    )


def cor_status_card(decisao_tipo):
    return {
        "error": "dot-red",
        "warning": "dot-yellow",
        "info": "dot-blue",
        "success": "dot-green",
    }.get(decisao_tipo, "dot-green")