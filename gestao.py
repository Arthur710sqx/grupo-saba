"""Operações da equipe: sempre autenticadas e com consultas parametrizadas."""
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from flask import abort, flash, redirect, render_template, request, session
from banco import conectar


def registrar_rotas(app, caminho, protegido):
    def auditar(db, acao, entidade):
        db.execute('INSERT INTO logs_auditoria(usuario_id,acao,entidade) VALUES(?,?,?)',
                   (session['admin_id'], acao, entidade))

    @app.get('/galeria')
    def galeria():
        with conectar(caminho()) as db:
            fotos = db.execute('SELECT * FROM midias ORDER BY id DESC').fetchall()
        return render_template('galeria.html', fotos=fotos)

    @app.get('/projetos/<int:identificador>')
    def projeto_detalhe(identificador):
        with conectar(caminho()) as db:
            projeto = db.execute('SELECT * FROM projetos WHERE id=? AND id>=1001', (identificador,)).fetchone()
            if not projeto:
                abort(404)
            fotos = db.execute('SELECT * FROM midias WHERE projeto_id=?', (identificador,)).fetchall()
        return render_template('projeto.html', projeto=projeto, fotos=fotos)

    @app.get('/admin/beneficiario/<int:identificador>')
    @protegido
    def ficha(identificador):
        with conectar(caminho()) as db:
            pessoa = db.execute('SELECT * FROM beneficiarios WHERE id=?', (identificador,)).fetchone()
            if not pessoa:
                abort(404)
            historicos = {t: db.execute(f'SELECT * FROM {t} WHERE beneficiario_id=? ORDER BY id DESC', (identificador,)).fetchall()
                          for t in ('agendamentos', 'visitas_beneficiarios', 'atendimentos')}
        return render_template('ficha.html', pessoa=pessoa, historicos=historicos)

    @app.post('/admin/beneficiario/<int:identificador>/acompanhar')
    @protegido
    def acompanhar(identificador):
        acao = request.form.get('acao')
        with conectar(caminho()) as db:
            pessoa = db.execute('SELECT * FROM beneficiarios WHERE id=?', (identificador,)).fetchone()
            if not pessoa:
                abort(404)
            if acao == 'agendar':
                try:
                    dia = date.fromisoformat(request.form.get('data',''))
                    if dia < date.today() or not request.form.get('responsavel','').strip():
                        raise ValueError()
                except ValueError:
                    abort(400)
                db.execute("UPDATE agendamentos SET status='reagendada' WHERE beneficiario_id=? AND status='agendada'", (identificador,))
                db.execute('INSERT INTO agendamentos(beneficiario_id,data,responsavel) VALUES(?,?,?)', (identificador,dia.isoformat(),request.form['responsavel'].strip()))
                db.execute("UPDATE beneficiarios SET status='visita agendada' WHERE id=?", (identificador,))
            elif acao == 'atendimento':
                status = request.form.get('status')
                descricao = request.form.get('descricao','').strip()
                if status not in ('em acompanhamento', 'atendido', 'encerrado') or len(descricao) < 10:
                    abort(400)
                if pessoa['prioridade'] == 'pendente':
                    flash('Registre a avaliação da visita antes do atendimento.', 'erro')
                    return redirect(f'/admin/beneficiario/{identificador}')
                db.execute('INSERT INTO atendimentos(beneficiario_id,status,descricao) VALUES(?,?,?)', (identificador,status,descricao))
                db.execute('UPDATE beneficiarios SET status=? WHERE id=?', (status,identificador))
            else:
                abort(400)
            auditar(db, acao, f'beneficiario:{identificador}')
        flash('Acompanhamento salvo.', 'sucesso')
        return redirect(f'/admin/beneficiario/{identificador}')

    @app.post('/admin/cadastro/<categoria>/<int:identificador>')
    @protegido
    def cadastro_status(categoria, identificador):
        tabelas = {'voluntario': ('voluntarios', ('novo','contatado','ativo','inativo')),
                   'parceiro': ('parceiros_doadores', ('interessado','contatado','ativo','inativo'))}
        if categoria not in tabelas:
            abort(404)
        tabela, permitidos = tabelas[categoria]
        status = request.form.get('status')
        if status not in permitidos:
            abort(400)
        with conectar(caminho()) as db:
            if not db.execute(f'UPDATE {tabela} SET status=? WHERE id=?', (status,identificador)).rowcount:
                abort(404)
            auditar(db, f'status:{status}', f'{categoria}:{identificador}')
        flash('Cadastro atualizado.', 'sucesso')
        return redirect('/admin')

    @app.route('/admin/doacoes', methods=['GET','POST'])
    @protegido
    def doacoes():
        with conectar(caminho()) as db:
            if request.method == 'POST':
                tipo = request.form.get('tipo')
                descricao = request.form.get('descricao','').strip()
                valor = None
                if tipo not in ('financeira','materiais','servicos') or len(descricao) < 3:
                    abort(400)
                if tipo == 'financeira':
                    try:
                        quantia = Decimal(request.form.get('valor','').replace(',','.'))
                        if not quantia.is_finite() or quantia <= 0 or quantia > 100000000 or quantia.as_tuple().exponent < -2:
                            raise InvalidOperation()
                        valor = float(quantia)
                    except InvalidOperation:
                        abort(400)
                parceiro = request.form.get('parceiro_id')
                if not db.execute('SELECT id FROM parceiros_doadores WHERE id=?',(parceiro,)).fetchone():
                    abort(400)
                db.execute('INSERT INTO doacoes_parcerias(parceiro_id,tipo,valor,descricao,criado_em) VALUES(?,?,?,?,CURRENT_TIMESTAMP)', (parceiro,tipo,valor,descricao))
                auditar(db,'doação registrada',f'parceiro:{parceiro}')
                flash('Doação registrada no banco. Este registro não realiza cobrança.', 'sucesso')
                return redirect('/admin/doacoes')
            parceiros = db.execute('SELECT id,nome FROM parceiros_doadores ORDER BY nome').fetchall()
            registros = db.execute('SELECT d.*,p.nome FROM doacoes_parcerias d JOIN parceiros_doadores p ON p.id=d.parceiro_id ORDER BY d.id DESC').fetchall()
        return render_template('doacoes.html', parceiros=parceiros, registros=registros)

    @app.route('/admin/conteudo', methods=['GET','POST'])
    @protegido
    def conteudo():
        with conectar(caminho()) as db:
            if request.method == 'POST':
                tipo = request.form.get('tipo')
                titulo = request.form.get('titulo','').strip()
                if not titulo:
                    abort(400)
                if tipo == 'projeto':
                    objetivo = request.form.get('objetivo','').strip()
                    if not objetivo:
                        abort(400)
                    identificador = request.form.get('id')
                    valores = (titulo,objetivo,request.form.get('tema',''),request.form.get('situacao',''))
                    if identificador:
                        if not db.execute('UPDATE projetos SET titulo=?,objetivo=?,tema=?,situacao=? WHERE id=? AND id>=1001', (*valores,identificador)).rowcount:
                            abort(404)
                    else:
                        db.execute('INSERT INTO projetos(titulo,objetivo,tema,situacao) VALUES(?,?,?,?)', valores)
                elif tipo == 'foto':
                    url, fonte = request.form.get('url',''),request.form.get('fonte','')
                    if any(urlparse(u).scheme != 'https' or not urlparse(u).hostname for u in (url,fonte)) or request.form.get('autorizacao') != 'on':
                        abort(400)
                    projeto = request.form.get('projeto_id') or None
                    if projeto and not db.execute('SELECT id FROM projetos WHERE id=? AND id>=1001',(projeto,)).fetchone():
                        abort(400)
                    db.execute('INSERT INTO midias(projeto_id,titulo,url,fonte) VALUES(?,?,?,?)', (projeto,titulo,url,fonte))
                else:
                    abort(400)
                auditar(db,'conteúdo atualizado',tipo)
                flash('Conteúdo publicado no site local.', 'sucesso')
                return redirect('/admin/conteudo')
            projetos = db.execute('SELECT * FROM projetos WHERE id>=1001 ORDER BY id').fetchall()
        return render_template('conteudo.html', projetos=projetos)
