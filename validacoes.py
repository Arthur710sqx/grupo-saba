import re
def validar_email(email): return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email or ''))
def validar_telefone(telefone): return 10 <= len(re.sub(r'\D','',telefone or '')) <= 13
def validar_consentimento(valor): return valor in (True,1,'1','on')
