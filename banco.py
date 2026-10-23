import sqlite3
from pathlib import Path
def conectar(path):
    db=sqlite3.connect(path); db.row_factory=sqlite3.Row; db.execute('PRAGMA foreign_keys=ON'); return db
def inicializar_banco(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with conectar(path) as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS projetos(id INTEGER PRIMARY KEY,titulo TEXT NOT NULL,objetivo TEXT NOT NULL,tema TEXT,situacao TEXT NOT NULL DEFAULT 'A confirmar');
        CREATE TABLE IF NOT EXISTS acoes_eventos(id INTEGER PRIMARY KEY,projeto_id INTEGER NOT NULL REFERENCES projetos(id),titulo TEXT NOT NULL,data TEXT);
        CREATE TABLE IF NOT EXISTS voluntarios(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,email TEXT UNIQUE NOT NULL,telefone TEXT NOT NULL,cidade TEXT NOT NULL,consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'novo');
        CREATE TABLE IF NOT EXISTS beneficiarios(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,contato TEXT NOT NULL,localizacao TEXT NOT NULL,situacao TEXT NOT NULL,consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'recebido');
        CREATE TABLE IF NOT EXISTS visitas_beneficiarios(id INTEGER PRIMARY KEY,beneficiario_id INTEGER NOT NULL REFERENCES beneficiarios(id),data TEXT NOT NULL,responsavel TEXT NOT NULL,observacoes TEXT);
        CREATE TABLE IF NOT EXISTS parceiros_doadores(id INTEGER PRIMARY KEY,tipo_pessoa TEXT NOT NULL,nome TEXT NOT NULL,email TEXT,telefone TEXT,consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'interessado');
        CREATE TABLE IF NOT EXISTS doacoes_parcerias(id INTEGER PRIMARY KEY,parceiro_id INTEGER NOT NULL REFERENCES parceiros_doadores(id),tipo TEXT NOT NULL,valor REAL);
        CREATE TABLE IF NOT EXISTS usuarios_admin(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,senha_hash TEXT NOT NULL,perfil TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS logs_auditoria(id INTEGER PRIMARY KEY,usuario_id INTEGER REFERENCES usuarios_admin(id),acao TEXT NOT NULL,entidade TEXT NOT NULL,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_vol_status ON voluntarios(status);''')
