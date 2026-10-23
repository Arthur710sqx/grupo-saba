"""Verificação isolada: não modifica cadastros reais."""
import tempfile
from pathlib import Path
import app as modulo
from banco import inicializar_banco, conectar

with tempfile.TemporaryDirectory() as pasta:
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
    print('Fluxos públicos, autenticação, visita, auditoria, CSRF e reinicialização: OK.')
