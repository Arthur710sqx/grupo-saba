"""Carrega conteúdo demonstrativo no banco sem substituir registros."""
import os
from pathlib import Path
from banco import inicializar_banco, inserir_dados_iniciais

CAMINHO = Path(os.environ.get('SABA_DATABASE', str(Path(__file__).resolve().parent / 'grupo_saba.sqlite3')))

if __name__ == '__main__':
    inicializar_banco(CAMINHO)
    inserir_dados_iniciais(CAMINHO)
    print(f'Dados demonstrativos preparados em: {CAMINHO}')
