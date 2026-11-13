# Grupo Sabá — site e administração local

Aplicação web em Python, Flask e SQLite. O painel permite atualizar partes do site, acompanhar cadastros e consultar relatórios.

## Abrir no VS Code (Windows)

Abra `grupo-saba.code-workspace` no VS Code. Em **Terminal → Novo Terminal**, execute:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abra http://127.0.0.1:5000. Para parar o servidor, pressione `Ctrl+C` no terminal. Se não existir a pasta `.venv`, crie o ambiente e instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Banco de dados

O SQLite é o arquivo `grupo_saba.sqlite3` na raiz desta pasta, ao lado de `app.py`. A aplicação cria as tabelas e aplica migrações quando inicia. Cadastros ficam salvos nesse arquivo depois que o servidor fecha. O caminho pode ser definido com `SABA_DATABASE`. O `.gitignore` mantém o arquivo de fora do Git porque pode conter dados pessoais.

Em uma instalação nova, o banco começa sem conteúdo de demonstração. Para carregar o conteúdo inicial, execute uma vez:

```powershell
.\.venv\Scripts\python.exe dados_iniciais.py
```

Esse comando usa `INSERT OR IGNORE`: não substitui os cadastros que já existem. O `revisar_fluxos.py` prepara seus dados de exemplo em um banco temporário e não altera este arquivo.

## Acesso administrativo

Entre em `/admin/entrar` e use **Adicionar conta** acima de **Sair da conta**. Em uma instalação sem contas, configure o primeiro administrador no terminal do projeto com `.\.venv\Scripts\python.exe -m flask --app app inicializar-admin`.

No painel:

- `/admin/central`: busca e paginação de projetos, notícias e fotos; criação, edição individual e exclusão com confirmação. As imagens são cadastradas por URL HTTPS, sem upload de arquivos.
- `/admin/aparencia`: edição dos textos institucionais, apresentação, banner principal (imagem, descrição acessível e legenda), endereço e CNPJ.
- `/admin/novo/<categoria>`: cadastro administrativo de voluntário, parceiro ou beneficiário, mantendo a autorização de uso de dados.
- Os cadastros aparecem em tabelas de até 20 registros; o link “Gerenciar cadastro” reúne edição, situação e exclusão. Solicitações mantêm seus históricos.

## Ferramentas de acessibilidade

O botão no canto inferior abre um painel operável com Tab, Shift+Tab e Esc. Há fonte de 80% a 200%, contraste, inversão, escala de cinza, espaçamento, destaque de links/títulos, redução de animações e restauração. Régua e máscara acompanham ponteiro/toque ou a posição escolhida no controle deslizante; fora dos campos, as setas também ajustam a posição. Preferências ficam no navegador, sem gravar dados pessoais.

Verificações adicionais usam banco temporário:

```powershell
.\.venv\Scripts\python.exe verificar_melhorias.py
# Opcional: teste no Edge com Playwright instalado no ambiente de desenvolvimento
.\.venv\Scripts\python.exe -m pip install playwright
.\.venv\Scripts\python.exe verificar_interface.py
```

Os testes cobrem 55 cadastros, busca, paginação, edição, conteúdo publicado, validação, controle de acesso, CSRF e uso das ferramentas no navegador. Não equivalem a uma certificação de acessibilidade ou teste com todas as tecnologias assistivas.

## Fluxos existentes

- `/admin/conteudo`: altera textos institucionais, cria/edita projetos e publica referências de fotos HTTPS autorizadas; projetos podem ser removidos com suas mídias vinculadas.
- `/admin`: permite acompanhar solicitações, registrar avaliação de visita, editar e atualizar a situação de voluntários e parceiros, além de excluí-los quando permitido.
- `/admin/beneficiario/<id>`: agenda visita, registra avaliação, define prioridade após avaliação humana e mantém histórico de atendimentos.
- `/admin/doacoes`: registra contribuições financeiras, materiais e serviços. É apenas controle interno, sem processar pagamentos ou emitir recibos fiscais.
- `/admin/relatorio`: apresenta totais e agrupamentos por tema de projeto e cidade de voluntários.

## Estrutura de dados

| Tabela | Uso |
|---|---|
| `projetos`, `midias`, `noticias`, `acoes_eventos`, `site_conteudo` | Conteúdo do site e referências de mídia |
| `voluntarios` | Contato, disponibilidade e situação |
| `beneficiarios`, `agendamentos`, `visitas_beneficiarios`, `atendimentos` | Solicitações e histórico de acompanhamento |
| `parceiros_doadores`, `doacoes_parcerias` | Parceiros e contribuições recebidas |
| `usuarios_admin`, `logs_auditoria` | Acesso administrativo e registro de alterações |

As tabelas relacionadas usam chaves estrangeiras. As consultas de gravação usam parâmetros SQL; formulários verificam os campos antes de escrever e mantêm os valores em caso de erro. Há proteção CSRF nos formulários POST e senhas armazenadas com hash.

## Verificação e cópia de segurança

```powershell
.\.venv\Scripts\python.exe revisar_fluxos.py
.\.venv\Scripts\python.exe backup.py
```

O primeiro comando verifica páginas públicas, cadastros, autenticação, acompanhamento, doações, conteúdo e chaves estrangeiras usando arquivo temporário. O segundo cria uma cópia consistente em `backups/`. Guarde o banco e as cópias em local protegido; SQLite não cifra os dados por conta própria.

## Escopo e publicação

O visual e as informações institucionais tomam como referência o site oficial https://gruposaba.org/ e páginas de sobre, fotos e transparência. Revise textos, fontes e autorização das imagens antes de publicar externamente. A aplicação é para execução local: antes de operar publicamente, configure servidor de produção, HTTPS, chave secreta persistente, política de privacidade e rotina de cópias. Não exponha o servidor de desenvolvimento na internet.

O projeto tem repositório Git local. Banco, ambiente virtual e cópias de segurança ficam fora do Git; não há remoto configurado.
