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
        db.executescript('''CREATE TABLE IF NOT EXISTS agendamentos(id INTEGER PRIMARY KEY,beneficiario_id INTEGER NOT NULL REFERENCES beneficiarios(id),data TEXT NOT NULL,responsavel TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'agendada');
        CREATE TABLE IF NOT EXISTS atendimentos(id INTEGER PRIMARY KEY,beneficiario_id INTEGER NOT NULL REFERENCES beneficiarios(id),status TEXT NOT NULL,descricao TEXT NOT NULL,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS midias(id INTEGER PRIMARY KEY,projeto_id INTEGER REFERENCES projetos(id),titulo TEXT NOT NULL,url TEXT NOT NULL,fonte TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS site_conteudo(chave TEXT PRIMARY KEY,valor TEXT NOT NULL);
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
        ''')
        for tabela, campos in {
            'voluntarios': [('disponibilidade', "TEXT DEFAULT ''"), ('interesses', "TEXT DEFAULT ''")],
            'doacoes_parcerias': [('descricao', "TEXT DEFAULT ''"), ('criado_em', "TEXT DEFAULT ''")],
        }.items():
            existentes = {r[1] for r in db.execute(f'PRAGMA table_info({tabela})')}
            for campo, definicao in campos:
                if campo not in existentes:
                    db.execute(f'ALTER TABLE {tabela} ADD COLUMN {campo} {definicao}')


def buscar_painel(path, categoria, busca, status, pagina, tamanho=20):
    configuracao = {
        'voluntarios': ('voluntarios', ['nome','email','telefone','cidade','interesses']),
        'parceiros': ('parceiros_doadores', ['nome','email','telefone','tipo_apoio']),
        'beneficiarios': ('beneficiarios', ['nome','contato','localizacao','necessidades']),
    }
    tabela, campos = configuracao[categoria]
    termo = '%' + busca.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    where = '(' + ' OR '.join(f"{campo} LIKE ? ESCAPE '\\'" for campo in campos) + ')'
    parametros = [termo] * len(campos)
    if status:
        where += ' AND status=?'
        parametros.append(status)
    with conectar(path) as db:
        quantidade = db.execute(f'SELECT COUNT(*) FROM {tabela} WHERE {where}', parametros).fetchone()[0]
        pagina = min(pagina,max(1,(quantidade+tamanho-1)//tamanho))
        registros = db.execute(f'SELECT * FROM {tabela} WHERE {where} ORDER BY id DESC LIMIT ? OFFSET ?',
                               [*parametros, tamanho, (pagina-1)*tamanho]).fetchall()
        situacoes = [r[0] for r in db.execute(f'SELECT DISTINCT status FROM {tabela} ORDER BY status')]
    return registros, quantidade, situacoes


def conteudo_paginado(path, tabela, busca, pagina):
    assert tabela in ('projetos','noticias','midias')
    where = 'id>=1001' if tabela!='midias' else '1=1'
    with conectar(path) as db:
        total=db.execute(f'SELECT COUNT(*) FROM {tabela} WHERE {where} AND instr(lower(titulo),lower(?))>0',(busca,)).fetchone()[0]
        pagina=min(pagina,max(1,(total+19)//20))
        rows=db.execute(f'SELECT * FROM {tabela} WHERE {where} AND instr(lower(titulo),lower(?))>0 ORDER BY id DESC LIMIT 20 OFFSET ?',(busca,(pagina-1)*20)).fetchall()
    return rows,total,pagina

def conteudo_individual(path,tabela,identificador):
    assert tabela in ('projetos','noticias','midias')
    with conectar(path) as db:
        return db.execute(f'SELECT * FROM {tabela} WHERE id=?',(identificador,)).fetchone()

def gravar_conteudo(path,tabela,identificador,dados,usuario):
    permitidos={'projetos':('titulo','objetivo','tema','situacao','imagem'),'noticias':('titulo','resumo','data','imagem'),'midias':('titulo','url','fonte','projeto_id')}
    campos=permitidos[tabela]
    with conectar(path) as db:
        db.execute('BEGIN IMMEDIATE')
        valores=[dados[k] for k in campos]
        if identificador:
            db.execute(f'UPDATE {tabela} SET '+','.join(k+'=?' for k in campos)+' WHERE id=?',[*valores,identificador])
        else:
            identificador=max(1001,db.execute(f'SELECT COALESCE(MAX(id),0)+1 FROM {tabela}').fetchone()[0])
            db.execute(f'INSERT INTO {tabela}(id,'+','.join(campos)+') VALUES('+','.join('?' for _ in range(len(campos)+1))+')',[identificador,*valores])
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)',(usuario,'salvar conteúdo',f'{tabela}:{identificador}'))

def remover_conteudo(path,tabela,identificador,usuario):
    assert tabela in ('projetos','noticias','midias')
    with conectar(path) as db:
        if tabela=='projetos':
            db.execute('DELETE FROM midias WHERE projeto_id=?',(identificador,))
            db.execute('DELETE FROM acoes_eventos WHERE projeto_id=?',(identificador,))
        db.execute(f'DELETE FROM {tabela} WHERE id=?',(identificador,))
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)',(usuario,'excluir conteúdo',f'{tabela}:{identificador}'))

def salvar_textos(path,dados,usuario):
    with conectar(path) as db:
        db.executemany('INSERT INTO site_conteudo(chave,valor) VALUES(?,?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor',dados.items())
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)',(usuario,'atualizar textos e banner','site'))

def editar_solicitacao(path,identificador,dados,usuario):
    with conectar(path) as db:
        db.execute('UPDATE beneficiarios SET nome=?,contato=?,localizacao=?,situacao=?,necessidades=? WHERE id=?',
                   [dados[k] for k in ('nome','contato','localizacao','situacao','necessidades')]+[identificador])
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)',(usuario,'editar solicitação',f'beneficiario:{identificador}'))

