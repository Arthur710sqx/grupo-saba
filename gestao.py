"""Rotas de apresentação e gestão; consultas e persistência ficam em banco.py."""
from datetime import date
from decimal import Decimal, InvalidOperation
from flask import abort, flash, redirect, render_template, request, session, url_for
import banco
from validacoes import validar_parceiro, validar_projeto, validar_texto, validar_url_https, validar_visita, validar_voluntario

def registrar_rotas(app, caminho, protegido):
    @app.get('/galeria')
    def galeria():
        return render_template('galeria.html', fotos=banco.listar_midias(caminho()))

    @app.get('/projetos/<int:identificador>')
    def projeto_detalhe(identificador):
        projeto=banco.obter_projeto(caminho(),identificador)
        if not projeto: abort(404)
        return render_template('projeto.html',projeto=projeto,fotos=banco.listar_midias_projeto(caminho(),identificador))

    @app.get('/admin/beneficiario/<int:identificador>')
    @protegido
    def ficha(identificador):
        pessoa=banco.obter_beneficiario(caminho(),identificador)
        if not pessoa: abort(404)
        return render_template('ficha.html',pessoa=pessoa,historicos=banco.historico_beneficiario(caminho(),identificador),dados=request.args)

    @app.post('/admin/beneficiario/<int:identificador>/acompanhar')
    @protegido
    def acompanhar(identificador):
        pessoa=banco.obter_beneficiario(caminho(),identificador)
        if not pessoa: abort(404)
        dados=request.form.to_dict()
        acao=dados.get('acao')
        if acao=='agendar':
            try:
                dia=date.fromisoformat(dados.get('data',''))
                if dia < date.today() or not validar_texto(dados.get('responsavel'),2,120): raise ValueError()
            except ValueError:
                flash('Informe data válida e responsável. Os campos foram preservados.','erro')
                return render_template('ficha.html',pessoa=pessoa,historicos=banco.historico_beneficiario(caminho(),identificador),dados=dados),400
            banco.agendar_visita(caminho(),identificador,dia.isoformat(),dados['responsavel'].strip(),session['admin_id'])
        elif acao=='atendimento':
            status=dados.get('status'); descricao=dados.get('descricao','').strip()
            if status not in ('em acompanhamento','atendido','encerrado') or not validar_texto(descricao,10,1000):
                flash('Revise o status e registre de 10 a 1000 caracteres. Os campos foram preservados.','erro')
                return render_template('ficha.html',pessoa=pessoa,historicos=banco.historico_beneficiario(caminho(),identificador),dados=dados),400
            if pessoa['prioridade']=='pendente':
                flash('Registre a avaliação da visita antes do atendimento.','erro')
                return redirect(url_for('ficha',identificador=identificador))
            banco.registrar_atendimento(caminho(),identificador,status,descricao,session['admin_id'])
        else: abort(400)
        flash('Acompanhamento salvo.','sucesso')
        return redirect(url_for('ficha',identificador=identificador))

    @app.post('/admin/beneficiario/<int:identificador>/visita')
    @protegido
    def visita(identificador):
        pessoa=banco.obter_beneficiario(caminho(),identificador)
        if not pessoa: abort(404)
        dados=request.form.to_dict(); erros=validar_visita(dados)
        if erros:
            flash('Confira os campos: '+' '.join(erros.values()),'erro')
            return render_template('ficha.html',pessoa=pessoa,historicos=banco.historico_beneficiario(caminho(),identificador),dados=dados),400
        banco.registrar_visita(caminho(),identificador,dados['data'],dados['responsavel'].strip(),dados['observacoes'].strip(),dados['urgencia'],session['admin_id'])
        flash('Visita registrada e avaliação humana preservada.','sucesso')
        return redirect(url_for('ficha',identificador=identificador))

    @app.route('/admin/cadastro/<categoria>/<int:identificador>',methods=['GET','POST'])
    @protegido
    def cadastro(categoria,identificador):
        if categoria not in ('voluntario','parceiro'): abort(404)
        atual=(banco.obter_voluntario(caminho(),identificador) if categoria=='voluntario' else banco.obter_parceiro(caminho(),identificador))
        if not atual: abort(404)
        dados=request.form.to_dict() if request.method=='POST' else dict(atual)
        if request.method=='POST':
            if 'status' in dados:
                permitidos={'voluntario':('novo','contatado','ativo','inativo'),'parceiro':('interessado','contatado','ativo','inativo')}[categoria]
                if dados['status'] not in permitidos: abort(400)
                tabela='voluntarios' if categoria=='voluntario' else 'parceiros_doadores'
                if not banco.atualizar_status_cadastro(caminho(),tabela,dados['status'],identificador): abort(404)
                banco.registrar_log(caminho(),session['admin_id'],f'status:{dados["status"]}',f'{categoria}:{identificador}')
                flash('Situação atualizada.','sucesso')
                return redirect(url_for('admin_dashboard'))
            dados['consentimento'] = atual['consentimento']
            dados.setdefault('disponibilidade', '')
            dados.setdefault('interesses', '')
            erros=(validar_voluntario(dados) if categoria=='voluntario' else validar_parceiro(dados))
            if erros:
                flash('Confira os campos: '+' '.join(erros.values()),'erro')
                return render_template('cadastro_editar.html',categoria=categoria,dados=dados,identificador=identificador),400
            if categoria=='voluntario':
                dados['email']=dados['email'].strip().lower()
                resultado=banco.atualizar_voluntario(caminho(),identificador,dados)
                if resultado==-1:
                    flash('Este e-mail já pertence a outro cadastro.','erro')
                    return render_template('cadastro_editar.html',categoria=categoria,dados=dados,identificador=identificador),400
            else:
                dados['email']=dados['email'].strip().lower()
                banco.atualizar_parceiro(caminho(),identificador,dados)
            banco.registrar_log(caminho(),session['admin_id'],'editar cadastro',f'{categoria}:{identificador}')
            flash('Cadastro atualizado.','sucesso')
            return redirect(url_for('admin_dashboard'))
        return render_template('cadastro_editar.html',categoria=categoria,dados=dados,identificador=identificador)

    @app.post('/admin/cadastro/<categoria>/<int:identificador>/excluir')
    @protegido
    def excluir_cadastro(categoria,identificador):
        if categoria=='voluntario': apagados=banco.excluir_voluntario(caminho(),identificador)
        elif categoria=='parceiro': apagados=banco.excluir_parceiro(caminho(),identificador)
        else: abort(404)
        if not apagados:
            flash('Não foi possível excluir: o parceiro pode ter doações vinculadas.','erro')
        else:
            banco.registrar_log(caminho(),session['admin_id'],'excluir cadastro',f'{categoria}:{identificador}')
            flash('Cadastro excluído.','sucesso')
        return redirect(url_for('admin_dashboard'))

    @app.post('/admin/projetos/<int:identificador>/excluir')
    @protegido
    def excluir_projeto(identificador):
        if not banco.excluir_projeto(caminho(),identificador): abort(404)
        banco.registrar_log(caminho(),session['admin_id'],'excluir projeto',f'projeto:{identificador}')
        flash('Projeto e mídias vinculadas foram removidos.','sucesso')
        return redirect(url_for('conteudo'))

    @app.route('/admin/relatorio',methods=['GET'])
    @protegido
    def relatorio():
        return render_template('relatorio.html',totais=banco.totais(caminho()),projetos=banco.resumo_projetos(caminho()),cidades=banco.listar_voluntarios_por_cidade(caminho()))

    @app.route('/admin/doacoes', methods=['GET','POST'])
    @protegido
    def doacoes():
        dados=request.form.to_dict() if request.method=='POST' else {}
        parceiros,registros=banco.listar_doacoes(caminho())
        if request.method=='POST':
            tipo=dados.get('tipo'); descricao=dados.get('descricao','').strip(); valor=None
            erros=[]
            if tipo not in ('financeira','materiais','servicos'): erros.append('Selecione o tipo de doação.')
            if not validar_texto(descricao,3,500): erros.append('Informe uma descrição de 3 a 500 caracteres.')
            if tipo=='financeira':
                try:
                    quantia=Decimal(dados.get('valor','').replace(',','.'))
                    if not quantia.is_finite() or quantia<=0 or quantia>100000000 or quantia.as_tuple().exponent < -2: raise InvalidOperation()
                    valor=float(quantia)
                except (InvalidOperation,ValueError): erros.append('Informe um valor positivo com até duas casas decimais.')
            if erros:
                flash(' '.join(erros)+' Os campos foram preservados.','erro')
                return render_template('doacoes.html',parceiros=parceiros,registros=registros,dados=dados),400
            if not banco.registrar_doacao(caminho(),dados.get('parceiro_id'),tipo,valor,descricao,session['admin_id']):
                flash('Selecione um parceiro válido.','erro')
                return render_template('doacoes.html',parceiros=parceiros,registros=registros,dados=dados),400
            flash('Doação registrada no banco; nenhum pagamento foi processado.','sucesso')
            return redirect(url_for('doacoes'))
        return render_template('doacoes.html',parceiros=parceiros,registros=registros,dados=dados)

    @app.route('/admin/conteudo', methods=['GET','POST'])
    @protegido
    def conteudo():
        projetos,textos=banco.listar_conteudo_admin(caminho())
        if request.method=='POST':
            dados=request.form.to_dict(); tipo=dados.get('tipo'); titulo=dados.get('titulo','').strip()
            projetos,textos=banco.listar_conteudo_admin(caminho())
            if tipo=='projeto':
                erros=validar_projeto(dados)
                if erros:
                    flash('Confira os campos: '+' '.join(erros.values())+' Os valores foram preservados.','erro')
                    return render_template('conteudo.html',projetos=projetos,textos=textos,dados=dados),400
                valores=(titulo,dados.get('objetivo','').strip(),dados.get('tema','').strip(),dados.get('situacao','').strip(),dados.get('imagem','').strip() or None)
                identificador=dados.get('id') or None
                if banco.salvar_projeto(caminho(),identificador,valores)==0: abort(404)
            elif tipo=='texto':
                chave=dados.get('chave',''); valor=dados.get('valor','').strip()
                if chave not in {'hero_titulo','hero_texto','missao','visao'} or not validar_texto(valor,2,1200):
                    flash('Texto inválido. O conteúdo digitado foi preservado.','erro')
                    return render_template('conteudo.html',projetos=projetos,textos=textos,dados=dados),400
                if not banco.salvar_texto(caminho(),chave,valor): abort(404)
            elif tipo=='foto':
                url=dados.get('url',''); fonte=dados.get('fonte','')
                if not validar_texto(titulo,2,160) or not validar_url_https(url) or not validar_url_https(fonte) or dados.get('autorizacao')!='on':
                    flash('Revise título, endereços HTTPS e autorização. Os valores foram preservados.','erro')
                    return render_template('conteudo.html',projetos=projetos,textos=textos,dados=dados),400
                projeto=dados.get('projeto_id') or None
                if not banco.salvar_foto(caminho(),projeto,titulo,url,fonte,session['admin_id']): abort(400)
            else: abort(400)
            banco.registrar_log(caminho(),session['admin_id'],'conteúdo atualizado',tipo)
            flash('Conteúdo atualizado.','sucesso')
            return redirect(url_for('conteudo'))
        return render_template('conteudo.html',projetos=projetos,textos=textos,dados={})
