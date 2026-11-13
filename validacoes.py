"""Regras de validação sem dependência de Flask ou de SQLite."""
import re
from urllib.parse import urlparse

def validar_email(email):
    return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', (email or '').strip()))

def validar_telefone(telefone):
    return 10 <= len(re.sub(r'\D','',telefone or '')) <= 13

def validar_consentimento(valor):
    return valor in (True,1,'1','on')

def validar_texto(valor, minimo=1, maximo=120):
    valor=(valor or '').strip()
    return minimo <= len(valor) <= maximo

def validar_voluntario(dados):
    erros = {}
    if not validar_texto(dados.get('nome'),2,120):
        erros['nome'] = 'Informe um nome com até 120 caracteres.'
    if not validar_email(dados.get('email')):
        erros['email'] = 'Informe um e-mail válido.'
    if not validar_telefone(dados.get('telefone')):
        erros['telefone'] = 'Informe um telefone válido com DDD.'
    if not validar_texto(dados.get('cidade'),2,100):
        erros['cidade'] = 'Informe uma cidade com até 100 caracteres.'
    if not validar_texto(dados.get('disponibilidade',''),0,300):
        erros['disponibilidade'] = 'Use até 300 caracteres.'
    if not validar_texto(dados.get('interesses',''),0,500):
        erros['interesses'] = 'Use até 500 caracteres.'
    if not validar_consentimento(dados.get('consentimento')):
        erros['consentimento'] = 'A autorização de contato é obrigatória.'
    return erros

def validar_beneficiario(dados):
    erros = {}
    for campo, rotulo, limite in [('nome','Nome',120),('localizacao','Localização',160),('situacao','Situação',500),('necessidades','Necessidades',500)]:
        if not validar_texto(dados.get(campo),2,limite):
            erros[campo] = f'{rotulo}: informe de 2 a {limite} caracteres.'
    if not validar_telefone(dados.get('contato')):
        erros['contato'] = 'Informe um telefone válido com DDD.'
    if not validar_consentimento(dados.get('consentimento')):
        erros['consentimento'] = 'A autorização para armazenamento é obrigatória.'
    return erros

def validar_parceiro(dados):
    erros = {}
    if dados.get('tipo_pessoa') not in ('fisica','juridica'):
        erros['tipo_pessoa'] = 'Escolha pessoa física ou jurídica.'
    if not validar_texto(dados.get('nome'),2,160):
        erros['nome'] = 'Informe o nome ou razão social (até 160 caracteres).'
    if not validar_email(dados.get('email')):
        erros['email'] = 'Informe um e-mail válido.'
    if not validar_telefone(dados.get('telefone')):
        erros['telefone'] = 'Informe um telefone válido com DDD.'
    if not validar_texto(dados.get('tipo_apoio'),2,300):
        erros['tipo_apoio'] = 'Descreva o tipo de apoio (até 300 caracteres).'
    if not validar_consentimento(dados.get('consentimento')):
        erros['consentimento'] = 'A autorização de contato é obrigatória.'
    return erros

def validar_projeto(dados):
    erros = {}
    for campo,rotulo,limite in [('titulo','Título',120),('objetivo','Descrição',1000),('tema','Tema',100),('situacao','Situação',120)]:
        minimo=2 if campo in ('titulo','objetivo') else 0
        if not validar_texto(dados.get(campo,''),minimo,limite):
            erros[campo] = f'{rotulo}: máximo de {limite} caracteres.'
    imagem=(dados.get('imagem') or '').strip()
    if imagem and not validar_url_https(imagem):
        erros['imagem'] = 'A imagem deve usar um endereço HTTPS válido.'
    return erros

def validar_url_https(url):
    try:
        parsed=urlparse(url or '')
        return parsed.scheme=='https' and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False

def validar_visita(dados):
    from datetime import date
    erros = {}
    try:
        dia=date.fromisoformat(dados.get('data',''))
        if dia>date.today():
            erros['data'] = 'A data não pode estar no futuro.'
    except ValueError:
        erros['data'] = 'Informe uma data válida no formato AAAA-MM-DD.'
    if not validar_texto(dados.get('responsavel'),2,120):
        erros['responsavel'] = 'Informe a pessoa responsável.'
    if not validar_texto(dados.get('observacoes'),10,1000):
        erros['observacoes'] = 'Registre uma justificativa de 10 a 1000 caracteres.'
    if dados.get('urgencia') not in ('baixa','media','alta'):
        erros['urgencia'] = 'Selecione um grau de urgência válido.'
    return erros
