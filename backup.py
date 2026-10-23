import os
import sqlite3
from datetime import datetime
from pathlib import Path
raiz = Path(__file__).resolve().parent
origem = Path(os.environ.get('SABA_DATABASE', str(raiz / 'grupo_saba.sqlite3'))).resolve()
if not origem.is_file():
    raise SystemExit('Banco não encontrado. Inicie o aplicativo primeiro.')
destino = raiz / 'backups' / ('saba-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.sqlite3')
destino.parent.mkdir(exist_ok=True)
fonte = sqlite3.connect(origem.as_uri() + '?mode=ro', uri=True)
copia = sqlite3.connect(destino)
try:
    fonte.backup(copia)
finally:
    copia.close()
    fonte.close()
print(f'Cópia salva: {destino}')
