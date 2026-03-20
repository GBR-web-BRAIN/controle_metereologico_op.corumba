import pandas as pd
import streamlit as st
from datetime import datetime

from config import (
    LAT_OBRA,
    LON_OBRA,
    FUSO_LOCAL,
    JANELA_ALERTA_HORAS,
    LIMITE_PROB_CHUVA_CRITICO,
    LIMITE_CHUVA_FORTE_MM_H,
    LIMITE_PROB_CHUVA_ATENCAO,
    LIMITE_CHUVA_ATENCAO_MM_H,
    WEATHER_CODE_MAP,
)
from core.helpers import http_get_json, safe_float, agora_local


@st.cache_data(ttl=1800)
def obter_previsao(lat=LAT_OBRA, lon=LON_OBRA):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
        "&timezone=America%2FCampo_Grande&forecast_days=7"
    )

    dados = http_get_json(url, timeout=15)
    diario = dados.get("daily", {})

    df = pd.DataFrame(
        {
            "Data": diario.get("time", []),
            "Temp. Máx (°C)": diario.get("temperature_2m_max", []),
            "Temp. Mín (°C)": diario.get("temperature_2m_min", []),
            "Chuva Prevista (mm)": diario.get("precipitation_sum", []),
            "Código": diario.get("weathercode", []),
        }
    )

    if df.empty:
        return pd.DataFrame()

    for col in ["Temp. Máx (°C)", "Temp. Mín (°C)", "Chuva Prevista (mm)", "Código"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.fillna(0)


@st.cache_data(ttl=900)
def obter_previsao_alerta(lat=LAT_OBRA, lon=LON_OBRA):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&hourly=precipitation_probability,precipitation,rain"
        "&forecast_days=2"
        "&timezone=America%2FCampo_Grande"
    )
    return http_get_json(url, timeout=20)


@st.cache_data(ttl=900)
def obter_risco_frente(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&hourly=precipitation_probability,precipitation,rain"
        "&forecast_days=1"
        "&timezone=America%2FCampo_Grande"
    )

    previsao = http_get_json(url, timeout=20)
    hourly = previsao.get("hourly", {}) if isinstance(previsao, dict) else {}

    tempos = hourly.get("time", [])
    probs = hourly.get("precipitation_probability", [])
    precips = hourly.get("precipitation", [])
    rains = hourly.get("rain", [])

    agora = agora_local()
    janela = []

    for t, p, pr, r in zip(tempos, probs, precips, rains):
        try:
            dt = datetime.fromisoformat(t)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=FUSO_LOCAL)
        except Exception:
            continue

        delta_horas = (dt - agora).total_seconds() / 3600

        if 0 <= delta_horas <= 3:
            janela.append(
                {
                    "hora": dt,
                    "probabilidade": safe_float(p),
                    "precipitacao": safe_float(pr),
                    "chuva": safe_float(r),
                }
            )

    if not janela:
        return {
            "risco": "Sem leitura",
            "cor": "gray",
            "pico_prob": 0.0,
            "pico_chuva": 0.0,
            "hora_critica": None,
        }

    pico_prob = max(item["probabilidade"] for item in janela)
    pico_chuva = max(max(item["precipitacao"], item["chuva"]) for item in janela)

    hora_critica = None
    for item in janela:
        if item["probabilidade"] >= 80 and max(item["precipitacao"], item["chuva"]) >= 6:
            hora_critica = item["hora"]
            break

    if pico_prob >= 80 or pico_chuva >= 8:
        risco = "Crítico"
        cor = "red"
    elif pico_prob >= 60 or pico_chuva >= 4:
        risco = "Restrição provável"
        cor = "orange"
    elif pico_prob >= 40 or pico_chuva >= 1:
        risco = "Monitoramento"
        cor = "blue"
    else:
        risco = "Baixo"
        cor = "green"

    return {
        "risco": risco,
        "cor": cor,
        "pico_prob": pico_prob,
        "pico_chuva": pico_chuva,
        "hora_critica": hora_critica,
    }


def descricao_tempo(codigo):
    try:
        return WEATHER_CODE_MAP.get(int(codigo), "Condição não identificada")
    except Exception:
        return "Condição não identificada"


def icone_tempo(codigo):
    try:
        codigo = int(codigo)
    except Exception:
        return "🌧️"

    if codigo in [0, 1]:
        return "☀️"
    if codigo in [2, 3]:
        return "⛅"
    if codigo in [45, 48]:
        return "🌫️"
    if codigo in [61, 63, 80, 81]:
        return "🌦️"
    if codigo in [65, 82, 95]:
        return "⛈️"
    return "🌧️"


