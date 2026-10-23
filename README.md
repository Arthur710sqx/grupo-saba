# Grupo Sabá — aplicação Python com banco de dados

Site institucional e gestão local em Flask e SQLite. A abertura da página inicial foi preservada. Os cadastros são persistentes.

## Abrir e executar no Windows

Abra grupo-saba.code-workspace no VS Code. No terminal da pasta:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abra http://127.0.0.1:5000. Se uma versão antiga estiver aberta, encerre-a com Ctrl+C e execute novamente. Não é necessário ativar o ambiente nem usar py ou pip isoladamente. F5 exige as extensões Python e Python Debugger.

Em outro computador, instale Python 3.10+, execute `python -m venv .venv` e `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. O ambiente virtual não acompanha o Git/ZIP.

## Primeiro acesso da equipe

Na própria máquina, abra /admin/primeiro-acesso e escolha e-mail e senha de pelo menos 12 caracteres. Não existe senha padrão. Depois use /admin/entrar. O cadastro inicial é desativado quando existe um administrador. Cadastre a equipe antes de expor a instalação na rede.

## Fluxos implementados

- Voluntários: contato, cidade, disponibilidade, interesses e situação novo/contatado/ativo/inativo.
- Beneficiários: cadastro → agendamento → visita com avaliação humana justificada → prioridade → atendimento. A ficha mantém histórico de agendamentos, visitas e atendimentos. Reagendar preserva a agenda anterior; a avaliação conclui agendas até sua data.
- Parceiros: pessoas físicas ou jurídicas, contato, colaboração e situação.
- Doações: valores financeiros, materiais ou serviços vinculados ao parceiro. Registro interno; não processa pagamento nem emite recibo fiscal.
- Projetos: busca pública, página individual, cadastro e edição pela equipe.
- Galeria: fotos oficiais, ampliação, fonte e vínculo a projeto. A equipe cadastra URLs HTTPS de imagens autorizadas. Vídeo abre no Instagram. Imagens dependem do servidor de origem.
- Transparência: identificação e fontes institucionais. Sem indicadores ou relatórios inventados.

## Banco e relacionamentos

O arquivo grupo_saba.sqlite3 é criado automaticamente e permanece após fechar o aplicativo. SABA_DATABASE permite escolher outro caminho. Migrações preservam os registros existentes. Projetos demonstrativos antigos (IDs inferiores a 1001) permanecem armazenados, fora da apresentação pública.

| Tabela | Finalidade |
|---|---|
| voluntarios | Cadastro, disponibilidade e situação |
| beneficiarios | Solicitação e prioridade definida pela equipe |
| agendamentos | Datas e responsáveis vinculados ao beneficiário |
| visitas_beneficiarios | Avaliações e justificativas vinculadas ao beneficiário |
| atendimentos | Histórico de apoios e encaminhamentos |
| parceiros_doadores | Pessoas físicas e jurídicas |
| doacoes_parcerias | Doações vinculadas ao parceiro |
| projetos / midias | Projetos e referências às fotografias |
| noticias / acoes_eventos / site_conteudo | Conteúdo institucional e estrutura de eventos |
| usuarios_admin / logs_auditoria | Senhas com hash e alterações de gestão |

Administradores têm o mesmo acesso nesta versão. Dados pessoais não aparecem em páginas públicas. Consultas parametrizadas, chaves estrangeiras, proteção CSRF e senhas com hash. SQLite é um arquivo sem criptografia própria: proteja a pasta e suas cópias.

## Testes e backup

```powershell
.\.venv\Scripts\python.exe revisar_fluxos.py
.\.venv\Scripts\python.exe backup.py
```

Os testes usam banco temporário isolado: páginas, cadastros, login, bloqueio anônimo, CSRF, visitas, agenda, atendimento, doações e conteúdo. O backup usa a API SQLite e salva em backups/. Mantenha cópia protegida fora do computador. Para restaurar, pare o servidor, preserve uma cópia do banco atual e copie o backup escolhido para o caminho do banco.

## Fontes e publicação

Fontes: https://gruposaba.org/sobre-nos/, https://gruposaba.org/fotos/ e notícias institucionais. Trans-formando Identidades é iniciativa da Defensoria Pública de Roraima divulgada pelo Grupo Sabá. Fotos referenciadas do acervo oficial.

Entrega preparada para execução local. Antes da operação pública: validar textos, autorização de imagens, aviso de privacidade e retenção; configurar HTTPS, FLASK_SECRET_KEY persistente, cookies seguros, servidor de produção, backups e proteção contra abuso. Não exponha o servidor de desenvolvimento na internet. Não há envio automático de mensagens, pagamento online ou conta individual de beneficiário: contato e avaliação são feitos pela equipe.

## Git

Repositório local versionado. Banco, ambiente e backups não entram no Git. Não há remoto configurado; envio ao GitHub requer endereço do repositório e autenticação do proprietário.
