"""Regressão da central administrativa em banco temporário."""
import os
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as pasta:
    os.environ['SABA_DATABASE']=str(Path(pasta)/'teste.sqlite3')
    import app
    import banco
    from central import TEXTOS
    from conteudo_padrao import PADRAO
    from werkzeug.security import generate_password_hash
    banco.inserir_dados_iniciais(app.DB_PATH)
    banco.criar_admin(app.DB_PATH,'admin@example.com',generate_password_hash('senha-de-teste-123'))
    app.app.config['TESTING']=True
    c=app.app.test_client()
    assert c.get('/admin/central').status_code==302
    with c.session_transaction() as s: s['admin_id']=1; s['csrf']='teste'
    def post(destino,**dados):
        return c.post(destino,data={**dados,'_csrf':'teste'})
    for pagina in ['/admin','/admin/central','/admin/aparencia','/admin/novo/voluntario','/admin/central/midias/0']:
        assert c.get(pagina).status_code==200,pagina
    for i in range(55):
        banco.registrar_voluntario(app.DB_PATH,dict(nome=f'Pessoa {i:02}',email=f'p{i}@example.com',telefone='11999999999',cidade='Boa Vista',disponibilidade='',interesses=''))
    rows,total,_=banco.buscar_painel(app.DB_PATH,'voluntarios','','',2)
    assert total==55 and len(rows)==20
    assert len(banco.buscar_painel(app.DB_PATH,'voluntarios','','',3)[0])==15
    assert banco.buscar_painel(app.DB_PATH,'voluntarios','Pessoa 02','',1)[1]==1
    assert banco.buscar_painel(app.DB_PATH,'voluntarios',"' OR 1=1 --",'',1)[1]==0
    assert c.get('/admin?categoria=voluntarios&pagina=999999').status_code==302
    assert post('/admin/cadastro/voluntario/1',nome='Nome editado',email='p0@example.com',telefone='11999999999',cidade='Manaus',disponibilidade='',interesses='').status_code==302
    assert banco.obter_voluntario(app.DB_PATH,1)['nome']=='Nome editado'
    assert post('/admin/novo/parceiro',nome='Parceiro teste',email='p@example.com',telefone='11999999999',tipo_pessoa='juridica',tipo_apoio='Alimentos',consentimento='on').status_code==302
    assert post('/admin/central/noticias/0',titulo='Noticia nova',resumo='Resumo da noticia',data='2026-11-08',imagem='').status_code==302
    assert b'Noticia nova' in c.get('/').data
    assert post('/admin/central/midias/0',titulo='Imagem teste',url='javascript:alert(1)',fonte='https://example.com',projeto_id='1001').status_code==400
    assert post('/admin/central/midias/0',titulo='Imagem teste',url='https://example.com/image.png',fonte='https://example.com',projeto_id='1001').status_code==302
    assert post('/admin/central/noticias/1003/excluir').status_code==400
    assert c.get('/admin/central/noticias/1003/excluir').status_code==200
    assert post('/admin/central/noticias/1003/excluir',confirmacao='sim').status_code==302
    dados={**PADRAO,**banco.obter_conteudo(app.DB_PATH)}
    dados={k:dados.get(k,'') for k in TEXTOS}
    dados['hero_titulo']='Banner atualizado'
    assert post('/admin/aparencia',**dados).status_code==302
    assert b'Banner atualizado' in c.get('/').data
    assert c.post('/admin/aparencia',data=dados).status_code==400
    with banco.conectar(app.DB_PATH) as db:
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    with c.session_transaction() as s: s.clear()
    for url in ['/admin/central','/admin/aparencia','/admin/central/projetos/1001','/admin/novo/parceiro']:
        assert c.get(url).status_code==302
    print('OK: 55 cadastros, busca, paginação, edição, criação, conteúdo público, exclusão, validação, CSRF e acesso.')
