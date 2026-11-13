import click
import os
import sqlite3
import secrets
import hmac
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import banco
from banco import inicializar_banco
from validacoes import validar_beneficiario, validar_email, validar_parceiro, validar_voluntario

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=65536)
DB_PATH = Path(os.environ.get('SABA_DATABASE', str(Path(__file__).resolve().parent / 'grupo_saba.sqlite3')))
inicializar_banco(DB_PATH)

@app.before_request
def proteger_formularios():
    session.setdefault('csrf', secrets.token_hex(32))
    if request.method == 'POST' and any(len(v) > 2000 for v in request.form.values()):
        abort(400)
    if request.method == 'POST' and not hmac.compare_digest(session['csrf'], request.form.get('_csrf', '')):
        abort(400)

@app.after_request
def finalizar_resposta(response):
    if response.mimetype == 'text/html':
        import re
        token = session.get('csrf', '')
        html = re.sub(r'(<form[^>]*method="post"[^>]*>)', lambda m: m[1] + '<input type="hidden" name="_csrf" value="' + token + '">', response.get_data(as_text=True))
        response.set_data(html)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    if request.path.startswith('/admin'):
        response.headers['Cache-Control'] = 'no-store'
    return response


def site_content():
    return banco.obter_conteudo(DB_PATH)


@app.context_processor
def conteudo_global():
    return {'site_cfg': site_content()}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        usuario = banco.obter_admin(DB_PATH, session.get('admin_id'))
        if not usuario:
            return redirect(url_for('admin_login', next=request.path))
        if usuario['perfil'] != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.route('/')
def inicio():
    projetos = banco.listar_projetos(DB_PATH)[:3]
    noticias = banco.listar_noticias(DB_PATH)
    return render_template('inicio.html', site=site_content(), projetos=projetos, noticias=noticias)


@app.route('/quem-somos')
def quem_somos():
    return render_template('quem-somos.html', site=site_content())


@app.route('/projetos')
def projetos():
    projetos = banco.listar_projetos(DB_PATH, request.args.get('q','').strip())
    return render_template('projetos.html', projetos=projetos)


@app.route('/transparencia')
def transparencia():
    return render_template('transparencia.html')


@app.route('/como-ajudar')
def como_ajudar():
    return render_template('como-ajudar.html')


def ler_cadastro(*campos):
    """Lê os campos do formulário público antes da validação."""
    dados = {}
    for campo in campos:
        dados[campo] = request.form.get(campo, '').strip()
    dados['consentimento'] = request.form.get('consentimento')
    return dados


@app.route('/voluntariado', methods=['GET', 'POST'])
def voluntariado():
    dados = ler_cadastro('nome', 'email', 'telefone', 'cidade', 'disponibilidade', 'interesses')
    if request.method == 'POST':
        erros=validar_voluntario(dados)
        if erros:
            flash('Confira os campos: '+' '.join(erros.values()), 'erro')
            return render_template('voluntariado.html', dados=dados), 400
        try:
            dados['email']=dados['email'].lower()
            banco.registrar_voluntario(DB_PATH,dados)
        except sqlite3.IntegrityError:
            flash('Este e-mail já está cadastrado ou não foi possível receber seu interesse.', 'erro')
            return render_template('voluntariado.html', dados=dados), 400
        flash('Recebemos seu interesse. A equipe do Grupo Sabá poderá entrar em contato.', 'sucesso')
        return redirect(url_for('voluntariado'))
    return render_template('voluntariado.html', dados=dados)


@app.route('/privacidade')
def privacidade():
    return render_template('privacidade.html')


@app.cli.command('inicializar-admin')
def inicializar_admin():
    """Configura a primeira conta pelo terminal em uma instalação nova."""
    if banco.ha_admin(DB_PATH):
        raise click.ClickException('Já existe uma conta. Use Adicionar conta no painel.')
    email = click.prompt('E-mail').strip().lower()
    senha = click.prompt('Senha', hide_input=True, confirmation_prompt=True)
    if not validar_email(email) or not 12 <= len(senha) <= 2000:
        raise click.ClickException('Informe um e-mail válido e uma senha de 12 a 2000 caracteres.')
    with banco.conectar(DB_PATH) as db:
        insercao = db.execute(
            "INSERT INTO usuarios_admin(email, senha_hash, perfil) "
            "SELECT ?, ?, 'admin' WHERE NOT EXISTS (SELECT 1 FROM usuarios_admin)",
            (email, generate_password_hash(senha)),
        )
        if not insercao.rowcount:
            raise click.ClickException('Já existe uma conta. Use Adicionar conta no painel.')
    click.echo('Conta inicial criada.')


