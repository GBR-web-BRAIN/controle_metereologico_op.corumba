import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


INMET_AVISOS_RSS_URL = "https://apiprevmet3.inmet.gov.br/avisos/rss"


def _corrigir_texto(texto):
    if texto is None:
        return ""

    texto = str(texto)

    try:
        if "Ã" in texto or "�" in texto:
            texto = texto.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        pass

    return html.unescape(texto).strip()


def _baixar_texto(url: str, timeout: int = 20) -> str:
    headers = {"User-Agent": "controle-meteorologico/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return resp.text
    except Exception:
        return ""


def _parse_data_inmet(valor):
    try:
        if not valor:
            return pd.NaT
        txt = str(valor).replace(".0", "").strip()
        return pd.to_datetime(txt, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    except Exception:
        return pd.NaT


def _extrair_campos_descricao(descricao_html: str) -> dict:
    resultado = {
        "Status": "",
        "Evento": "",
        "Severidade": "",
        "Início": "",
        "Fim": "",
        "Descrição": "",
        "Área": "",
        "Link Gráfico": "",
    }

    if not descricao_html:
        return resultado

    desc = _corrigir_texto(descricao_html)

    pares = re.findall(
        r"<tr>\s*<th[^>]*>(.*?)</th>\s*<td>(.*?)</td>\s*</tr>",
        desc,
        flags=re.IGNORECASE | re.DOTALL,
    )

    for chave, valor in pares:
        chave_limpa = _corrigir_texto(re.sub(r"<.*?>", "", chave))
        valor_limpo = _corrigir_texto(re.sub(r"<.*?>", "", valor))
        if chave_limpa in resultado:
            resultado[chave_limpa] = valor_limpo

    return resultado


def _separar_areas(area_texto: str) -> list[str]:
    area_texto = _corrigir_texto(area_texto)

    if not area_texto:
        return []

    prefixos = [
        "Aviso para as Áreas:",
        "Aviso para as Areas:",
    ]

    for p in prefixos:
        if area_texto.startswith(p):
            area_texto = area_texto.replace(p, "", 1).strip()
            break

    partes = [p.strip() for p in area_texto.split(",") if p.strip()]
    return partes


@st.cache_data(ttl=900)
def obter_avisos_inmet_rss(url: str = INMET_AVISOS_RSS_URL) -> pd.DataFrame:
    xml_texto = _baixar_texto(url, timeout=25)

    if not xml_texto.strip():
        return pd.DataFrame()

    try:
        root = ET.fromstring(xml_texto)
    except Exception:
        return pd.DataFrame()

    itens = []
    for item in root.findall("./channel/item"):
        titulo = _corrigir_texto(item.findtext("title", default=""))
        link = _corrigir_texto(item.findtext("link", default=""))
        description = item.findtext("description", default="")
        pub_date = _corrigir_texto(item.findtext("pubDate", default=""))
        guid = _corrigir_texto(item.findtext("guid", default=""))

        campos = _extrair_campos_descricao(description)
        areas_lista = _separar_areas(campos.get("Área", ""))

        itens.append(
            {
                "Título": titulo,
                "Link": link,
                "Status": campos.get("Status", ""),
                "Evento": campos.get("Evento", ""),
                "Severidade": campos.get("Severidade", ""),
                "Início": campos.get("Início", ""),
                "Fim": campos.get("Fim", ""),
                "Descrição": campos.get("Descrição", ""),
                "Área": campos.get("Área", ""),
                "Áreas lista": areas_lista,
                "Link Gráfico": campos.get("Link Gráfico", link),
                "PubDate": pub_date,
                "Guid": guid,
            }
        )

    df = pd.DataFrame(itens)

    if df.empty:
        return df

    df["dt_inicio"] = df["Início"].apply(_parse_data_inmet)
    df["dt_fim"] = df["Fim"].apply(_parse_data_inmet)
    df["dt_pub"] = pd.to_datetime(df["PubDate"], errors="coerce", utc=True).dt.tz_localize(None)

    return df.sort_values(["dt_inicio", "dt_pub"], ascending=[False, False]).reset_index(drop=True)


def filtrar_avisos_por_regioes(df: pd.DataFrame, regioes: list[str]) -> pd.DataFrame:
    if df.empty or not regioes:
        return df.copy()

    regioes_norm = {_corrigir_texto(r).lower() for r in regioes if str(r).strip()}

    def contem_regiao(areas_lista):
        if not isinstance(areas_lista, list):
            return False
        areas_norm = {_corrigir_texto(a).lower() for a in areas_lista}
        return len(regioes_norm.intersection(areas_norm)) > 0

    filtrado = df[df["Áreas lista"].apply(contem_regiao)].copy()
    return filtrado.reset_index(drop=True)


def filtrar_avisos_vigentes(df: pd.DataFrame, agora: datetime | None = None) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    agora_ts = pd.Timestamp(agora or datetime.utcnow())

    df2 = df.copy()
    df2 = df2[df2["dt_inicio"].notna() & df2["dt_fim"].notna()].copy()
    df2 = df2[(df2["dt_inicio"] <= agora_ts) & (df2["dt_fim"] >= agora_ts)].copy()

    return df2.sort_values(["dt_inicio", "dt_pub"], ascending=[False, False]).reset_index(drop=True)


def severidade_peso(severidade: str) -> int:
    sev = _corrigir_texto(severidade).lower()

    if sev == "grande perigo":
        return 4
    if sev == "perigo":
        return 3
    if sev == "perigo potencial":
        return 2
    return 1


def resumir_nivel_avisos(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "nivel": "SEM_AVISOS",
            "titulo": "Sem avisos oficiais vigentes para a área do canteiro",
            "mensagem": "Não há aviso meteorológico oficial vigente do INMET, nas regiões monitoradas do canteiro e frentes em geral.",
            "badge": "success",
            "cor": "green",
            "peso": 0,
        }

    maior = df.iloc[df["Severidade"].apply(severidade_peso).idxmax()]
    severidade = _corrigir_texto(maior["Severidade"])
    evento = _corrigir_texto(maior["Evento"])

    if severidade == "Grande Perigo":
        return {
            "nivel": "GRANDE_PERIGO",
            "titulo": f"Aviso oficial INMET: {evento} · Grande Perigo",
            "mensagem": "Há aviso oficial vigente de grande perigo para áreas associadas ao canteiro. Recomenda-se máxima restrição operacional e revisão imediata das frentes.",
            "badge": "error",
            "cor": "red",
            "peso": 4,
        }

    if severidade == "Perigo":
        return {
            "nivel": "PERIGO",
            "titulo": f"Aviso oficial INMET: {evento} · Perigo",
            "mensagem": "Há aviso oficial vigente de perigo para áreas associadas ao canteiro. Recomenda-se restrição operacional reforçada e acompanhamento contínuo.",
            "badge": "warning",
            "cor": "orange",
            "peso": 3,
        }

    return {
        "nivel": "PERIGO_POTENCIAL",
        "titulo": f"Aviso oficial INMET: {evento} · Perigo Potencial",
        "mensagem": "Há aviso oficial vigente de perigo potencial para áreas associadas ao canteiro. Manter monitoramento reforçado e avaliação periódica das frentes.",
        "badge": "info",
        "cor": "blue",
        "peso": 2,
    }


def ajustar_decisao_por_aviso_inmet(
    decisao_titulo: str,
    decisao_texto: str,
    decisao_tipo: str,
    resumo_inmet: dict | None,
):
    resumo_inmet = resumo_inmet or {}
    nivel = str(resumo_inmet.get("nivel", "SEM_AVISOS")).upper()

    if nivel == "GRANDE_PERIGO":
        return (
            "Operação suspensa",
            "A decisão operacional foi agravada por aviso oficial do INMET em nível de grande perigo. Suspender atividades sensíveis, restringir deslocamentos e manter apenas ações indispensáveis sob controle rigoroso.",
            "error",
        )

    if nivel == "PERIGO":
        ordem = {"success": 1, "info": 2, "warning": 3, "error": 4}
        if ordem.get(decisao_tipo, 1) < 3:
            return (
                "Operação com restrição",
                "A decisão operacional foi agravada por aviso oficial do INMET em nível de perigo. Operar sob controle reforçado, limitar circulação em áreas vulneráveis e reavaliar continuamente as frentes.",
                "warning",
            )

    if nivel == "PERIGO_POTENCIAL":
        ordem = {"success": 1, "info": 2, "warning": 3, "error": 4}
        if ordem.get(decisao_tipo, 1) < 2:
            return (
                "Operação monitorada",
                "A decisão operacional foi agravada por aviso oficial do INMET em nível de perigo potencial. Manter monitoramento reforçado das frentes e revisão periódica ao longo do turno.",
                "info",
            )

    return decisao_titulo, decisao_texto, decisao_tipo


def formatar_datahora_inmet(valor) -> str:
    try:
        if pd.isna(valor):
            return "-"
        dt = pd.to_datetime(valor, errors="coerce")
        if pd.isna(dt):
            return "-"
        return dt.strftime("%d/%m/%y %H:%M")
    except Exception:
        return "-"