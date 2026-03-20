from datetime import datetime
import pandas as pd
import requests

from config import FUSO_LOCAL


def agora_local() -> datetime:
    return datetime.now(FUSO_LOCAL)


def formatar_data(dt: datetime | None = None) -> str:
    dt = dt or agora_local()
    return dt.strftime("%d/%m/%y")


def formatar_datahora_local(dt: datetime | None = None) -> str:
    dt = dt or agora_local()
    return dt.strftime("%d/%m/%y %H:%M")


def formatar_iso_para_datahora(valor):
    try:
        if not valor:
            return ""
        dt = datetime.fromisoformat(str(valor))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=FUSO_LOCAL)
        return dt.strftime("%d/%m/%y %H:%M")
    except Exception:
        return str(valor)


def safe_float(valor, default=0.0) -> float:
    try:
        if pd.isna(valor):
            return default
        return float(valor)
    except Exception:
        return default


def safe_int(valor, default=0) -> int:
    try:
        if pd.isna(valor):
            return default
        return int(valor)
    except Exception:
        return default


def http_get_json(url: str, timeout: int = 20) -> dict:
    headers = {"User-Agent": "controle-meteorologico/1.0"}

    try:
        resposta = requests.get(url, headers=headers, timeout=timeout)
        resposta.raise_for_status()
        data = resposta.json()
        return data if isinstance(data, dict) else {}
    except requests.RequestException:
        return {}
    except ValueError:
        return {}