"""Central administrativa: campos permitidos e formulários de conteúdo."""
from datetime import date
import sqlite3
from flask import abort, flash, redirect, render_template, request, session, url_for
import banco
from conteudo_padrao import PADRAO
from validacoes import validar_url_https, validar_voluntario, validar_parceiro, validar_beneficiario

TEXTOS = {
    'hero_titulo': 'Título do banner', 'hero_texto': 'Texto do banner',
    'banner_imagem': 'Imagem do banner (URL HTTPS)', 'banner_alt': 'Descrição acessível do banner',
    'banner_nome': 'Nome na legenda do banner', 'banner_cargo': 'Complemento da legenda',
    'intro_titulo': 'Título da apresentação', 'intro_texto': 'Texto da apresentação',
    'missao': 'Missão', 'visao': 'Visão', 'endereco': 'Endereço', 'cnpj': 'CNPJ',
}
COLECOES = {
    'projetos': [('titulo','Título'),('objetivo','Descrição'),('tema','Tema'),('situacao','Situação'),('imagem','Imagem HTTPS (opcional)')],
    'noticias': [('titulo','Título'),('resumo','Resumo'),('data','Data (AAAA-MM-DD)'),('imagem','Imagem HTTPS (opcional)')],
    'midias': [('titulo','Descrição acessível'),('url','Imagem HTTPS'),('fonte','Fonte HTTPS'),('projeto_id','Projeto relacionado')],
}

