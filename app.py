import os
import sqlite3
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
import banco
from validacoes import CATEGORIAS, chave_documento, validar_formulario

app = Flask(__name__)
app.secret_key = os.urandom(32)


def exigir_login():
    if not session.get("usuario"):
        flash("Entre para alterar cadastros.", "erro")
        return redirect(url_for("login"))


def exigir_admin():
    falta_login = exigir_login()
    if falta_login:
        return falta_login
    if session.get("papel") != "admin":
        abort(403)


@app.route("/")
def listar():
    conn = banco.conectar_banco()
    try:
        return render_template("lista.html", pessoas=banco.listar_pessoas(conn))
    finally:
        conn.close()


@app.route("/busca")
def busca():
    termo = request.args.get("termo", "").strip()
    grupo = request.args.get("grupo", "").strip()
    conn = banco.conectar_banco()
    try:
        return render_template("busca.html", pessoas=banco.listar_pessoas(conn, termo, grupo),
                               termo=termo, grupo=grupo, categorias=CATEGORIAS)
    finally:
        conn.close()


@app.route("/pessoa/<int:id_pessoa>")
def detalhe(id_pessoa):
    conn = banco.conectar_banco()
    try:
        pessoa = banco.obter(conn, id_pessoa)
        if pessoa is None:
            abort(404)
        return render_template("detalhe.html", pessoa=pessoa, registros=banco.participacoes(conn, id_pessoa))
    finally:
        conn.close()


@app.route("/novo", methods=["GET", "POST"])
@app.route("/pessoa/<int:id_pessoa>/editar", methods=["GET", "POST"])
def formulario(id_pessoa=None):
    bloqueio = exigir_login()
    if bloqueio:
        return bloqueio
    conn = banco.conectar_banco()
    try:
        pessoa = banco.obter(conn, id_pessoa) if id_pessoa is not None else None
        if id_pessoa is not None and pessoa is None:
            abort(404)
        dados = dict(pessoa) if pessoa else {}
        erros = {}
        if request.method == "POST":
            dados = {campo: request.form.get(campo, "").strip() for campo in banco.CAMPOS}
            if pessoa:
                dados["grupo"] = pessoa["grupo"]
            erros = validar_formulario(dados, conn, id_pessoa)
            if not erros:
                try:
                    if dados["grupo"] == "Beneficiário":
                        dados.update(especialidade="", area="", disponibilidade="")
                    else:
                        dados["necessidade"] = ""
                        if dados["categoria"] != "Voluntário profissional":
                            dados["especialidade"] = ""
                    salvo = banco.salvar(conn, dados, chave_documento(dados["documento"]), id_pessoa)
                    if salvo is None:
                        abort(404)
                    conn.commit()
                except sqlite3.IntegrityError:
                    erros["documento"] = "Documento já cadastrado neste grupo."
                else:
                    flash("Cadastro salvo.", "sucesso")
                    return redirect(url_for("listar"))
        return render_template("form.html", dados=dados, erros=erros, categorias=CATEGORIAS,
                               id_pessoa=id_pessoa), 400 if erros else 200
    finally:
        conn.close()


@app.route("/pessoa/<int:id_pessoa>/excluir", methods=["POST"])
def excluir(id_pessoa):
    bloqueio = exigir_admin()
    if bloqueio:
        return bloqueio
    conn = banco.conectar_banco()
    try:
        if not banco.excluir(conn, id_pessoa):
            abort(404)
        conn.commit()
        flash("Cadastro excluído.", "sucesso")
        return redirect(url_for("listar"))
    finally:
        conn.close()


@app.route("/relatorio")
def relatorio():
    conn = banco.conectar_banco()
    try:
        return render_template("relatorio.html", linhas=banco.resumo(conn))
    finally:
        conn.close()


@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = banco.conectar_banco()
        try:
            usuario = banco.buscar_login(conn, request.form.get("usuario", "").strip())
            if usuario is not None and check_password_hash(usuario["senha_hash"], request.form.get("senha", "")):
                session.clear()
                session.update(usuario=usuario["usuario"], papel=usuario["papel"])
                flash("Entrada realizada.", "sucesso")
                return redirect(url_for("listar"))
        finally:
            conn.close()
        flash("Usuario ou senha invalidos.", "erro")
        return render_template("login.html"), 401
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("listar"))


@app.errorhandler(403)
@app.errorhandler(404)
def erro(e):
    return render_template("erro.html", codigo=e.code), e.code


if __name__ == "__main__":
    app.run()
