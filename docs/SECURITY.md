# Segurança, privacidade e limites de uso

Esta base é um MVP avaliado com dados fictícios, não um produto certificado ou homologado para qualquer empresa. O guia da ANPD orienta controles proporcionais, gestão de acesso e medidas administrativas; conformidade depende também do tratamento e da operação. [Guia oficial da ANPD](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-sobre-seguranca-da-informacao-para-agentes-de-tratamento-de-pequeno-porte).

## Implementado

- Sessões aleatórias, hash no banco, expiração de 8 horas, cookies HttpOnly/SameSite e Secure obrigatório no modo piloto.
- Verificação de Origin nas mutações, origem CORS específica e limitação de tentativas de login/consulta/upload no banco.
- Senhas com scrypt e salt; sem cadastro público. Provisão por administrador via CLI.
- Separação por organização, RBAC admin/reader e visibilidade de documento team/admin.
- Arquivos criptografados, nomes/chunks/histórico criptografados; chave externa obrigatória no piloto. Em demo, chave local com permissão 0600.
- Fontes e downloads autenticados; HTML de documentos não é executado; React renderiza trechos como texto, sem dangerouslySetInnerHTML.
- PDF/TXT com limite de tamanho, páginas e texto extraído. PDFs com ações ativas de catálogo são recusados. Processo extrator com timeout, CPU e memória limitados.
- LLM sem ferramentas, sem acesso ao banco, sem URLs executáveis e contexto composto exclusivamente de fontes previamente autorizadas. Saída textual livre não é mostrada.
- Histórico revalida fontes e pertence apenas ao usuário. Exclusão apaga chunks e conversas relacionadas; expiração bloqueia a leitura e cleanup remove dados físicos.
- Auditoria de login, consulta, fonte, download, processamento e exclusão sem corpo dos documentos/perguntas em logs operacionais.

## O que esses controles NÃO provam

Criptografia em aplicação não protege contra comprometimento do processo que possui a chave. Embeddings podem revelar características do conteúdo e não são anonimizados. O modelo pode selecionar trecho irrelevante. Prompt de sistema e citação não eliminam prompt injection. Um PDF pode explorar vulnerabilidade do parser: processo separado e limites não constituem sandbox de segurança completo nem substituem antimalware. Logs são básicos, não imutáveis nem resistentes a um administrador do banco.

O piloto aceita somente uploads de administradores e deve começar com documentos revisados e não altamente sensíveis. Não abrir upload público. Atualizar parser/dependências e executar varredura de segurança conforme requisitos do cliente. Não enviar PDFs suspeitos ao visualizador nativo automaticamente: o aplicativo exibe texto extraído e oferece download explícito.

## Implantação antes de dados reais

1. Definir cliente/controlador e fornecedor/operador conforme o tratamento efetivo, finalidade, base legal aplicável, pessoas autorizadas, contrato, contato de incidentes e descarte. Não assumir que consentimento é a base correta para toda documentação empresarial.
2. Minimizar dados pessoais. Excluir RH, saúde, biometria, segredos desnecessários e contratos críticos do piloto inicial.
3. Usar APP_MODE=pilot em instalação separada da demo, credenciais nominativas e chave mantida em segredo fora do banco e do repositório.
4. Configurar TLS no proxy aprovado; manter banco/API/Ollama em rede privada; restringir egress aos destinos explicitamente aprovados. O aplicativo não altera firewall.
5. Criptografar volumes e backups, controlar acesso ao host e testar restauração. Proteger e guardar a chave separadamente: sem ela não existe recuperação dos textos.
6. Configurar backup com retenção máxima definida (exemplo negociável: 7 dias). Exclusão no banco ativo não apaga magicamente backups existentes. Na restauração, reaplicar expiração/exclusões conforme registro operacional.
7. Agendar cleanup diariamente e monitorar sua saída. Conferir processamento interrompido, arquivos órfãos, falhas de serviço e alertas de capacidade.
8. Se usar API externa, aprovar região, subprocessadores, retenção, finalidade e termos de não treinamento; EXTERNAL_AI_APPROVED é um bloqueio de configuração, não prova contratual. O mesmo cuidado vale para embeddings, que também recebem texto.
9. Rodar os testes de acesso e a avaliação de respostas no ambiente de implantação. Homologar o modelo e ajustar o limiar com dados autorizados.
10. Definir suporte, janela de atendimento, limite de documentos e processo de incidentes. Não prometer disponibilidade enterprise com operação individual.

## Retenção

Padrão experimental: 30 dias para documentos, histórico e auditoria. Validade inicia no upload; a aplicação exibe a retenção. Sessões expiram em 8 horas. A retenção contratada precisa ser acordada com o cliente, inclusive obrigações de auditoria que exijam prazos diferentes. Documentos expirados nunca participam de busca ou abertura, mesmo se o job não rodar. O administrador pode excluir antes do prazo. Histórico pode ser apagado pelo próprio usuário.

## Limites de acesso

Dois níveis de visibilidade são deliberadamente simples. Não incluir no mesmo grupo documentos que exijam segregação mais fina. Esta versão não importa permissões do SharePoint/Drive, não implementa SSO/MFA e não possui tela de gestão de contas. Se esses requisitos forem obrigatórios, são bloqueadores reais do piloto até implementação aprovada, não itens a esconder na proposta.

Relatos de vulnerabilidade: comunicar de forma privada ao mantenedor, sem publicar documentos, chaves ou dados de clientes em issues públicas.