def obter_conteudo(path):
    with conectar(path) as db:
        return {r['chave']: r['valor'] for r in db.execute('SELECT chave,valor FROM site_conteudo')}


def listar_projetos(path, termo=''):
    with conectar(path) as db:
        return db.execute('SELECT * FROM projetos WHERE id>=1001 AND (titulo LIKE ? OR tema LIKE ?) ORDER BY titulo',
                          (f'%{termo}%', f'%{termo}%')).fetchall()


def obter_projeto(path, identificador):
    with conectar(path) as db:
        return db.execute('SELECT * FROM projetos WHERE id=? AND id>=1001', (identificador,)).fetchone()


def listar_midias_projeto(path, identificador):
    with conectar(path) as db:
        return db.execute('SELECT * FROM midias WHERE projeto_id=? ORDER BY id DESC', (identificador,)).fetchall()


def listar_midias(path):
    with conectar(path) as db:
        return db.execute('SELECT * FROM midias ORDER BY id DESC').fetchall()


def listar_noticias(path):
    with conectar(path) as db:
        return db.execute('SELECT * FROM noticias WHERE id>=1001 ORDER BY data DESC LIMIT 3').fetchall()


def resumo_projetos(path):
    with conectar(path) as db:
        return db.execute('SELECT tema,COUNT(*) AS quantidade FROM projetos WHERE id>=1001 GROUP BY tema ORDER BY quantidade DESC,tema').fetchall()


def resumo_voluntarios_por_cidade(path):
    with conectar(path) as db:
        return db.execute('SELECT cidade,COUNT(*) AS quantidade FROM voluntarios GROUP BY cidade ORDER BY quantidade DESC,cidade').fetchall()


def totais(path):
    with conectar(path) as db:
        return {
            'projetos': db.execute('SELECT COUNT(*) FROM projetos WHERE id>=1001').fetchone()[0],
            'voluntarios': db.execute('SELECT COUNT(*) FROM voluntarios').fetchone()[0],
            'beneficiarios': db.execute('SELECT COUNT(*) FROM beneficiarios').fetchone()[0],
            'parceiros': db.execute('SELECT COUNT(*) FROM parceiros_doadores').fetchone()[0],
        }


def listar_painel(path):
    with conectar(path) as db:
        beneficiarios = db.execute('SELECT * FROM beneficiarios ORDER BY CASE prioridade WHEN "alta" THEN 0 WHEN "media" THEN 1 WHEN "pendente" THEN 2 ELSE 3 END,criado_em').fetchall()
        voluntarios = db.execute('SELECT * FROM voluntarios ORDER BY id DESC').fetchall()
        parceiros = db.execute('SELECT * FROM parceiros_doadores ORDER BY id DESC').fetchall()
    return beneficiarios, voluntarios, parceiros


