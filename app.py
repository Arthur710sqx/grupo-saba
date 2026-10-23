import os
from flask import Flask, render_template, request, redirect, url_for, flash
from banco import inicializar_banco, conectar
from validacoes import validar_email
from pathlib import Path
app=Flask(__name__)
app.config['SECRET_KEY']=os.environ.get('FLASK_SECRET_KEY', 'chave-local-apenas-para-desenvolvimento')
DB_PATH=Path(__file__).resolve().parent/'grupo_saba.sqlite3'
inicializar_banco(DB_PATH)
def conteudo():
    with conectar(DB_PATH) as db:
        return {r['chave']: r['valor'] for r in db.execute('SELECT chave,valor FROM site_conteudo')}
@app.route('/')
def inicio():
    with conectar(DB_PATH) as db:
        projetos=db.execute('SELECT * FROM projetos ORDER BY id LIMIT 3').fetchall()
        noticias=db.execute('SELECT * FROM noticias ORDER BY data DESC LIMIT 3').fetchall()
    return render_template('inicio.html', site=conteudo(), projetos=projetos, noticias=noticias)
@app.route('/quem-somos')
def quem_somos(): return render_template('quem-somos.html', site=conteudo())
@app.route('/projetos')
def projetos():
    with conectar(DB_PATH) as db: projetos=db.execute('SELECT * FROM projetos ORDER BY id').fetchall()
    return render_template('projetos.html', projetos=projetos)
@app.route('/transparencia')
def transparencia(): return render_template('transparencia.html')
@app.route('/como-ajudar')
def como_ajudar(): return render_template('como-ajudar.html')
@app.route('/voluntariado', methods=['GET','POST'])
def voluntariado():
    if request.method == 'POST':
        dados={k:request.form.get(k,'').strip() for k in ('nome','email','telefone','cidade')}
        if not dados['nome'] or not validar_email(dados['email']) or not dados['telefone'] or not dados['cidade'] or not request.form.get('consentimento'):
            flash('Preencha os campos obrigatórios e aceite o aviso de privacidade.','erro')
            return render_template('voluntariado.html', dados=dados),400
        try:
            with conectar(DB_PATH) as db: db.execute('INSERT INTO voluntarios(nome,email,telefone,cidade,consentimento) VALUES(?,?,?,?,1)', tuple(dados.values()))
        except Exception:
            flash('Este e-mail já foi cadastrado ou não pôde ser recebido.','erro')
            return render_template('voluntariado.html', dados=dados),400
        flash('Recebemos seu interesse. A equipe do Grupo Sabá entrará em contato.','sucesso')
        return redirect(url_for('voluntariado'))
    return render_template('voluntariado.html', dados={})
@app.route('/privacidade')
def privacidade(): return render_template('privacidade.html')
if __name__=='__main__': app.run()