def registrar_central(app, caminho, protegido):
    @app.route('/admin/solicitacao/<int:identificador>/editar',methods=['GET','POST'])
    @protegido
    def editar_solicitacao(identificador):
        atual=banco.obter_beneficiario(caminho(),identificador)
        if not atual: abort(404)
        dados=dict(atual)
        if request.method=='POST':
            dados={k:request.form.get(k,'').strip() for k in ('nome','contato','localizacao','situacao','necessidades')}
            dados['consentimento']=atual['consentimento']
            erros=validar_beneficiario(dados)
            if erros:
                flash(' '.join(erros.values()),'erro')
                return render_template('solicitacao_editar.html',dados=dados),400
            banco.editar_solicitacao(caminho(),identificador,dados,session['admin_id'])
            flash('Solicitação atualizada. Histórico preservado.','sucesso')
            return redirect(url_for('ficha',identificador=identificador))
        return render_template('solicitacao_editar.html',dados=dados)

    @app.get('/admin/central')
    @protegido
    def central():
        colecao=request.args.get('colecao','projetos')
        if colecao not in COLECOES: abort(404)
        q=request.args.get('q','').strip()[:120]
        pagina=max(1,request.args.get('pagina',1,type=int))
        registros,total,pagina=banco.conteudo_paginado(caminho(),colecao,q,pagina)
        return render_template('central.html',colecao=colecao,registros=registros,total=total,
                               pagina=pagina,paginas=max(1,(total+19)//20),q=q)

    @app.route('/admin/aparencia',methods=['GET','POST'])
    @protegido
    def aparencia():
        dados={**PADRAO, **banco.obter_conteudo(caminho())}
        if request.method=='POST':
            dados.update({k:request.form.get(k,'').strip() for k in TEXTOS})
            if any(len(dados[k])>1200 for k in TEXTOS) or (dados['banner_imagem'] and not validar_url_https(dados['banner_imagem'])):
                flash('Use até 1200 caracteres por campo e endereço HTTPS válido para a imagem.','erro')
                return render_template('aparencia.html',dados=dados,campos=TEXTOS),400
            if dados['banner_imagem'] and not dados['banner_alt']:
                flash('Descreva a imagem para quem usa leitor de tela.','erro')
                return render_template('aparencia.html',dados=dados,campos=TEXTOS),400
            banco.salvar_textos(caminho(),{k:dados[k] for k in TEXTOS},session['admin_id'])
            flash('Textos e banner atualizados.','sucesso')
            return redirect(url_for('aparencia'))
        return render_template('aparencia.html',dados=dados,campos=TEXTOS)

    @app.route('/admin/central/<colecao>/<int:identificador>',methods=['GET','POST'])
    @protegido
    def editar_conteudo(colecao,identificador):
        if colecao not in COLECOES: abort(404)
        atual=banco.conteudo_individual(caminho(),colecao,identificador) if identificador else {}
        if identificador and not atual: abort(404)
        campos=COLECOES[colecao]
        dados=dict(atual)
        if request.method=='POST':
            dados={k:request.form.get(k,'').strip() for k,_ in campos}
            erros=[]
            if not 2<=len(dados['titulo'])<=120: erros.append('Título: informe de 2 a 120 caracteres.')
            if any(len(v)>1200 for v in dados.values()): erros.append('Limite de 1200 caracteres por campo.')
            for k in ('imagem','url','fonte'):
                if k in dados and (dados[k] or k!='imagem') and not validar_url_https(dados[k]): erros.append('Imagens e fontes devem usar HTTPS.')
            if colecao=='noticias':
                try: date.fromisoformat(dados['data'])
                except ValueError: erros.append('Informe uma data válida.')
            if colecao=='projetos' and len(dados['objetivo'])<2: erros.append('Informe a descrição.')
            if colecao=='midias':
                pid=dados['projeto_id']
                if pid and (not pid.isdigit() or not banco.obter_projeto(caminho(),int(pid))): erros.append('Selecione um projeto existente.')
                dados['projeto_id']=int(pid) if pid.isdigit() else None
            if erros:
                flash(' '.join(erros),'erro')
            else:
                banco.gravar_conteudo(caminho(),colecao,identificador,dados,session['admin_id'])
                flash('Conteúdo salvo.','sucesso')
                return redirect(url_for('central',colecao=colecao))
        else: erros=[]
        return render_template('conteudo_editar.html',dados=dados,campos=campos,colecao=colecao,
                               identificador=identificador,projetos=banco.listar_projetos(caminho())),400 if erros else 200

    @app.route('/admin/central/<colecao>/<int:identificador>/excluir',methods=['GET','POST'])
    @protegido
    def remover_conteudo(colecao,identificador):
        if colecao not in COLECOES: abort(404)
        registro=banco.conteudo_individual(caminho(),colecao,identificador)
        if not registro: abort(404)
        if request.method=='POST':
            if request.form.get('confirmacao')!='sim': abort(400)
            banco.remover_conteudo(caminho(),colecao,identificador,session['admin_id'])
            flash('Conteúdo excluído.','sucesso')
            return redirect(url_for('central',colecao=colecao))
        return render_template('confirmar_exclusao.html',registro=registro,colecao=colecao)

    @app.route('/admin/novo/<categoria>',methods=['GET','POST'])
    @protegido
    def novo_cadastro(categoria):
        config={'voluntario':('voluntariado.html',validar_voluntario,banco.registrar_voluntario),
                'parceiro':('parcerias.html',validar_parceiro,banco.registrar_parceiro),
                'beneficiario':('apoio.html',validar_beneficiario,banco.registrar_beneficiario)}
        if categoria not in config: abort(404)
        template,validar,gravar=config[categoria]
        dados=request.form.to_dict()
        if request.method=='POST':
            dados={k:v.strip() for k,v in dados.items()}
            dados.setdefault('disponibilidade',''); dados.setdefault('interesses','')
            if 'email' in dados: dados['email']=dados['email'].lower()
            erros=validar(dados)
            if not erros:
                try:
                    gravar(caminho(),dados)
                    flash('Cadastro registrado.','sucesso')
                    return redirect(url_for('admin_dashboard',categoria={'voluntario':'voluntarios','parceiro':'parceiros','beneficiario':'beneficiarios'}[categoria]))
                except sqlite3.IntegrityError: erros={'email':'E-mail já cadastrado.'}
            flash(' '.join(erros.values()),'erro')
            return render_template(template,dados=dados),400
        return render_template(template,dados=dados)
