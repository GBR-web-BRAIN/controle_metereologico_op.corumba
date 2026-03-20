import hashlib
import hmac
import os
from typing import Optional

import pandas as pd
import streamlit as st

from core.database import get_conn
from core.helpers import agora_local


def _get_secret(nome: str, default: str = "") -> str:
    try:
        valor = st.secrets.get(nome, default)
        return str(valor).strip()
    except Exception:
        return str(os.getenv(nome, default)).strip()


USUARIO_ADMIN_PADRAO = _get_secret("APP_ADMIN_USER", "admin")
SENHA_ADMIN_PADRAO = _get_secret("APP_ADMIN_PASSWORD", "")
NOME_ADMIN_PADRAO = _get_secret("APP_ADMIN_NAME", "Administrador")


def _normalizar_username(username: str) -> str:
    return (username or "").strip().lower()


def _normalizar_nome(nome: str) -> str:
    return (nome or "").strip()


def _gerar_salt() -> str:
    return os.urandom(16).hex()


def _hash_senha(senha: str, salt: str) -> str:
    senha = senha or ""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return dk.hex()


def verificar_senha(senha_informada: str, salt: str, senha_hash: str) -> bool:
    hash_calculado = _hash_senha(senha_informada, salt)
    return hmac.compare_digest(hash_calculado, senha_hash)


def init_auth_db():
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                perfil TEXT NOT NULL CHECK (perfil IN ('admin', 'visitante')),
                senha_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )
            """
        )

        conn.commit()

    garantir_admin_inicial()


def garantir_admin_inicial():
    username = _normalizar_username(USUARIO_ADMIN_PADRAO)
    senha = SENHA_ADMIN_PADRAO

    if not username:
        return

    if not senha:
        raise RuntimeError(
            "APP_ADMIN_PASSWORD não foi definido. Configure a senha do administrador em st.secrets ou variável de ambiente."
        )

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM usuarios WHERE username = ?",
            (username,),
        )
        existe = cur.fetchone()

        if existe:
            return

        agora = agora_local().isoformat()
        salt = _gerar_salt()
        senha_hash = _hash_senha(senha, salt)

        cur.execute(
            """
            INSERT INTO usuarios (
                username, nome, perfil, senha_hash, salt, ativo, criado_em, atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                _normalizar_nome(NOME_ADMIN_PADRAO) or "Administrador",
                "admin",
                senha_hash,
                salt,
                1,
                agora,
                agora,
            ),
        )
        conn.commit()


def autenticar_usuario(username: str, senha: str) -> Optional[dict]:
    username = _normalizar_username(username)

    if not username or not senha:
        return None

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, username, nome, perfil, senha_hash, salt, ativo
            FROM usuarios
            WHERE username = ?
            """
            ,
            (username,),
        )
        row = cur.fetchone()

    if not row:
        return None

    usuario_id, username_db, nome, perfil, senha_hash, salt, ativo = row

    if int(ativo) != 1:
        return None

    if not verificar_senha(senha, salt, senha_hash):
        return None

    return {
        "id": int(usuario_id),
        "username": str(username_db),
        "nome": str(nome),
        "perfil": str(perfil),
        "ativo": bool(ativo),
    }


def iniciar_sessao_usuario(usuario: dict):
    st.session_state.usuario_logado = {
        "id": int(usuario["id"]),
        "username": str(usuario["username"]),
        "nome": str(usuario["nome"]),
        "perfil": str(usuario["perfil"]),
        "ativo": bool(usuario.get("ativo", True)),
    }


def atualizar_dados_sessao(nome: str | None = None):
    usuario = st.session_state.get("usuario_logado")
    if not isinstance(usuario, dict):
        return

    if nome is not None:
        usuario["nome"] = str(nome)

    st.session_state.usuario_logado = usuario


def encerrar_sessao_usuario():
    st.session_state.pop("usuario_logado", None)


def obter_usuario_logado() -> Optional[dict]:
    usuario = st.session_state.get("usuario_logado")
    if not isinstance(usuario, dict):
        return None
    return usuario


def usuario_esta_logado() -> bool:
    return obter_usuario_logado() is not None


def usuario_e_admin(usuario: Optional[dict] = None) -> bool:
    usuario = usuario or obter_usuario_logado()
    return bool(usuario and usuario.get("perfil") == "admin")


def buscar_usuario_por_id(user_id: int) -> Optional[dict]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, username, nome, perfil, ativo, criado_em, atualizado_em
            FROM usuarios
            WHERE id = ?
            """,
            (int(user_id),),
        )
        row = cur.fetchone()

    if not row:
        return None

    return {
        "id": int(row[0]),
        "username": str(row[1]),
        "nome": str(row[2]),
        "perfil": str(row[3]),
        "ativo": bool(row[4]),
        "criado_em": str(row[5]),
        "atualizado_em": str(row[6]),
    }


