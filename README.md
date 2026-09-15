# BRIMAJOR AI DOCS

**Encontre em segundos informações espalhadas em procedimentos, manuais e documentos internos.**

MVP de inteligência documental para validar um **piloto pago de 30 dias**. Interface com Documentos, Assistente e Histórico; respostas extrativas com documento, página, seção e abertura da evidência.

> DADOS FICTÍCIOS — AMBIENTE DEMONSTRATIVO. A empresa Aurora Componentes e os cinco documentos incluídos são inteiramente fictícios. Não usar suas instruções em operações reais.

## Decisão de produto

**GO condicionado para descoberta e piloto; NO-GO para investir em SaaS amplo antes de demonstrar demanda e economia de tempo.** Não existe validação de mercado ou cliente contratado. [Avaliação completa e 12 entregáveis](docs/PLANO-PILOTO.md).

## Rodar a demonstração local

Requer Python 3.12, Node 22+, Linux/macOS (o extrator usa limites de recursos POSIX). No Windows, use WSL2 ou Docker Desktop. O download e a instalação das dependências não estão incluídos nos dois minutos de apresentação.

Terminal 1, a partir da raiz:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli demo
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Terminal 2:

```bash
cd frontend
npm ci
npm run dev
```

Abra `http://localhost:5173` (use **localhost**, não 127.0.0.1, para corresponder à origem configurada). O login demonstrativo já vem preenchido:

| Perfil | E-mail | Senha fictícia |
|---|---|---|
| Administrador | demo@brimajor.local | Demo-Ficticia-2026! |
| Leitor | leitor@brimajor.local | Demo-Leitor-2026! |

Este modo usa **SQLite + busca textual**, sem modelo, API ou embeddings simulados. Serve para demonstrar o fluxo, não para comprovar qualidade de busca semântica.

## Rodar com PostgreSQL/pgvector

Copie `.env.example` para `.env`, substitua a senha por um valor hexadecimal aleatório e execute:

```bash
docker compose build
docker compose up -d db
docker compose run --rm api python -m app.cli demo
docker compose up -d api web
```

Abra `http://localhost:8080`. Não há porta pública do banco ou da API. O frontend fica restrito ao computador local por padrão. Não exponha a demonstração à internet.

## Modelo open source básico: configuração recomendada

Comece com **Qwen3-Embedding 0.6B via Ollama**, sem gerador. O modelo local recupera evidências; a aplicação devolve os trechos literais. Só adicione `qwen3:4b` se ele melhorar a seleção em um conjunto de avaliação em português. [Análise, limites e teste de aprovação](docs/MODELO-LOCAL.md).

1. Instale Ollama no host e execute `ollama pull qwen3-embedding:0.6b`.
2. Copie `.env.ollama.example` para `.env` e ajuste a senha do banco.
3. Garanta conectividade **privada** do contêiner à API Ollama. Em Linux, o Ollama limitado a loopback pode não aceitar `host.docker.internal`; ajuste a interface e firewall somente para a rede Docker, sem exposição pública.
4. Execute os mesmos comandos Docker acima em uma instalação limpa.
5. Para experimentar seleção por LLM: `ollama pull qwen3:4b`, configure `CHAT_MODEL=qwen3:4b` e recrie o serviço API.

Mudar modelo de embeddings exige **reprocessar documentos**. O perfil gravado impede misturar espaços vetoriais; os documentos com perfil diferente deixam de participar da busca. Mudar dimensão exige migração/recriação do índice, não apenas alterar `.env`. Não apague volumes de clientes para isso.

## Piloto com documentos reais

Use `.env.pilot.example`, chave de criptografia própria, HTTPS em proxy aprovado, contas nominativas e aprovação de TI. O modo piloto recusa SQLite, provedor ausente, cookie inseguro e origem sem HTTPS. O seed demonstrativo é bloqueado nesse modo.

```bash
docker compose run --rm api python -m app.cli init
docker compose run --rm api python -m app.cli create-user --tenant "Cliente piloto" --email "admin@cliente.example" --role admin
docker compose run --rm api python -m app.cli create-user --tenant "Cliente piloto" --email "leitor@cliente.example" --role reader
```

As senhas são solicitadas sem eco. Não há cadastro público nem escolha de organização pelo usuário. Agende a limpeza diária no host: `docker compose run --rm api python -m app.cli cleanup`. A expiração já bloqueia consulta e fontes imediatamente, mesmo antes da limpeza física.

Leia [arquitetura](docs/ARQUITETURA.md) e [segurança e implantação](docs/SECURITY.md) antes de inserir dados reais. A aplicação não executa treinamento. A política de retenção e treinamento de provedores externos depende de contrato e configuração do provedor.

## Verificação

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```

Sem `TEST_DATABASE_URL`, roda SQLite e pula o teste vetorial. Use um **banco exclusivamente de testes** em `TEST_DATABASE_URL`; os testes apagam suas tabelas. O workflow testa PostgreSQL/pgvector e compila o frontend. As chamadas de embeddings no teste vetorial são controladas: ele testa SQL/permissões, não a precisão de um modelo real.

## Limites desta versão

- PDF textual e TXT UTF-8: 10 MB, 100 páginas e 400 mil caracteres; até 100 documentos por organização.
- Processamento síncrono: adequado a baixa concorrência; sem fila distribuída.
- Papéis admin/leitor e documentos compartilhados com equipe ou restritos a admins. Sem ACL por pessoa, departamento ou importada do SharePoint.
- Trechos citados são conferidos contra o texto extraído. **Isso não garante relevância, vigência ou ausência de ambiguidade.** Não prometer “zero erro” ou “zero alucinação”.
- Fonte abre em visualizador de texto por página; original disponível para download autenticado. TXT usa separador `\f` para páginas lógicas; PDFs preservam o índice físico da página, não a numeração impressa.
- Não há OCR, análise de tabelas complexas, validação automática de versões conflitantes, SSO, antimalware completo ou certificação de conformidade.
- Integrações externas e inferência Ollama precisam de validação no ambiente do cliente antes do piloto.