def recomendacao_operacional(chuva_prevista, condicao):
    chuva_prevista = safe_float(chuva_prevista)
    cond = str(condicao).lower()

    if chuva_prevista >= 50 or "trovoada" in cond or "forte" in cond:
        return (
            "Suspender atividades críticas",
            "Interromper serviços sensíveis e reforçar a observação de campo.",
            "critico",
        )
    if chuva_prevista >= 30:
        return (
            "Operar com restrição",
            "Executar apenas serviços controlados e reforçar supervisão local.",
            "atencao",
        )
    if chuva_prevista >= 10:
        return (
            "Manter com monitoramento",
            "Prosseguir com atenção e avaliação periódica nas frentes.",
            "monitoramento",
        )
    return (
        "Manter atividade",
        "Condição favorável para operação normal.",
        "normal",
    )


def analisar_alerta_chuva(previsao):
    hourly = previsao.get("hourly", {}) if isinstance(previsao, dict) else {}
    tempos = hourly.get("time", [])
    probs = hourly.get("precipitation_probability", [])
    precips = hourly.get("precipitation", [])
    rains = hourly.get("rain", [])

    agora = agora_local()
    proximas_horas = []

    for t, p, pr, r in zip(tempos, probs, precips, rains):
        try:
            dt = datetime.fromisoformat(t)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=FUSO_LOCAL)
        except Exception:
            continue

        delta_horas = (dt - agora).total_seconds() / 3600

        if 0 <= delta_horas <= JANELA_ALERTA_HORAS:
            proximas_horas.append(
                {
                    "hora": dt,
                    "probabilidade": safe_float(p),
                    "precipitacao": safe_float(pr),
                    "chuva": safe_float(r),
                }
            )

    if not proximas_horas:
        return {
            "nivel": "SEM_DADOS",
            "titulo": "Sem dados suficientes",
            "mensagem": "Não foi possível avaliar a aproximação de chuva nas próximas horas.",
            "detalhes": [],
            "pico_prob": 0.0,
            "pico_chuva": 0.0,
            "pico_precip": 0.0,
            "hora_critica": None,
        }

    pico_prob = max(item["probabilidade"] for item in proximas_horas)
    pico_chuva = max(item["chuva"] for item in proximas_horas)
    pico_precip = max(item["precipitacao"] for item in proximas_horas)

    hora_critica = None
    for item in proximas_horas:
        if (
            item["probabilidade"] >= LIMITE_PROB_CHUVA_CRITICO
            and (
                item["chuva"] >= LIMITE_CHUVA_FORTE_MM_H
                or item["precipitacao"] >= LIMITE_CHUVA_FORTE_MM_H
            )
        ):
            hora_critica = item["hora"]
            break

    if hora_critica:
        return {
            "nivel": "CRITICO",
            "titulo": "CHUVA FORTE APROXIMANDO DA OBRA",
            "mensagem": (
                f"Janela crítica detectada para aproximadamente "
                f"{hora_critica.strftime('%H:%M')}. Recomenda-se preparar restrição imediata de mobilidade e serviços sensíveis."
            ),
            "detalhes": proximas_horas,
            "pico_prob": pico_prob,
            "pico_chuva": pico_chuva,
            "pico_precip": pico_precip,
            "hora_critica": hora_critica,
        }

    if (
        pico_prob >= LIMITE_PROB_CHUVA_ATENCAO
        or pico_chuva >= LIMITE_CHUVA_ATENCAO_MM_H
        or pico_precip >= LIMITE_CHUVA_ATENCAO_MM_H
    ):
        return {
            "nivel": "ATENCAO",
            "titulo": "Possível chuva se aproximando",
            "mensagem": "Há indicativos relevantes de precipitação nas próximas horas. Manter monitoramento reforçado e revisar frentes mais sensíveis.",
            "detalhes": proximas_horas,
            "pico_prob": pico_prob,
            "pico_chuva": pico_chuva,
            "pico_precip": pico_precip,
            "hora_critica": None,
        }

    return {
        "nivel": "NORMAL",
        "titulo": "Sem aproximação crítica de chuva",
        "mensagem": "Não há sinal de chuva forte nas próximas horas dentro da janela operacional monitorada.",
        "detalhes": proximas_horas,
        "pico_prob": pico_prob,
        "pico_chuva": pico_chuva,
        "pico_precip": pico_precip,
        "hora_critica": None,
    }