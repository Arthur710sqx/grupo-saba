# Grupo SABA — cadastro web
Projeto em Ciência de Dados I (IBM4023), Ibmec. Equipe: Arthur Franco Siqueira, Enzo Cardin e Gustavo. Matrículas não informadas.
Aplicação didática local para cadastrar voluntários e beneficiários e consultar participações vinculadas às fichas. O Grupo SABA é o domínio do projeto em grupo. Os quatro domínios do enunciado da AC1 se referem ao exercício individual.

## Como rodar no Windows
Na pasta do projeto, use Python 3 e execute:
```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python dados_iniciais.py
python criar_logins.py
python app.py
```
No PowerShell, a ativação é feita com `.\.venv\Scripts\Activate.ps1`. No macOS/Linux, use `source .venv/bin/activate`. Abra http://127.0.0.1:5000. Encerre com Ctrl+C. O arquivo dados/cadastro.db é criado automaticamente. O exemplo cria três fichas fictícias e quatro participações. Uma ficha fica sem participação. O carregamento de exemplos é opcional e não modifica uma base que já contém pessoas. A criação de logins solicita senhas locais e preserva contas existentes. Uma nova execução do servidor exige novo login.
O requirements.txt contém os sete itens nas versões do checklist. No Windows o pip também instala a dependência transitiva colorama, exigida por Click.

## Rotas
| Método | Caminho | Operação e acesso |
|---|---|---|
| GET | / | Listar, leitura aberta |
| GET | /busca | Buscar por termo e grupo, leitura aberta |
| GET | /pessoa/<id> | Ver ficha e participações, leitura aberta |
| GET | /relatorio | Contagens por grupo e categoria, leitura aberta |
| GET | /sobre | Identificação do projeto |
| GET, POST | /login | Entrar |
| POST | /logout | Sair |
| GET, POST | /novo | Cadastrar, comum ou admin |
| GET, POST | /pessoa/<id>/editar | Editar, comum ou admin |
| POST | /pessoa/<id>/excluir | Excluir ficha e participações, somente admin |

## Regras e organização
Nome, documento, nascimento, telefone, grupo e categoria são obrigatórios. A categoria pertence ao grupo. Voluntários exigem CPF válido e voluntários profissionais exigem especialidade. Beneficiários também admitem documento alternativo. Documento repetido no mesmo grupo é recusado mesmo com variação de pontuação ou maiúsculas. A edição mantém o grupo, o ID e a data de inclusão.
app.py trata HTTP; banco.py concentra SQL; validacoes.py reúne as regras. Templates herdam de base.html e carregam static/estilo.css. Participações são exemplos para consulta por chave estrangeira. Logins armazenam hashes Werkzeug. Com leitura aberta conforme a aula, utilize dados fictícios na demonstração. Esta versão cria uma base própria. Não importa automaticamente fichas da aplicação desktop anterior.

## O que depende da equipe
Matrículas, registros de entrevistas, validação da organização e contribuições individuais.

## Versão acadêmica no GitHub
[Arthur710sqx/grupo-saba — branch projeto-academico-2026-2](https://github.com/Arthur710sqx/grupo-saba/tree/projeto-academico-2026-2). No GitHub, selecione essa branch para consultar esta versão.

