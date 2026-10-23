"""Verificação isolada: não modifica cadastros reais."""
import tempfile
import os
from datetime import date, timedelta
from pathlib import Path
from banco import inicializar_banco, conectar

with tempfile.TemporaryDirectory() as pasta:
    os.environ['SABA_DATABASE'] = str(Path(pasta) / 'teste.db')
    import app as modulo
    modulo.DB_PATH = Path(pasta) / 'teste.db'
    inicializar_banco(modulo.DB_PATH)
    inicializar_banco(modulo.DB_PATH)
    c = modulo.app.test_client()
    for pagina in ['/', '/projetos', '/como-ajudar', '/transparencia', '/voluntariado', '/apoio', '/parcerias', '/admin/entrar']:
        assert c.get(pagina).status_code == 200, pagina
    assert c.get('/admin').status_code == 302
    def enviar(url, dados):
        c.get(url)
        with c.session_transaction() as s:
            dados['_csrf'] = s['csrf']
        return c.post(url, data=dados)
    assert enviar('/apoio', {}).status_code == 400
    assert enviar('/apoio', dict(nome='Teste',contato='11999999999',localizacao='Boa Vista',situacao='Avaliar',necessidades='Alimentos',consentimento='on')).status_code == 302
    assert enviar('/voluntariado',dict(nome='Teste',email='teste@example.com',telefone='11999999999',cidade='Boa Vista',consentimento='on')).status_code == 302
    for tipo in ['fisica','juridica']:
        assert enviar('/parcerias',dict(tipo_pessoa=tipo,nome='Parceiro',email='parceiro@example.com',telefone='11999999999',tipo_apoio='Materiais',consentimento='on')).status_code == 302
    assert enviar('/admin/primeiro-acesso',dict(email='admin@example.com',senha='senha-teste-longa-123')).status_code == 302
    assert enviar('/admin/entrar',dict(email='admin@example.com',senha='senha-teste-longa-123')).status_code == 302
    assert c.get('/admin').status_code == 200
    assert enviar('/admin/beneficiario/1/visita',dict(data='2026-01-01',responsavel='Equipe',observacoes='Avaliação humana documentada.',urgencia='alta')).status_code == 302
    with conectar(modulo.DB_PATH) as db:
        assert db.execute('SELECT prioridade FROM beneficiarios').fetchone()[0] == 'alta'
        assert db.execute('SELECT COUNT(*) FROM projetos').fetchone()[0] == 3
        assert db.execute('SELECT COUNT(*) FROM logs_auditoria').fetchone()[0] == 1
    assert c.post('/apoio',data={}).status_code == 400
    for pagina in ['/galeria','/projetos/1001','/admin/doacoes','/admin/conteudo','/admin/beneficiario/1']:
        assert c.get(pagina).status_code == 200, pagina
    assert c.get('/projetos/999999').status_code == 404
    assert enviar('/admin/beneficiario/1/acompanhar',dict(acao='agendar',data=(date.today()+timedelta(days=1)).isoformat(),responsavel='Equipe')).status_code == 302
    assert enviar('/admin/beneficiario/1/acompanhar',dict(acao='atendimento',status='atendido',descricao='Cesta entregue e encaminhamento registrado.')).status_code == 302
    assert enviar('/admin/cadastro/voluntario/1',dict(status='ativo')).status_code == 302
    assert enviar('/admin/cadastro/parceiro/1',dict(status='ativo')).status_code == 302
    for valor in ['-1','NaN','Infinity','1.001']:
        assert enviar('/admin/doacoes',dict(parceiro_id='1',tipo='financeira',valor=valor,descricao='Doação inválida')).status_code == 400
    assert enviar('/admin/doacoes',dict(parceiro_id='1',tipo='financeira',valor='125.50',descricao='Doação para alimentos')).status_code == 302
    assert enviar('/admin/doacoes',dict(parceiro_id='2',tipo='materiais',descricao='10 kits de higiene')).status_code == 302
    assert enviar('/admin/conteudo',dict(tipo='foto',titulo='Teste',url='javascript:alert(1)',fonte='https://gruposaba.org',autorizacao='on')).status_code == 400
    assert enviar('/admin/conteudo',dict(tipo='projeto',titulo='Projeto de teste',objetivo='Descrição verificada',tema='Comunidade',situacao='Em andamento')).status_code == 302
    assert enviar('/admin/conteudo',dict(tipo='foto',titulo='Foto de teste',url='https://gruposaba.org/wp-content/uploads/2025/01/01.png',fonte='https://gruposaba.org/fotos/',projeto_id='1004',autorizacao='on')).status_code == 302
    assert b'Projeto de teste' in c.get('/projetos/1004').data
    with conectar(modulo.DB_PATH) as db:
        assert db.execute('SELECT COUNT(*) FROM doacoes_parcerias').fetchone()[0] == 2
        assert db.execute('SELECT status FROM beneficiarios WHERE id=1').fetchone()[0] == 'atendido'
        assert db.execute('SELECT COUNT(*) FROM atendimentos').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM agendamentos').fetchone()[0] == 1
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    inicializar_banco(modulo.DB_PATH)
    assert c.get('/admin/beneficiario/1').status_code == 200
    assert enviar('/admin/sair',{}).status_code == 302
    for pagina in ['/admin','/admin/doacoes','/admin/conteudo','/admin/beneficiario/1']:
        assert c.get(pagina).status_code == 302
    assert enviar('/admin/doacoes',dict(parceiro_id='1',tipo='materiais',descricao='Não autorizado')).status_code == 302
    print('Agendamento, histórico, atendimento, parceiros PF/PJ, doações, conteúdo e acesso restrito: OK.')
    print('Fluxos públicos, autenticação, visita, auditoria, CSRF e reinicialização: OK.')
