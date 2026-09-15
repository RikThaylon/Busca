# Arquitetura mínima e decisões

## Componentes

| Camada | Implementação |
|---|---|
| Interface | React + Vite + Tailwind; sem serviços externos de fontes ou analytics |
| API | FastAPI; autenticação por sessão opaca HttpOnly; endpoints protegidos |
| Banco | PostgreSQL com pgvector no piloto; SQLite exclusivamente como demo textual |
| Arquivos | Volume local criptografado; identificadores UUID gerados pelo servidor |
| Extração | PDF textual/TXT; processo com limites de memória/CPU/tempo; sem OCR |
| Recuperação | Embeddings desacoplados; busca vetorial exata, sem índice aproximado desnecessário para o volume inicial |
| Resposta | Extrativa; seletor LLM opcional com validação contra evidências permitidas |
| Operação | Um serviço API, um banco, frontend estático; limpeza diária; logs por ação |

## Fluxo

Upload autorizado → registro processing → gravação criptografada → extração por página → chunking → embeddings em lotes → transação de chunks e estado ready. Falha elimina arquivo e chunks não confirmados e deixa estado error explicável.

Pergunta autenticada → filtros de tenant/visibilidade/expiração/perfil → busca → seleção opcional de evidências → conferência de texto e acesso → resposta + fontes → histórico privado. “Onde está escrito isso?” resolve pelo identificador do turno anterior do próprio usuário, sem nova inferência.

Exclusão → remover histórico que cita a fonte → remover chunks/documento → commit → remover arquivo. Se houver interrupção entre commit e remoção física, cleanup remove arquivo órfão. Documentos expirados deixam de ser acessíveis antes da rotina física. Backups exigem política operacional própria.

## Provedores

| AI_PROVIDER | AI_BASE_URL | Observações |
|---|---|---|
| none | vazio | Demo textual; sem embeddings, sem IA simulada |
| ollama | endpoint privado :11434 | API /api/embed e /api/chat; configuração inicial Qwen |
| openai | endpoint compatível terminando em /v1 | /embeddings e /chat/completions; contrato e autorização antes de envio |
| azure | raiz do recurso Azure | deployments separados em EMBED_MODEL/CHAT_MODEL, versão REST configurada no adaptador |

Os adaptadores permitem substituir o provedor sem alterar interface/biblioteca. Eles não garantem compatibilidade com todos os modelos: parâmetros de geração e JSON precisam ser homologados para cada deployment. Não houve chamada paga ou envio de documentos reais nesta implementação.

**Geração livre foi deliberadamente excluída do POC.** Um LLM opcional seleciona fontes; a resposta final continua extrativa. Portanto, esta versão não promete um chat generativo completo. É uma redução consciente de escopo para testar a hipótese comercial com menos risco, documentada para não confundir demo com um RAG generativo validado.

## Segurança pragmática

tenant_id obtido da sessão, nunca da pergunta ou formulário. Visibilidade team/admin; usuários reader só consultam team. Fontes/download/histórico repetem autorização. Nenhum link assinado público. Senha scrypt; sessão armazenada por hash. Arquivos, chunks e conteúdo do histórico criptografados com Fernet; embeddings e metadados operacionais não são cifrados pela aplicação. Exigir criptografia do volume do banco no piloto.

Sem RLS nesta primeira base: filtros de aplicação são a fronteira lógica testada. Recomenda-se uma implantação e banco por cliente no primeiro piloto como contenção adicional, sem alegar isolamento físico de uma instância compartilhada. RLS deve ser avaliada se houver oferta multicliente compartilhada.

## Limites conhecidos

Não há detecção completa de contradições, revisão vigente automática, interpretação confiável de tabelas, ACL herdada de sistemas externos, fila de ingestão ou migrations de esquema. Antes da primeira alteração de esquema em dados reais, introduzir migração versionada e backup testado. create_all só cria tabelas ausentes.

O armazenamento local está encapsulado no serviço e pode ser trocado por object storage posteriormente; S3/Azure Blob não estão implementados. Priorizar somente quando houver necessidade de implantação ou recuperação que justifique a mudança.
