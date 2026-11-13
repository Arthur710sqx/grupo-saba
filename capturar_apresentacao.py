"""Capturas de demonstração em banco temporário, sem acesso a cadastros reais."""
import os
import tempfile
import threading
from pathlib import Path
from werkzeug.serving import make_server
from werkzeug.security import generate_password_hash
from playwright.sync_api import sync_playwright

destino=Path(__file__).parent.parent/'apresentacao-saba'/'assets'
destino.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as pasta:
    os.environ['SABA_DATABASE']=str(Path(pasta)/'demo.sqlite3')
    import app
    import banco
    banco.inserir_dados_iniciais(app.DB_PATH)
    banco.criar_admin(app.DB_PATH,'demo@example.com',generate_password_hash('demonstracao-123'))
    banco.registrar_voluntario(app.DB_PATH,dict(nome='Voluntária de demonstração',email='voluntaria@example.com',telefone='11999990000',cidade='Boa Vista',disponibilidade='Sábados',interesses='Apoio em ações comunitárias'))
    banco.registrar_parceiro(app.DB_PATH,dict(nome='Apoiador de demonstração',email='apoio@example.com',telefone='11999990000',tipo_pessoa='fisica',tipo_apoio='Materiais para ações'))
    banco.registrar_beneficiario(app.DB_PATH,dict(nome='Solicitação de demonstração',contato='11999990000',localizacao='Boa Vista',situacao='Pedido para avaliação da equipe',necessidades='Apoio alimentar'))
    server=make_server('127.0.0.1',0,app.app)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
            page=browser.new_page(viewport={'width':1400,'height':1000},device_scale_factor=1)
            base=f'http://127.0.0.1:{server.server_port}'
            def shot(route,name,selector=None):
                page.goto(base+route,wait_until='domcontentloaded')
                page.evaluate('document.fonts.ready')
                if selector: page.locator(selector).screenshot(path=str(destino/name))
                else: page.screenshot(path=str(destino/name))
            shot('/quem-somos','historia.png','.story-cover')
            shot('/voluntariado','cadastro.png','main .page')
            page.goto(base+'/admin/entrar')
            page.locator('[name=email]').fill('demo@example.com')
            page.locator('[name=senha]').fill('demonstracao-123')
            page.get_by_role('button',name='Entrar',exact=True).click()
            shot('/admin','painel.png')
            shot('/admin/beneficiario/1','acompanhamento.png','main .page')
            shot('/admin/central','conteudo.png')
            page.goto(base+'/')
            page.locator('#abrir-acesso').click()
            page.locator('#access-panel').screenshot(path=str(destino/'acessibilidade.png'))
            page.set_viewport_size({'width':390,'height':844})
            shot('/admin?categoria=voluntarios&q=demo','mobile.png')
            browser.close()
    finally:
        server.shutdown();thread.join()
print(destino)
