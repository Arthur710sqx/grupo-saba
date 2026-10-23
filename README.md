# Grupo Sabá — site institucional (base demonstrativa)

Aplicação Flask com páginas públicas responsivas e esquema SQLite preparado para projetos, ações, voluntários, beneficiários, visitas, parceiros, doações e auditoria. As informações institucionais não confirmadas aparecem como conteúdo a preencher pela equipe.

## Requisitos e execução

1. Instale Python 3.10 ou superior.
2. Na pasta do projeto, crie ambiente e instale dependências:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Configure `FLASK_SECRET_KEY` com um valor aleatório antes de publicar.
4. Execute `python app.py` e abra http://127.0.0.1:5000.

O banco é criado automaticamente ao iniciar. Para preparar o arquivo e um projeto explicitamente demonstrativo, execute `python dados_iniciais.py`. A senha de demonstração deve ser trocada; não publique credenciais padrão.

## Rotas

- `/` página inicial
- `/quem-somos` apresentação institucional
- `/projetos` projetos e ações (conteúdo a confirmar)
- `/transparencia` documentos e indicadores (conteúdo a confirmar)
- `/como-ajudar` formas de participação
- `/voluntariado` formulário demonstrativo
- `/privacidade` minuta de política para revisão jurídica

## Banco e validações

`banco.py` cria tabelas com chaves estrangeiras, restrições e índice de busca. `validacoes.py` reúne funções básicas de e-mail, telefone e consentimento. Use consultas parametrizadas (`?`) em toda operação SQL. Senhas administrativas devem ser armazenadas com hash seguro.

## Prontidão e limites

Esta entrega é uma base de site, não um sistema pronto para operar dados de pessoas. O formulário de voluntariado é apenas visual e não grava dados. Área administrativa, perfis, cadastros restritos, visitas, auditoria, exportação, mensagens, edição/exclusão POST-Redirect-GET e revisão humana de prioridade ainda precisam ser implementados e submetidos a revisão de segurança e LGPD antes de uso. O modelo de dados contém tabelas para orientar essa evolução. Não usar dados reais de beneficiários nesta demonstração.

Os textos de missão, contatos, projetos, indicadores, parceiros, imagens e documentos precisam de validação expressa da organização antes de publicação. A frase de campanha também depende de autorização.
