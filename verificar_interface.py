"""Verificação opcional com Playwright e Edge, usando banco isolado."""
import os
import tempfile
import threading
from pathlib import Path
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory() as pasta:
    os.environ['SABA_DATABASE']=str(Path(pasta)/'interface.sqlite3')
    import app
    import banco
    banco.inserir_dados_iniciais(app.DB_PATH)
    server=make_server('127.0.0.1',0,app.app)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1000})
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='domcontentloaded')
            assert page.locator('#abrir-acesso').count()==1
            page.locator('#abrir-acesso').click()
            assert page.locator('#access-panel').evaluate('(el)=>el.open')
            page.locator('#fonte-mais').click()
            assert page.locator('#font-value').inner_text()=='110%'
            page.locator('#fonte-menos').click()
            assert page.locator('#font-value').inner_text()=='100%'
            for control,css in [('alto-contraste','high-contrast'),('inverter','inverted'),('cinza','grayscale'),('letras','spaced-letters'),('linhas','spaced-lines'),('links','highlight-links'),('titulos','highlight-titles'),('menos-movimento','reduce-motion')]:
                page.locator('#'+control).click()
                assert page.locator('html').evaluate('(el,c)=>el.classList.contains(c)',css)
                assert page.locator('#'+control).get_attribute('aria-pressed')=='true'
                page.locator('#'+control).click()
            page.locator('#regua').click()
            page.locator('#mascara').click()
            page.keyboard.press('Escape')
            assert page.locator('#abrir-acesso').evaluate('(el)=>el===document.activeElement')
            assert page.locator('#reading-guide').is_visible()
            page.screenshot(path='../acessibilidade-desktop.png')
            page.mouse.move(100,350)
            assert abs(page.locator('#reading-guide').evaluate('(el)=>parseFloat(el.style.top)')-35)<2
            page.reload(wait_until='domcontentloaded')
            assert page.locator('#reading-guide').is_visible()
            page.locator('#abrir-acesso').click()
            page.locator('#restaurar-acesso').click()
            assert page.locator('#reading-guide').get_attribute('hidden') is not None
            page.keyboard.press('Escape')
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.locator('#abrir-acesso').click()
            assert page.locator('#access-panel').is_visible()
            page.locator('#fonte-mais').click()
            page.locator('#fechar-acesso').click()
            from werkzeug.security import generate_password_hash
            banco.criar_admin(app.DB_PATH, 'admin@example.com', generate_password_hash('senha-de-teste-123'))
            page.goto(f'http://127.0.0.1:{server.server_port}/admin/entrar')
            page.locator('input[name=email]').fill('admin@example.com')
            page.locator('input[name=senha]').fill('senha-de-teste-123')
            page.get_by_role('button',name='Entrar',exact=True).click()
            assert page.get_by_role('heading',name='Painel da equipe').is_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.goto(f'http://127.0.0.1:{server.server_port}/admin/central')
            assert page.get_by_role('heading',name='Gerenciar conteúdo').is_visible()
            page.screenshot(path='../administracao-mobile.png',full_page=True)
            assert not errors,errors
            page.goto(f'http://127.0.0.1:{server.server_port}/quem-somos')
            assert page.locator('.story-timeline li').count()==6
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.set_viewport_size({'width':1440,'height':1000})
            page.screenshot(path='../historia-grupo-saba.png',full_page=True)
            browser.close()
            print('OK: navegador desktop/mobile, controles, persistência, máscara, régua, Esc, foco, login e tabelas.')
    finally:
        server.shutdown()
        thread.join()