def registrar_voluntario(path, dados):
    with conectar(path) as db:
        db.execute('INSERT INTO voluntarios(nome,email,telefone,cidade,consentimento,disponibilidade,interesses) VALUES(?,?,?,?,1,?,?)',
                   (dados['nome'], dados['email'], dados['telefone'], dados['cidade'], dados['disponibilidade'], dados['interesses']))


def registrar_beneficiario(path, dados):
    with conectar(path) as db:
        db.execute('INSERT INTO beneficiarios(nome,contato,localizacao,situacao,necessidades,consentimento) VALUES(?,?,?,?,?,1)',
                   (dados['nome'], dados['contato'], dados['localizacao'], dados['situacao'], dados['necessidades']))


def registrar_parceiro(path, dados):
    with conectar(path) as db:
        db.execute('INSERT INTO parceiros_doadores(tipo_pessoa,nome,email,telefone,consentimento,tipo_apoio) VALUES(?,?,?,?,1,?)',
                   (dados['tipo_pessoa'], dados['nome'], dados['email'], dados['telefone'], dados['tipo_apoio']))


def obter_admin(path, identificador):
    with conectar(path) as db:
        return db.execute('SELECT id,perfil FROM usuarios_admin WHERE id=?', (identificador,)).fetchone()


def obter_admin_email(path, email):
    with conectar(path) as db:
        return db.execute('SELECT * FROM usuarios_admin WHERE email=?', (email,)).fetchone()


def ha_admin(path):
    with conectar(path) as db:
        return db.execute('SELECT 1 FROM usuarios_admin LIMIT 1').fetchone() is not None


def criar_admin(path, email, senha_hash):
    with conectar(path) as db:
        db.execute('INSERT INTO usuarios_admin(email,senha_hash,perfil) VALUES(?,?,?)', (email,senha_hash,'admin'))


def listar_midias_admin(path):
    return listar_midias(path)


def obter_beneficiario(path, identificador):
    with conectar(path) as db:
        return db.execute('SELECT * FROM beneficiarios WHERE id=?', (identificador,)).fetchone()


def historico_beneficiario(path, identificador):
    with conectar(path) as db:
        return {t: db.execute(f'SELECT * FROM {t} WHERE beneficiario_id=? ORDER BY id DESC', (identificador,)).fetchall()
                for t in ('agendamentos','visitas_beneficiarios','atendimentos')}


def agendar_visita(path, identificador, dia, responsavel, usuario_id):
    with conectar(path) as db:
        db.execute("UPDATE agendamentos SET status='reagendada' WHERE beneficiario_id=? AND status='agendada'", (identificador,))
        db.execute('INSERT INTO agendamentos(beneficiario_id,data,responsavel) VALUES(?,?,?)', (identificador,dia,responsavel))
        db.execute("UPDATE beneficiarios SET status='visita agendada' WHERE id=?", (identificador,))
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)', (usuario_id,'agendar visita',f'beneficiario:{identificador}'))


def registrar_atendimento(path, identificador, status, descricao, usuario_id):
    with conectar(path) as db:
        db.execute('INSERT INTO atendimentos(beneficiario_id,status,descricao) VALUES(?,?,?)', (identificador,status,descricao))
        db.execute('UPDATE beneficiarios SET status=? WHERE id=?', (status,identificador))
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)', (usuario_id,'registrar atendimento',f'beneficiario:{identificador}'))


def atualizar_status_cadastro(path, tabela, status, identificador):
    with conectar(path) as db:
        return db.execute(f'UPDATE {tabela} SET status=? WHERE id=?', (status,identificador)).rowcount


def listar_doacoes(path):
    with conectar(path) as db:
        parceiros = db.execute('SELECT id,nome FROM parceiros_doadores ORDER BY nome').fetchall()
        registros = db.execute('SELECT d.*,p.nome FROM doacoes_parcerias d JOIN parceiros_doadores p ON p.id=d.parceiro_id ORDER BY d.id DESC').fetchall()
    return parceiros, registros


