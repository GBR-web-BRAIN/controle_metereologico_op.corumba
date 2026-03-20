from pathlib import Path
from zoneinfo import ZoneInfo
import streamlit as st

APP_TITLE = "CONTROLE METEOROLÓGICO DA OP. CORUMBÁ"
APP_PAGE_TITLE = APP_TITLE
APP_PAGE_ICON = "🌧️"

FUSO_LOCAL = ZoneInfo("America/Campo_Grande")

DB_PATH = Path("pluviometria.db")
BASE_BACKUP_DIR = Path("backup_banco")

ANO_PADRAO = 2026
MES_PADRAO = 3

LAT_OBRA = -19.055932
LON_OBRA = -57.636584
CENTRO_OBRA = [LAT_OBRA, LON_OBRA]
ZOOM_INICIAL = 16

LIMITE_PROB_CHUVA_CRITICO = 70
LIMITE_CHUVA_FORTE_MM_H = 8.0
LIMITE_PROB_CHUVA_ATENCAO = 50
LIMITE_CHUVA_ATENCAO_MM_H = 4.0
JANELA_ALERTA_HORAS = 3

SERVICOS = ["Terraplanagem", "Concretagem", "Transporte", "Drenagem"]
IMPACTOS = ["Nenhum", "Redução produtividade", "Solo encharcado", "Atividade suspensa"]
TIPOS_DRENAGEM = ["Boa", "Regular", "Ruim"]
TIPOS_EVIDENCIA = [
    "Sem restrição",
    "Superfície úmida",
    "Poças isoladas",
    "Lama / atolamento leve",
    "Encharcado / atolamento crítico",
]
STATUS_FRENTE = [
    "Sem atualização",
    "Operando normal",
    "Monitoramento",
    "Operando com restrição",
    "Paralisada",
]

WEATHER_CODE_MAP = {
    0: "Céu limpo",
    1: "Predomínio de sol",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Neblina",
    48: "Neblina intensa",
    61: "Chuva fraca",
    63: "Chuva moderada",
    65: "Chuva forte",
    80: "Pancadas fracas",
    81: "Pancadas moderadas",
    82: "Pancadas fortes",
    95: "Trovoada",
}


def configure_page():
    st.set_page_config(
        page_title=APP_PAGE_TITLE,
        layout="wide",
        page_icon=APP_PAGE_ICON,
        initial_sidebar_state="expanded",
    )