import sqlite3
class Conexao(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()
from pathlib import Path
def conectar(path):
    db=sqlite3.connect(path, factory=Conexao); db.row_factory=sqlite3.Row; db.execute('PRAGMA foreign_keys=ON'); return db
def inicializar_banco(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with conectar(path) as db:
        existe_projetos=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='projetos'").fetchone()
        if existe_projetos:
            colunas={r[1] for r in db.execute('PRAGMA table_info(projetos)')}
            if 'imagem' not in colunas: db.execute('ALTER TABLE projetos ADD COLUMN imagem TEXT')
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='beneficiarios'").fetchone():
            for campo, definicao in [('necessidades', "TEXT NOT NULL DEFAULT ''"), ('prioridade', "TEXT NOT NULL DEFAULT 'pendente'"), ('criado_em', "TEXT DEFAULT ''")]:
                if campo not in {r[1] for r in db.execute('PRAGMA table_info(beneficiarios)')}: db.execute(f'ALTER TABLE beneficiarios ADD COLUMN {campo} {definicao}')
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='visitas_beneficiarios'").fetchone():
            if 'grau_urgencia' not in {r[1] for r in db.execute('PRAGMA table_info(visitas_beneficiarios)')}: db.execute('ALTER TABLE visitas_beneficiarios ADD COLUMN grau_urgencia TEXT')
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='parceiros_doadores'").fetchone():
            for campo, definicao in [('documento','TEXT'),('tipo_apoio','TEXT')]:
                if campo not in {r[1] for r in db.execute('PRAGMA table_info(parceiros_doadores)')}: db.execute(f'ALTER TABLE parceiros_doadores ADD COLUMN {campo} {definicao}')
        db.executescript('''CREATE TABLE IF NOT EXISTS site_conteudo(chave TEXT PRIMARY KEY,valor TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS projetos(id INTEGER PRIMARY KEY,titulo TEXT NOT NULL,objetivo TEXT NOT NULL,tema TEXT,situacao TEXT NOT NULL DEFAULT 'A confirmar',imagem TEXT);
        CREATE TABLE IF NOT EXISTS noticias(id INTEGER PRIMARY KEY,titulo TEXT NOT NULL,resumo TEXT NOT NULL,data TEXT NOT NULL,imagem TEXT);
        CREATE TABLE IF NOT EXISTS acoes_eventos(id INTEGER PRIMARY KEY,projeto_id INTEGER NOT NULL REFERENCES projetos(id),titulo TEXT NOT NULL,data TEXT);
        CREATE TABLE IF NOT EXISTS voluntarios(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,email TEXT UNIQUE NOT NULL,telefone TEXT NOT NULL,cidade TEXT NOT NULL,consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'novo');
        CREATE TABLE IF NOT EXISTS beneficiarios(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,contato TEXT NOT NULL,localizacao TEXT NOT NULL,situacao TEXT NOT NULL,necessidades TEXT NOT NULL DEFAULT '',consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'recebido',prioridade TEXT NOT NULL DEFAULT 'pendente',criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS visitas_beneficiarios(id INTEGER PRIMARY KEY,beneficiario_id INTEGER NOT NULL REFERENCES beneficiarios(id),data TEXT NOT NULL,responsavel TEXT NOT NULL,observacoes TEXT,grau_urgencia TEXT);
        CREATE TABLE IF NOT EXISTS parceiros_doadores(id INTEGER PRIMARY KEY,tipo_pessoa TEXT NOT NULL,nome TEXT NOT NULL,email TEXT,telefone TEXT,consentimento INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'interessado',documento TEXT,tipo_apoio TEXT);
        CREATE TABLE IF NOT EXISTS doacoes_parcerias(id INTEGER PRIMARY KEY,parceiro_id INTEGER NOT NULL REFERENCES parceiros_doadores(id),tipo TEXT NOT NULL,valor REAL,descricao TEXT,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS usuarios_admin(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,senha_hash TEXT NOT NULL,perfil TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS logs_auditoria(id INTEGER PRIMARY KEY,usuario_id INTEGER REFERENCES usuarios_admin(id),acao TEXT NOT NULL,entidade TEXT NOT NULL,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_vol_status ON voluntarios(status);
        CREATE INDEX IF NOT EXISTS idx_benef_status ON beneficiarios(status,prioridade);
        CREATE INDEX IF NOT EXISTS idx_parceiros_status ON parceiros_doadores(status);
        INSERT OR IGNORE INTO site_conteudo(chave,valor) VALUES
        ('hero_titulo','Cuidado que vira direito. Solidariedade que transforma.'),
        ('hero_texto','Há mais de 27 anos, caminhamos ao lado de pessoas, famílias e comunidades em situação de vulnerabilidade em Roraima, promovendo direitos humanos, saúde e inclusão social com dignidade e respeito à diversidade.'),
        ('missao','Transformar realidades vulneráveis por meio de ações socioassistenciais, promoção da saúde e defesa dos direitos humanos.'),
        ('visao','Ser referência na Amazônia na construção de uma sociedade mais justa, equitativa e livre de discriminações.'),
        ('endereco','Rua Oeste, nº 225, Conjunto Cruviana I, Bairro Equatorial, Boa Vista - RR'),
        ('cnpj','03.257.182/0001-79');
        INSERT OR IGNORE INTO projetos(id,titulo,objetivo,tema,situacao) VALUES
        (1001,'Viva Protegidx','Ações de prevenção combinada, orientação em saúde, direitos humanos e acesso à rede de proteção.','Saúde e direitos','Programa permanente'),
        (1002,'Trans-formando Identidades','Iniciativa de cidadania e acesso à retificação de nome e gênero no registro civil, em articulação com a Defensoria Pública de Roraima.','Direitos e inclusão','Ação divulgada em junho de 2026'),
        (1003,'Segurança Alimentar e Nutricional','Distribuição gratuita de alimentos em parceria com o Mesa Brasil - SESC/RR.','Segurança alimentar','Ação institucional');
        INSERT OR IGNORE INTO noticias(id,titulo,resumo,data) VALUES
        (1001,'Dia Mundial do Refugiado: Solidariedade, Direitos e Inclusão para Transformar Vidas','Reflexão sobre acolhimento, direitos e inclusão de pessoas refugiadas em Roraima.','2026-06-20'),
        (1002,'Grupo Sabá leva dignidade, prevenção e esperança a migrantes e pessoas em situação de rua em Boa Vista','Ação do Programa Viva Protegidx com kits de prevenção, informação em saúde e orientação sobre direitos.','2025-01-09');''')

