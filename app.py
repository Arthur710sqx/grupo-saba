import os
import secrets
import hmac
from datetime import date
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from banco import conectar, inicializar_banco
from validacoes import validar_consentimento, validar_email, validar_telefone

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=65536)
DB_PATH = Path(__file__).resolve().parent / 'grupo_saba.sqlite3'
inicializar_banco(DB_PATH)

@app.before_request
def proteger_formularios():
    session.setdefault('csrf', secrets.token_hex(32))
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
    with conectar(DB_PATH) as db:
        return {r['chave']: r['valor'] for r in db.execute('SELECT chave,valor FROM site_conteudo')}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('admin_login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route('/')
def inicio():
    with conectar(DB_PATH) as db:
        projetos = db.execute('SELECT * FROM projetos ORDER BY id LIMIT 3').fetchall()
        noticias = db.execute('SELECT * FROM noticias ORDER BY data DESC LIMIT 3').fetchall()
    return render_template('inicio.html', site=site_content(), projetos=projetos, noticias=noticias)


@app.route('/quem-somos')
def quem_somos():
    return render_template('quem-somos.html', site=site_content())


@app.route('/projetos')
def projetos():
    with conectar(DB_PATH) as db:
        projetos = db.execute('SELECT * FROM projetos ORDER BY id').fetchall()
    return render_template('projetos.html', projetos=projetos)


@app.route('/transparencia')
def transparencia():
    return render_template('transparencia.html')


@app.route('/como-ajudar')
def como_ajudar():
    return render_template('como-ajudar.html')


@app.route('/voluntariado', methods=['GET', 'POST'])
def voluntariado():
    dados = {k: request.form.get(k, '').strip() for k in ('nome', 'email', 'telefone', 'cidade')}
    if request.method == 'POST':
        if not dados['nome'] or not validar_email(dados['email']) or not validar_telefone(dados['telefone']) or not dados['cidade'] or not validar_consentimento(request.form.get('consentimento')):
            flash('Confira os campos, informe um telefone válido e aceite o aviso de privacidade.', 'erro')
            return render_template('voluntariado.html', dados=dados), 400
        try:
            with conectar(DB_PATH) as db:
                db.execute('INSERT INTO voluntarios(nome,email,telefone,cidade,consentimento) VALUES(?,?,?,?,1)', tuple(dados.values()))
        except Exception:
            flash('Este e-mail já está cadastrado ou não foi possível receber seu interesse.', 'erro')
            return render_template('voluntariado.html', dados=dados), 400
        flash('Recebemos seu interesse. A equipe do Grupo Sabá poderá entrar em contato.', 'sucesso')
        return redirect(url_for('voluntariado'))
    return render_template('voluntariado.html', dados=dados)


@app.route('/privacidade')
def privacidade():
    return render_template('privacidade.html')


@app.route('/admin/primeiro-acesso', methods=['GET', 'POST'])
def admin_setup():
    if request.remote_addr not in ('127.0.0.1', '::1'):
        abort(403)
    with conectar(DB_PATH) as db:
        existe = db.execute('SELECT 1 FROM usuarios_admin LIMIT 1').fetchone()
    if existe:
        abort(404)
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        if not validar_email(email) or len(senha) < 12:
            flash('Informe um e-mail válido e uma senha com pelo menos 12 caracteres.', 'erro')
            return render_template('admin_setup.html'), 400
        with conectar(DB_PATH) as db:
            db.execute('INSERT INTO usuarios_admin(email,senha_hash,perfil) VALUES(?,?,?)', (email, generate_password_hash(senha), 'admin'))
        flash('Acesso administrativo criado. Entre para continuar.', 'sucesso')
        return redirect(url_for('admin_login'))
    return render_template('admin_setup.html')


@app.route('/admin/entrar', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        with conectar(DB_PATH) as db:
            user = db.execute('SELECT * FROM usuarios_admin WHERE email=?', (email,)).fetchone()
        if user and check_password_hash(user['senha_hash'], request.form.get('senha', '')):
            session.clear()
            session['admin_id'] = user['id']
            session['admin_email'] = user['email']
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
    with conectar(DB_PATH) as db:
        totais = {t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('voluntarios', 'beneficiarios', 'parceiros_doadores', 'projetos')}
        beneficiarios = db.execute('SELECT id,nome,localizacao,status,prioridade,criado_em FROM beneficiarios ORDER BY CASE prioridade WHEN "alta" THEN 0 WHEN "media" THEN 1 ELSE 2 END, criado_em').fetchall()
        voluntarios = db.execute('SELECT id,nome,email,cidade,status FROM voluntarios ORDER BY id DESC LIMIT 30').fetchall()
        parceiros = db.execute('SELECT id,tipo_pessoa,nome,email,tipo_apoio,status FROM parceiros_doadores ORDER BY id DESC LIMIT 30').fetchall()
    return render_template('admin.html', totais=totais, beneficiarios=beneficiarios, voluntarios=voluntarios, parceiros=parceiros)


@app.route('/apoio', methods=['GET', 'POST'])
def solicitar_apoio():
    dados = {k: request.form.get(k, '').strip() for k in ('nome', 'contato', 'localizacao', 'situacao', 'necessidades')}
    if request.method == 'POST':
        if not all(dados.values()) or not validar_consentimento(request.form.get('consentimento')):
            flash('Preencha os campos obrigatórios e confirme o aviso de privacidade.', 'erro')
            return render_template('apoio.html', dados=dados), 400
        with conectar(DB_PATH) as db:
            db.execute('INSERT INTO beneficiarios(nome,contato,localizacao,situacao,necessidades,consentimento) VALUES(?,?,?,?,?,1)', tuple(dados.values()))
        flash('Sua solicitação foi recebida. A equipe avaliará as informações e, se necessário, combinará uma visita.', 'sucesso')
        return redirect(url_for('solicitar_apoio'))
    return render_template('apoio.html', dados=dados)


@app.route('/parcerias', methods=['GET', 'POST'])
def parcerias():
    dados = {k: request.form.get(k, '').strip() for k in ('tipo_pessoa', 'nome', 'email', 'telefone', 'tipo_apoio')}
    if request.method == 'POST':
        if dados['tipo_pessoa'] not in ('fisica', 'juridica') or not dados['nome'] or not validar_email(dados['email']) or not validar_telefone(dados['telefone']) or not dados['tipo_apoio'] or not validar_consentimento(request.form.get('consentimento')):
            flash('Revise os campos, telefone, categoria e autorização de contato.', 'erro')
            return render_template('parcerias.html', dados=dados), 400
        with conectar(DB_PATH) as db:
            db.execute('INSERT INTO parceiros_doadores(tipo_pessoa,nome,email,telefone,consentimento,tipo_apoio) VALUES(?,?,?,?,1,?)', tuple(dados[k] for k in ('tipo_pessoa', 'nome', 'email', 'telefone', 'tipo_apoio')))
        flash('Obrigado pelo interesse. Nossa equipe poderá entrar em contato.', 'sucesso')
        return redirect(url_for('parcerias'))
    return render_template('parcerias.html', dados=dados)


@app.post('/admin/beneficiario/<int:beneficiario_id>/visita')
@login_required
def registrar_visita(beneficiario_id):
    data_visita = request.form.get('data', '').strip()
    responsavel = request.form.get('responsavel', '').strip()
    observacoes = request.form.get('observacoes', '').strip()
    urgencia = request.form.get('urgencia', '').strip()
    if not data_visita or not responsavel or urgencia not in ('baixa', 'media', 'alta'):
        flash('Informe data, responsável e grau de urgência para registrar a visita.', 'erro')
        return redirect(url_for('admin_dashboard'))
    try:
        date.fromisoformat(data_visita)
    except ValueError:
        flash('Data da visita inválida.', 'erro')
        return redirect(url_for('admin_dashboard'))
    status = 'priorizado' if urgencia == 'alta' else 'em avaliacao'
    with conectar(DB_PATH) as db:
        if not db.execute('SELECT id FROM beneficiarios WHERE id=?', (beneficiario_id,)).fetchone():
            abort(404)
        db.execute('INSERT INTO visitas_beneficiarios(beneficiario_id,data,responsavel,observacoes,grau_urgencia) VALUES(?,?,?,?,?)', (beneficiario_id, data_visita, responsavel, observacoes, urgencia))
        db.execute('UPDATE beneficiarios SET prioridade=?,status=? WHERE id=?', (urgencia, status, beneficiario_id))
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)', (session['admin_id'], 'visita registrada', f'beneficiario:{beneficiario_id}'))
    flash('Visita registrada. A prioridade foi definida pela avaliação humana informada.', 'sucesso')
    return redirect(url_for('admin_dashboard'))


@app.errorhandler(404)
def pagina_nao_encontrada(_):
    return render_template('erro.html', codigo=404, mensagem='Não encontramos essa página.'), 404


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
