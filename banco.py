import os
import sqlite3
from datetime import datetime

CAMPOS = ("grupo", "nome", "documento", "nascimento", "telefone", "email", "endereco",
          "categoria", "especialidade", "area", "disponibilidade", "necessidade", "observacoes")


def conectar_banco():
    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
    os.makedirs(pasta, exist_ok=True)
    conn = sqlite3.connect(os.path.join(pasta, "cadastro.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pessoas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, grupo TEXT NOT NULL,
            nome TEXT NOT NULL, documento TEXT NOT NULL, documento_chave TEXT NOT NULL,
            nascimento TEXT NOT NULL, telefone TEXT NOT NULL, email TEXT NOT NULL,
            endereco TEXT NOT NULL, categoria TEXT NOT NULL, especialidade TEXT NOT NULL,
            area TEXT NOT NULL, disponibilidade TEXT NOT NULL, necessidade TEXT NOT NULL,
            observacoes TEXT NOT NULL, criado_em TEXT NOT NULL, UNIQUE(grupo, documento_chave)
        );
        CREATE TABLE IF NOT EXISTS participacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, pessoa_id INTEGER NOT NULL,
            atividade TEXT NOT NULL, data TEXT NOT NULL,
            FOREIGN KEY(pessoa_id) REFERENCES pessoas(id)
        );
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL, papel TEXT NOT NULL
        );
    """)
    return conn


def listar_pessoas(conn, termo="", grupo=""):
    filtro = "%" + termo + "%"
    return conn.execute("""
        SELECT * FROM pessoas WHERE (?='' OR grupo=?) AND
        (nome LIKE ? OR documento LIKE ? OR categoria LIKE ? OR telefone LIKE ? OR id=?)
        ORDER BY nome, id
    """, (grupo, grupo, filtro, filtro, filtro, filtro, termo)).fetchall()


def obter(conn, id_pessoa):
    return conn.execute("SELECT * FROM pessoas WHERE id=?", (id_pessoa,)).fetchone()


def documento_em_uso(conn, grupo, chave, id_atual):
    return conn.execute("SELECT id FROM pessoas WHERE grupo=? AND documento_chave=? AND id!=?",
                        (grupo, chave, id_atual or 0)).fetchone() is not None


def salvar(conn, dados, chave, id_atual=None):
    valores = tuple(dados[c] for c in CAMPOS) + (chave,)
    if id_atual is None:
        cur = conn.execute("""INSERT INTO pessoas
            (grupo,nome,documento,nascimento,telefone,email,endereco,categoria,especialidade,
             area,disponibilidade,necessidade,observacoes,documento_chave,criado_em)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            valores + (datetime.now().isoformat(timespec="seconds"),))
        return cur.lastrowid
    if obter(conn, id_atual) is None:
        return None
    conn.execute("""UPDATE pessoas SET grupo=?, nome=?, documento=?, nascimento=?, telefone=?,
        email=?, endereco=?, categoria=?, especialidade=?, area=?, disponibilidade=?,
        necessidade=?, observacoes=?, documento_chave=? WHERE id=?""", valores + (id_atual,))
    return id_atual


def participacoes(conn, pessoa_id):
    return conn.execute("SELECT * FROM participacoes WHERE pessoa_id=? ORDER BY data DESC,id DESC",
                        (pessoa_id,)).fetchall()


def excluir(conn, pessoa_id):
    if obter(conn, pessoa_id) is None:
        return False
    if participacoes(conn, pessoa_id):
        conn.execute("DELETE FROM participacoes WHERE pessoa_id=?", (pessoa_id,))
    conn.execute("DELETE FROM pessoas WHERE id=?", (pessoa_id,))
    return True


def resumo(conn):
    return conn.execute("""SELECT grupo,categoria,COUNT(*) AS total FROM pessoas
        GROUP BY grupo,categoria ORDER BY grupo,categoria""").fetchall()


def buscar_login(conn, usuario):
    return conn.execute("SELECT * FROM logins WHERE usuario=?", (usuario,)).fetchone()


def criar_login(conn, usuario, senha_hash, papel):
    conn.execute("INSERT INTO logins(usuario,senha_hash,papel) VALUES (?,?,?)",
                 (usuario, senha_hash, papel))


def registrar_participacao(conn, pessoa_id, atividade, data):
    conn.execute("INSERT INTO participacoes(pessoa_id,atividade,data) VALUES (?,?,?)",
                 (pessoa_id, atividade, data))
