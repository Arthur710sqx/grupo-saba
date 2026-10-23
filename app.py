import os
from flask import Flask, render_template
from banco import inicializar_banco
from pathlib import Path
app=Flask(__name__)
app.config['SECRET_KEY']=os.environ.get('FLASK_SECRET_KEY', 'chave-local-apenas-para-desenvolvimento')
inicializar_banco(Path(__file__).resolve().parent/'grupo_saba.sqlite3')
@app.route('/')
def inicio(): return render_template('inicio.html')
@app.route('/quem-somos')
def quem_somos(): return render_template('quem-somos.html')
@app.route('/projetos')
def projetos(): return render_template('projetos.html')
@app.route('/transparencia')
def transparencia(): return render_template('transparencia.html')
@app.route('/como-ajudar')
def como_ajudar(): return render_template('como-ajudar.html')
@app.route('/voluntariado')
def voluntariado(): return render_template('voluntariado.html')
@app.route('/privacidade')
def privacidade(): return render_template('privacidade.html')
if __name__=='__main__': app.run()