def registrar_doacao(path, parceiro, tipo, valor, descricao, usuario_id):
    with conectar(path) as db:
        if not db.execute('SELECT id FROM parceiros_doadores WHERE id=?',(parceiro,)).fetchone():
            return False
        db.execute('INSERT INTO doacoes_parcerias(parceiro_id,tipo,valor,descricao,criado_em) VALUES(?,?,?,?,CURRENT_TIMESTAMP)', (parceiro,tipo,valor,descricao))
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)', (usuario_id,'doação registrada',f'parceiro:{parceiro}'))
    return True


def listar_conteudo_admin(path):
    with conectar(path) as db:
        projetos = db.execute('SELECT * FROM projetos WHERE id>=1001 ORDER BY id').fetchall()
        textos = db.execute('SELECT chave,valor FROM site_conteudo WHERE chave IN (?,?,?,?) ORDER BY chave', ('hero_titulo','hero_texto','missao','visao')).fetchall()
    return projetos, textos


def inserir_dados_iniciais(path):
    """Prepara conteúdo demonstrativo sem sobrescrever dados cadastrados."""
    with conectar(path) as db:
        db.executemany('INSERT OR IGNORE INTO site_conteudo(chave,valor) VALUES(?,?)', [
            ('hero_titulo','Cuidado que vira direito. Solidariedade que transforma.'),
            ('hero_texto','Há mais de 27 anos, caminhamos ao lado de pessoas, famílias e comunidades em situação de vulnerabilidade em Roraima, promovendo direitos humanos, saúde e inclusão social com dignidade e respeito à diversidade.'),
            ('missao','Transformar realidades vulneráveis por meio de ações socioassistenciais, promoção da saúde e defesa dos direitos humanos.'),
            ('visao','Ser referência na Amazônia na construção de uma sociedade mais justa, equitativa e livre de discriminações.'),
            ('endereco','Rua Oeste, nº 225, Conjunto Cruviana I, Bairro Equatorial, Boa Vista - RR'),
            ('cnpj','03.257.182/0001-79'),
        ])
        db.executemany('INSERT OR IGNORE INTO projetos(id,titulo,objetivo,tema,situacao) VALUES(?,?,?,?,?)', [
            (1001,'Viva Protegidx','Ações de prevenção combinada, orientação em saúde, direitos humanos e acesso à rede de proteção.','Saúde e direitos','Programa permanente'),
            (1002,'Trans-formando Identidades','Iniciativa de cidadania e acesso à retificação de nome e gênero no registro civil, em articulação com a Defensoria Pública de Roraima.','Direitos e inclusão','Ação institucional'),
            (1003,'Segurança Alimentar e Nutricional','Distribuição gratuita de alimentos em parceria com o Mesa Brasil - SESC/RR.','Segurança alimentar','Ação institucional'),
        ])
        db.executemany('INSERT OR IGNORE INTO noticias(id,titulo,resumo,data) VALUES(?,?,?,?)', [
            (1001,'Dia Mundial do Refugiado: Solidariedade, Direitos e Inclusão para Transformar Vidas','Reflexão sobre acolhimento, direitos e inclusão de pessoas refugiadas em Roraima.','2026-06-20'),
            (1002,'Grupo Sabá leva dignidade, prevenção e esperança a migrantes e pessoas em situação de rua em Boa Vista','Ação do Programa Viva Protegidx com kits de prevenção, informação em saúde e orientação sobre direitos.','2025-01-09'),
        ])
        for numero in range(1,6):
            db.execute('INSERT OR IGNORE INTO midias(id,projeto_id,titulo,url,fonte) VALUES(?,?,?,?,?)',
                       (numero,1001,f'Registro de ação — acervo Grupo Sabá {numero}',f'https://gruposaba.org/wp-content/uploads/2025/01/0{numero}.png','https://gruposaba.org/fotos/'))


def salvar_texto(path, chave, valor):
    with conectar(path) as db:
        db.execute('INSERT INTO site_conteudo(chave,valor) VALUES(?,?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor', (chave,valor))
        return 1


def salvar_projeto(path, identificador, valores):
    with conectar(path) as db:
        db.execute('BEGIN IMMEDIATE')
        if identificador:
            cur=db.execute('UPDATE projetos SET titulo=?,objetivo=?,tema=?,situacao=?,imagem=? WHERE id=? AND id>=1001', (*valores,identificador))
            return cur.rowcount if cur.rowcount else (1 if db.execute('SELECT 1 FROM projetos WHERE id=? AND id>=1001',(identificador,)).fetchone() else 0)
        identificador=max(1001,db.execute('SELECT COALESCE(MAX(id),0)+1 FROM projetos').fetchone()[0])
        db.execute('INSERT INTO projetos(id,titulo,objetivo,tema,situacao,imagem) VALUES(?,?,?,?,?,?)', (identificador,*valores))
        return identificador