def criar_usuario(nome: str, username: str, senha: str, perfil: str = "visitante"):
    nome = _normalizar_nome(nome)
    username = _normalizar_username(username)
    perfil = (perfil or "").strip().lower()

    if not nome:
        raise ValueError("Informe o nome do usuário.")

    if not username:
        raise ValueError("Informe o nome de usuário.")

    if len(username) < 3:
        raise ValueError("O nome de usuário deve ter pelo menos 3 caracteres.")

    if not senha or len(senha) < 4:
        raise ValueError("A senha deve ter pelo menos 4 caracteres.")

    if perfil not in {"admin", "visitante"}:
        raise ValueError("Perfil inválido.")

    agora = agora_local().isoformat()
    salt = _gerar_salt()
    senha_hash = _hash_senha(senha, salt)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO usuarios (
                username, nome, perfil, senha_hash, salt, ativo, criado_em, atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                nome,
                perfil,
                senha_hash,
                salt,
                1,
                agora,
                agora,
            ),
        )
        conn.commit()


def alterar_status_usuario(user_id: int, ativo: bool):
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT perfil, username FROM usuarios WHERE id = ?",
            (int(user_id),),
        )
        row = cur.fetchone()

        if not row:
            raise ValueError("Usuário não encontrado.")

        perfil, username = row

        if str(perfil) == "admin" and _normalizar_username(str(username)) == _normalizar_username(USUARIO_ADMIN_PADRAO):
            raise ValueError("Não é permitido desativar o administrador principal.")

        cur.execute(
            """
            UPDATE usuarios
            SET ativo = ?, atualizado_em = ?
            WHERE id = ?
            """,
            (
                1 if ativo else 0,
                agora_local().isoformat(),
                int(user_id),
            ),
        )
        conn.commit()


def redefinir_senha_usuario(user_id: int, nova_senha: str):
    if not nova_senha or len(nova_senha) < 4:
        raise ValueError("A nova senha deve ter pelo menos 4 caracteres.")

    salt = _gerar_salt()
    senha_hash = _hash_senha(nova_senha, salt)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?, salt = ?, atualizado_em = ?
            WHERE id = ?
            """,
            (
                senha_hash,
                salt,
                agora_local().isoformat(),
                int(user_id),
            ),
        )
        conn.commit()


def alterar_senha_proprio_usuario(user_id: int, senha_atual: str, nova_senha: str, confirmar_nova_senha: str):
    if not senha_atual:
        raise ValueError("Informe a senha atual.")

    if not nova_senha or len(nova_senha) < 4:
        raise ValueError("A nova senha deve ter pelo menos 4 caracteres.")

    if nova_senha != confirmar_nova_senha:
        raise ValueError("A confirmação da nova senha não confere.")

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT senha_hash, salt
            FROM usuarios
            WHERE id = ?
            """,
            (int(user_id),),
        )
        row = cur.fetchone()

    if not row:
        raise ValueError("Usuário não encontrado.")

    senha_hash_atual, salt_atual = row

    if not verificar_senha(senha_atual, salt_atual, senha_hash_atual):
        raise ValueError("A senha atual está incorreta.")

    redefinir_senha_usuario(user_id, nova_senha)


def listar_usuarios() -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                nome AS Nome,
                username AS Usuario,
                perfil AS Perfil,
                ativo AS Ativo,
                criado_em AS Criado,
                atualizado_em AS Atualizado
            FROM usuarios
            ORDER BY perfil DESC, nome ASC, username ASC
            """,
            conn,
        )

    if df.empty:
        return df

    df["Ativo"] = df["Ativo"].apply(lambda x: "Sim" if int(x) == 1 else "Não")
    return df