@app.route('/admin/contas/nova', methods=['GET', 'POST'])
@login_required
def adicionar_conta():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        if not validar_email(email) or len(senha) < 12:
            flash('Informe um e-mail válido e uma senha com pelo menos 12 caracteres.', 'erro')
            return render_template('admin_conta.html', email=email), 400
        try:
            banco.criar_admin(DB_PATH, email, generate_password_hash(senha))
        except sqlite3.IntegrityError:
            flash('Já existe uma conta com esse e-mail.', 'erro')
            return render_template('admin_conta.html', email=email), 409
        flash('Conta administrativa adicionada.', 'sucesso')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_conta.html')


@app.route('/admin/entrar', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = banco.obter_admin_email(DB_PATH,email)
        if user and check_password_hash(user['senha_hash'], request.form.get('senha', '')):
            session.clear()
            session['admin_id'] = user['id']
            return redirect(url_for('admin_dashboard'))
        flash('E-mail ou senha incorretos.', 'erro')
    return render_template('admin_login.html')


@app.post('/admin/sair')
@login_required
def admin_logout():
    session.clear()
    return redirect(url_for('inicio'))


@app.route('/admin')
@login_required
def admin_dashboard():
    totais = banco.totais(DB_PATH)
    categoria = request.args.get('categoria')
    if not categoria:
        return render_template('admin_inicio.html', totais=totais)
    if categoria not in ('voluntarios', 'parceiros', 'beneficiarios'):
        abort(400)
    busca = request.args.get('q', '').strip()[:120]
    status = request.args.get('status', '').strip()
    pagina = max(1, request.args.get('pagina', 1, type=int))
    por_pagina = 6
    registros, quantidade, situacoes = banco.buscar_painel(DB_PATH, categoria, busca, status, pagina, tamanho=por_pagina)
    ultima = max(1, (quantidade + por_pagina - 1) // por_pagina)
    if pagina > ultima:
        return redirect(url_for('admin_dashboard', categoria=categoria, q=busca, status=status, pagina=ultima))
    return render_template('admin_busca.html', pesquisou='q' in request.args or 'status' in request.args, totais=totais, registros=registros,
                           quantidade=quantidade, situacoes=situacoes, categoria=categoria,
                           busca=busca, status=status, pagina=pagina, paginas=ultima)


@app.route('/apoio', methods=['GET', 'POST'])
def solicitar_apoio():
    dados = ler_cadastro('nome', 'contato', 'localizacao', 'situacao', 'necessidades')
    if request.method == 'POST':
        erros=validar_beneficiario(dados)
        if erros:
            flash('Confira os campos: '+' '.join(erros.values()), 'erro')
            return render_template('apoio.html', dados=dados), 400
        banco.registrar_beneficiario(DB_PATH,dados)
        flash('Sua solicitação foi recebida. A equipe avaliará as informações e, se necessário, combinará uma visita.', 'sucesso')
        return redirect(url_for('solicitar_apoio'))
    return render_template('apoio.html', dados=dados)


@app.route('/parcerias', methods=['GET', 'POST'])
def parcerias():
    dados = ler_cadastro('tipo_pessoa', 'nome', 'email', 'telefone', 'tipo_apoio')
    if request.method == 'POST':
        erros=validar_parceiro(dados)
        if erros:
            flash('Confira os campos: '+' '.join(erros.values()), 'erro')
            return render_template('parcerias.html', dados=dados), 400
        dados['email']=dados['email'].lower()
        banco.registrar_parceiro(DB_PATH,dados)
        flash('Obrigado pelo interesse. Nossa equipe poderá entrar em contato.', 'sucesso')
        return redirect(url_for('parcerias'))
    return render_template('parcerias.html', dados=dados)


@app.errorhandler(404)
def pagina_nao_encontrada(_):
    return render_template('erro.html', codigo=404, mensagem='Não encontramos essa página.'), 404


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(413)
def erro_formulario(erro):
    return render_template('erro.html', codigo=erro.code, mensagem='Não foi possível enviar. Atualize a página e confira os campos e o acesso.'), erro.code

from gestao import registrar_rotas
registrar_rotas(app, lambda: DB_PATH, login_required)
from central import registrar_central
registrar_central(app, lambda: DB_PATH, login_required)

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