def excluir_projeto(path, identificador):
    with conectar(path) as db:
        if not db.execute('SELECT id FROM projetos WHERE id=? AND id>=1001',(identificador,)).fetchone():
            return False
        db.execute('DELETE FROM acoes_eventos WHERE projeto_id=?',(identificador,))
        db.execute('DELETE FROM midias WHERE projeto_id=?',(identificador,))
        db.execute('DELETE FROM projetos WHERE id=? AND id>=1001',(identificador,))
    return True


def salvar_foto(path, projeto, titulo, url, fonte, usuario_id):
    with conectar(path) as db:
        if projeto and not db.execute('SELECT id FROM projetos WHERE id=? AND id>=1001',(projeto,)).fetchone():
            return False
        db.execute('INSERT INTO midias(projeto_id,titulo,url,fonte) VALUES(?,?,?,?)', (projeto,titulo,url,fonte))
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)', (usuario_id,'foto publicada','galeria'))
    return True


def registrar_visita(path, identificador, dia, responsavel, observacoes, urgencia, usuario_id):
    estado = 'priorizado' if urgencia == 'alta' else 'em avaliacao'
    with conectar(path) as db:
        if not db.execute('SELECT id FROM beneficiarios WHERE id=?',(identificador,)).fetchone():
            return False
        db.execute('INSERT INTO visitas_beneficiarios(beneficiario_id,data,responsavel,observacoes,grau_urgencia) VALUES(?,?,?,?,?)', (identificador,dia,responsavel,observacoes,urgencia))
        db.execute('UPDATE beneficiarios SET prioridade=?,status=? WHERE id=?', (urgencia,estado,identificador))
        db.execute("UPDATE agendamentos SET status='realizada' WHERE beneficiario_id=? AND status='agendada' AND data<=?", (identificador,dia))
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)', (usuario_id,'visita registrada',f'beneficiario:{identificador}'))
    return True


def registrar_log(path, usuario_id, acao, entidade):
    with conectar(path) as db:
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)',(usuario_id,acao,entidade))


def listar_voluntarios_por_cidade(path):
    with conectar(path) as db:
        return db.execute('SELECT cidade,COUNT(*) AS quantidade FROM voluntarios GROUP BY cidade ORDER BY quantidade DESC,cidade').fetchall()


def atualizar_voluntario(path, identificador, dados):
    with conectar(path) as db:
        try:
            return db.execute('UPDATE voluntarios SET nome=?,email=?,telefone=?,cidade=?,disponibilidade=?,interesses=? WHERE id=?',
                              (dados['nome'],dados['email'],dados['telefone'],dados['cidade'],dados['disponibilidade'],dados['interesses'],identificador)).rowcount
        except sqlite3.IntegrityError:
            return -1


def excluir_voluntario(path, identificador):
    with conectar(path) as db:
        return db.execute('DELETE FROM voluntarios WHERE id=?',(identificador,)).rowcount


def atualizar_parceiro(path, identificador, dados):
    with conectar(path) as db:
        return db.execute('UPDATE parceiros_doadores SET tipo_pessoa=?,nome=?,email=?,telefone=?,tipo_apoio=? WHERE id=?',
                          (dados['tipo_pessoa'],dados['nome'],dados['email'],dados['telefone'],dados['tipo_apoio'],identificador)).rowcount


def excluir_parceiro(path, identificador):
    with conectar(path) as db:
        if db.execute('SELECT id FROM doacoes_parcerias WHERE parceiro_id=? LIMIT 1',(identificador,)).fetchone():
            return False
        return db.execute('DELETE FROM parceiros_doadores WHERE id=?',(identificador,)).rowcount > 0


def obter_voluntario(path, identificador):
    with conectar(path) as db:
        return db.execute('SELECT * FROM voluntarios WHERE id=?',(identificador,)).fetchone()


def obter_parceiro(path, identificador):
    with conectar(path) as db:
        return db.execute('SELECT * FROM parceiros_doadores WHERE id=?',(identificador,)).fetchone()

