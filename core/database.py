import sqlite3
import shutil
import pandas as pd

from config import DB_PATH, BASE_BACKUP_DIR
from core.helpers import agora_local, safe_float, safe_int


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def criar_backup_banco():
    if not DB_PATH.exists():
        return None

    agora = agora_local()
    pasta_ano = BASE_BACKUP_DIR / str(agora.year)
    pasta_mes = pasta_ano / f"{agora.month:02d}"
    pasta_mes.mkdir(parents=True, exist_ok=True)

    nome_backup = f"pluviometria_{agora.strftime('%Y-%m-%d_%H-%M-%S')}.db"
    destino = pasta_mes / nome_backup

    try:
        shutil.copy2(DB_PATH, destino)
        return destino
    except Exception:
        return None


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS parametros_diarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ano INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                dia INTEGER NOT NULL,
                drenagem TEXT NOT NULL,
                evidencia_campo TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                UNIQUE (ano, mes, dia)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS lancamentos_diarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ano INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                dia INTEGER NOT NULL,
                chuva_mm REAL NOT NULL,
                servico_principal TEXT NOT NULL,
                impacto_obra TEXT NOT NULL,
                observacao TEXT,
                atualizado_em TEXT NOT NULL,
                UNIQUE (ano, mes, dia)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS frentes_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS status_frentes_diario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ano INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                dia INTEGER NOT NULL,
                frente_id INTEGER NOT NULL,
                status_frente TEXT NOT NULL,
                observacao_frente TEXT,
                atualizado_em TEXT NOT NULL,
                UNIQUE (ano, mes, dia, frente_id),
                FOREIGN KEY (frente_id) REFERENCES frentes_servico(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()


def gerar_mes(ano, mes):
    dias = pd.Period(f"{ano}-{mes:02d}").days_in_month
    return pd.DataFrame(
        {
            "Dia": list(range(1, dias + 1)),
            "Chuva (mm)": [None] * dias,
            "Serviço principal": ["Terraplanagem"] * dias,
            "Impacto na obra": ["Nenhum"] * dias,
            "Observação": [""] * dias,
            "Preenchido": [False] * dias,
        }
    )


def salvar_parametros_dia(ano, mes, dia, drenagem, evidencia_campo):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO parametros_diarios (
                ano, mes, dia, drenagem, evidencia_campo, atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(ano, mes, dia) DO UPDATE SET
                drenagem=excluded.drenagem,
                evidencia_campo=excluded.evidencia_campo,
                atualizado_em=excluded.atualizado_em
            """,
            (
                ano,
                mes,
                dia,
                drenagem,
                evidencia_campo,
                agora_local().isoformat(),
            ),
        )
        conn.commit()


def carregar_parametros_dia(ano, mes, dia):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT drenagem, evidencia_campo
            FROM parametros_diarios
            WHERE ano = ? AND mes = ? AND dia = ?
            """,
            (ano, mes, dia),
        )
        row = cur.fetchone()

    if row:
        return {
            "drenagem": row[0],
            "evidencia_campo": row[1],
        }

    return {
        "drenagem": "Regular",
        "evidencia_campo": "Sem restrição",
    }


def salvar_lancamento_diario(
    ano, mes, dia, chuva_mm, servico_principal, impacto_obra, observacao
):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO lancamentos_diarios (
                ano, mes, dia, chuva_mm, servico_principal, impacto_obra, observacao, atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ano, mes, dia) DO UPDATE SET
                chuva_mm=excluded.chuva_mm,
                servico_principal=excluded.servico_principal,
                impacto_obra=excluded.impacto_obra,
                observacao=excluded.observacao,
                atualizado_em=excluded.atualizado_em
            """,
            (
                ano,
                mes,
                dia,
                safe_float(chuva_mm),
                servico_principal,
                impacto_obra,
                (observacao or "").strip(),
                agora_local().isoformat(),
            ),
        )
        conn.commit()


def carregar_lancamentos_mes(ano, mes):
    with get_conn() as conn:
        query = """
            SELECT
                dia AS Dia,
                chuva_mm AS 'Chuva (mm)',
                servico_principal AS 'Serviço principal',
                impacto_obra AS 'Impacto na obra',
                COALESCE(observacao, '') AS 'Observação',
                1 AS Preenchido
            FROM lancamentos_diarios
            WHERE ano = ? AND mes = ?
            ORDER BY dia
        """
        df_db = pd.read_sql_query(query, conn, params=(ano, mes))

    base_mes = gerar_mes(ano, mes)

    if df_db.empty:
        return base_mes

    df = base_mes.merge(df_db, on="Dia", how="left", suffixes=("_base", ""))

    df["Chuva (mm)"] = pd.to_numeric(df["Chuva (mm)"], errors="coerce")
    df["Serviço principal"] = df["Serviço principal"].fillna(df["Serviço principal_base"])
    df["Impacto na obra"] = df["Impacto na obra"].fillna(df["Impacto na obra_base"])
    df["Observação"] = df["Observação"].fillna("")
    df["Preenchido"] = df["Preenchido"].fillna(False).astype(bool)

    return df[["Dia", "Chuva (mm)", "Serviço principal", "Impacto na obra", "Observação", "Preenchido"]]


def excluir_mes(ano, mes):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM lancamentos_diarios WHERE ano = ? AND mes = ?", (ano, mes))
        cur.execute("DELETE FROM parametros_diarios WHERE ano = ? AND mes = ?", (ano, mes))
        cur.execute("DELETE FROM status_frentes_diario WHERE ano = ? AND mes = ?", (ano, mes))
        conn.commit()


def listar_frentes_servico():
    with get_conn() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                nome AS Nome,
                latitude AS Latitude,
                longitude AS Longitude
            FROM frentes_servico
            ORDER BY nome
            """,
            conn,
        )
    return df


def salvar_frente_servico(nome, latitude, longitude):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO frentes_servico (
                nome, latitude, longitude
            )
            VALUES (?, ?, ?)
            """,
            (
                (nome or "").strip(),
                safe_float(latitude),
                safe_float(longitude),
            ),
        )
        conn.commit()


def excluir_frente_servico(frente_id):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM frentes_servico WHERE id = ?", (safe_int(frente_id),))
        conn.commit()


def carregar_status_frentes_dia(ano, mes, dia):
    with get_conn() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                frente_id,
                status_frente,
                COALESCE(observacao_frente, '') AS observacao_frente,
                atualizado_em
            FROM status_frentes_diario
            WHERE ano = ? AND mes = ? AND dia = ?
            """,
            conn,
            params=(ano, mes, dia),
        )
    return df


def salvar_status_frente_dia(ano, mes, dia, frente_id, status_frente, observacao_frente):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO status_frentes_diario (
                ano, mes, dia, frente_id, status_frente, observacao_frente, atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ano, mes, dia, frente_id) DO UPDATE SET
                status_frente=excluded.status_frente,
                observacao_frente=excluded.observacao_frente,
                atualizado_em=excluded.atualizado_em
            """,
            (
                ano,
                mes,
                dia,
                safe_int(frente_id),
                status_frente,
                (observacao_frente or "").strip(),
                agora_local().isoformat(),
            ),
        )
        conn.commit()