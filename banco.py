import sqlite3
from pathlib import Path
def conectar(path):
    db=sqlite3.connect(path); db.row_factory=sqlite3.Row; db.execute('PRAGMA foreign_keys=ON'); return db
def inicializar_banco(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with conectar(path) as db:
        existe_projetos=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='projetos'").fetchone()
        if existe_projetos:
            colunas={r[1] for r in db.execute('PRAGMA table_info(projetos)')}
            if 'imagem' not in colunas: db.execute('ALTER TABLE projetos ADD COLUMN imagem TEXT')
        db.executescript('''CREATE TABLE IF NOT EXISTS site_conteudo(chave TEXT PRIMARY KEY,valor TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS projetos(id INTEGER PRIMARY KEY,titulo TEXT NOT NULL,objetivo TEXT NOT NULL,tema TEXT,situacao TEXT NOT NULL DEFAULT 'A confirmar',imagem TEXT);
        CREATE TABLE IF NOT EXISTS noticias(id INTEGER PRIMARY KEY,titulo TEXT NOT NULL,resumo TEXT NOT NULL,data TEXT NOT NULL,imagem TEXT);
        CREATE TABLE IF NOT EXISTS acoes_eventos(id INTEGER PRIMARY KEY,projeto_id INTEGER NOT NULL REFERENCES projetos(id),titulo TEXT NOT NULL,data TEXT);
        CREATE TABLE IF NOT EXISTS voluntarios(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,email TEXT UNIQUE NOT NULL,telefone TEXT NOT NULL,cidade TEXT NOT NULL,consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'novo');
        CREATE TABLE IF NOT EXISTS beneficiarios(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,contato TEXT NOT NULL,localizacao TEXT NOT NULL,situacao TEXT NOT NULL,consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'recebido');
        CREATE TABLE IF NOT EXISTS visitas_beneficiarios(id INTEGER PRIMARY KEY,beneficiario_id INTEGER NOT NULL REFERENCES beneficiarios(id),data TEXT NOT NULL,responsavel TEXT NOT NULL,observacoes TEXT);
        CREATE TABLE IF NOT EXISTS parceiros_doadores(id INTEGER PRIMARY KEY,tipo_pessoa TEXT NOT NULL,nome TEXT NOT NULL,email TEXT,telefone TEXT,consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'interessado');
        CREATE TABLE IF NOT EXISTS doacoes_parcerias(id INTEGER PRIMARY KEY,parceiro_id INTEGER NOT NULL REFERENCES parceiros_doadores(id),tipo TEXT NOT NULL,valor REAL);
        CREATE TABLE IF NOT EXISTS usuarios_admin(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,senha_hash TEXT NOT NULL,perfil TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS logs_auditoria(id INTEGER PRIMARY KEY,usuario_id INTEGER REFERENCES usuarios_admin(id),acao TEXT NOT NULL,entidade TEXT NOT NULL,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_vol_status ON voluntarios(status);
        INSERT OR IGNORE INTO site_conteudo(chave,valor) VALUES
        ('hero_titulo','Cuidado que vira direito. Solidariedade que transforma.'),
        ('hero_texto','Há mais de 27 anos, caminhamos ao lado de pessoas, famílias e comunidades em situação de vulnerabilidade em Roraima, promovendo direitos humanos, saúde e inclusão social com dignidade e respeito à diversidade.'),
        ('missao','Transformar realidades vulneráveis por meio de ações socioassistenciais, promoção da saúde e defesa dos direitos humanos.'),
        ('visao','Ser referência na Amazônia na construção de uma sociedade mais justa, equitativa e livre de discriminações.'),
        ('endereco','Rua Oeste, nº 225, Conjunto Cruviana I, Bairro Equatorial, Boa Vista - RR'),
        ('cnpj','03.257.182/0001-79');
        INSERT OR IGNORE INTO projetos(titulo,objetivo,tema,situacao,imagem) VALUES
        ('Viva Protegidx','Prevenção, informação e acesso à rede de proteção e saúde.','Saúde e direitos','Em atuação','https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=900&q=80'),
        ('Trans-formando Identidades','Promover dignidade, cidadania e garantia de direitos.','Inclusão social','Em atuação','https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=900&q=80'),
        ('Rede de cuidado','Articular pessoas e instituições para ampliar o cuidado no território.','Trabalho em rede','Contínuo','https://images.unsplash.com/photo-1559027615-cd4628902d4a?auto=format&fit=crop&w=900&q=80');
        INSERT OR IGNORE INTO noticias(titulo,resumo,data,imagem) VALUES
        ('Dia Mundial do Refugiado: solidariedade, direitos e inclusão','Informação e acolhimento para transformar vidas.','2026-06-20','https://images.unsplash.com/photo-1469571486292-0ba58a3f068b?auto=format&fit=crop&w=900&q=80'),
        ('Grupo Sabá fortalece ações de prevenção e promoção da saúde','Voluntariado e trabalho em rede ampliam o alcance das ações.','2026-01-09','https://images.unsplash.com/photo-1504159506876-f8338247a14a?auto=format&fit=crop&w=900&q=80');''')
