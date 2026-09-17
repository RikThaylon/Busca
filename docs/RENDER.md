# Deploy na Render

Este repositório possui uma configuração de deploy pronta para a **demonstração pública** usando Render Blueprint.

## Arquitetura do deploy

Na Render, frontend e backend são empacotados em um único Web Service Docker:

- Vite/React é compilado durante o build.
- FastAPI serve a API em `/api/*`.
- O mesmo FastAPI entrega o frontend compilado.
- Frontend e API ficam no mesmo domínio, preservando cookies, proteção de origem e autenticação.
- `/api/health` é usado como health check.
- O serviço lê a porta fornecida automaticamente pela variável `PORT` da Render.

Arquivos envolvidos:

- `render.yaml`
- `Dockerfile.render`
- `backend/app/render.py`

## Deploy da demonstração

1. Faça merge das alterações de deploy na branch principal.
2. Entre em https://dashboard.render.com/.
3. Clique em **New > Blueprint**.
4. Conecte sua conta do GitHub e selecione o repositório `RikThaylon/Busca`.
5. A Render detectará `render.yaml` na raiz do projeto.
6. Revise o serviço `busca-documental-demo` e clique em **Apply**.
7. Aguarde o build e o health check `/api/health` ficarem verdes.
8. Abra a URL `https://<nome-do-servico>.onrender.com` criada pela Render.

O domínio público é injetado automaticamente em `APP_ORIGIN`, então não é necessário editar a URL manualmente.

## Login da demonstração

Administrador:

- E-mail: `demo@busca.local`
- Senha: `Demo-Ficticia-2026!`

Leitor:

- E-mail: `leitor@busca.local`
- Senha: `Demo-Leitor-2026!`

O seed fictício é executado automaticamente durante a inicialização do container no modo `demo`.

## Limitação importante do plano gratuito

O Blueprint usa `plan: free` para facilitar a demonstração. O filesystem do Web Service gratuito é efêmero. Isso significa que:

- uploads feitos pelo usuário podem desaparecer depois de restart, redeploy ou spin-down;
- o SQLite local pode ser recriado;
- os documentos fictícios da demonstração são restaurados pelo seed ao iniciar novamente.

Portanto, use este Blueprint apenas para demonstração, avaliação comercial e testes com dados fictícios.

## Produção / piloto com documentos reais

Não use o Blueprint gratuito atual para documentos reais.

Para piloto ou produção, configure no mínimo:

1. Web Service pago para evitar as limitações do plano gratuito.
2. PostgreSQL compatível com `pgvector` em `DATABASE_URL`.
3. Armazenamento persistente para `/app/data` ou armazenamento de objetos aprovado.
4. `APP_MODE=pilot`.
5. `SECURE_COOKIE=true`.
6. `APP_ORIGIN=https://seu-dominio`.
7. `STORAGE_KEY` gerada e armazenada como secret fora do repositório.
8. Provedor de embeddings configurado em `AI_PROVIDER`, `AI_BASE_URL`, `EMBED_MODEL` e demais variáveis necessárias.
9. Aprovação contratual antes de definir `EXTERNAL_AI_APPROVED=true` para provedores externos.

O modo `pilot` já bloqueia inicialização insegura quando PostgreSQL, HTTPS, cookie seguro ou provedor real não estão configurados.

## Diagnóstico rápido

Se o deploy falhar, confira os logs do serviço e valide estes pontos:

- `Dockerfile.render` foi encontrado na raiz do repositório.
- O build do frontend terminou com `npm run build`.
- Uvicorn iniciou em `0.0.0.0:$PORT`.
- `/api/health` retorna HTTP 200.
- `APP_ORIGIN` corresponde exatamente à URL HTTPS pública do serviço.

