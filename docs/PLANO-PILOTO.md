# Piloto de Inteligência Documental — decisão e execução

Data da avaliação: 15/09/2026. Todas as estimativas comerciais abaixo são hipóteses, não preços de mercado observados, vendas realizadas ou resultados medidos.

## Antes da arquitetura: 12 perguntas que decidem a venda

| Pergunta | Avaliação crítica e evidência a obter |
|---|---|
| O problema existe? | É plausível, mas não está comprovado em um cliente. Observar cinco buscas reais com usuários, sem lhes sugerir a resposta. Não usar “temos muitos PDFs” como prova de dor. |
| Alguém pagaria? | Ainda não sabemos. Sinal válido: responsável aceitar escopo, orçamento e data de um piloto pago. Elogio à demo ou carta de intenção sem orçamento não basta. |
| Quem sofre diariamente? | Analista de qualidade, supervisor, comprador e técnico que procuram regras e interrompem colegas. Começar por uma equipe e um processo. |
| Quem tem orçamento? | Gerente de operações/qualidade ou proprietário de uma empresa menor. Confirmar centro de custo e limite de aprovação. |
| Quem aprova? | Patrocinador operacional, gestor com alçada, TI/segurança e, quando necessário, jurídico/privacidade. O usuário entusiasmado não é necessariamente comprador. |
| O que usam hoje? | Entrevistar: busca do SharePoint/Drive, pastas de rede, Teams, intranet, PDFs locais ou consulta a um colega. Medir também a melhor alternativa já contratada. |
| Copilot ou Drive resolvem? | Possivelmente. Agentes de SharePoint já respondem sobre documentos respeitando permissões. Se a ferramenta existente resolver com menor custo total, recomendar sua configuração em vez de vender software duplicado. |
| Por que confiariam os documentos? | Confiança requer ambiente acordado, demonstração de isolamento, contrato de tratamento, responsáveis identificados e exclusão comprovável. Uma interface bonita não resolve isso. |
| O que pode impedir? | Falta de homologação, saída de dados, ausência de SSO obrigatório, permissões incompatíveis, dados pessoais, software sem suporte, contrato com provedor e exigências de rede. Descobrir antes de desenvolver integrações. |
| Há ROI demonstrável? | Sim como hipótese mensurável de tempo recuperado; não equivale automaticamente a redução de folha. Comparar custo total com capacidade operacional efetivamente reaproveitada. |
| Quantas horas? | Exemplo hipotético: 12 usuários × 3 buscas/dia × 22 dias × 4 minutos economizados ÷ 60 = **52,8 h/mês**. Substituir todos os parâmetros por observação. |
| É grave o bastante? | Só avançar se frequência, atraso e custo justificarem a compra. Se são poucas consultas mensais e ninguém consegue apontar perdas, NO-GO para este produto nessa conta. |

Referência competitiva: [permissões de agentes do SharePoint](https://learn.microsoft.com/en-us/sharepoint/manage-access-agents-in-sharepoint). A Microsoft informa que fontes e respostas obedecem ao acesso do usuário. Isso torna governança e implantação parte essencial da comparação.

## 1. GO / NO-GO

**GO condicionado para vender e executar um piloto restrito. NO-GO para escalar SaaS agora.**

Portões propostos: entrevistar 5 empresas do segmento, observar ao menos 10 buscas, identificar 2 patrocinadores com orçamento e obter 1 piloto pago antes de ampliar funcionalidades. Se em 10 conversas qualificadas ninguém reconhecer custo mensurável ou aceitar discutir pagamento, mudar o problema ou oferecer organização documental/implantação de ferramenta existente.

Não há evidência disponível de que uma empresa específica de Manaus comprará. A experiência técnica do fundador pode facilitar a conversa, mas não autoriza usar documentos, contatos internos ou marcas do empregador.

## 2. Problema mais valioso

Encontrar **a regra vigente e sua origem** para uma dúvida recorrente de trabalho, sem interromper especialistas. Primeiro recorte: alçadas de compra e procedimentos da qualidade. Segurança e manutenção aparecem na demo, mas recomendações operacionais críticas exigem conferência humana. Não iniciar como ferramenta autônoma de diagnóstico, liberação de máquinas ou atendimento de emergência.

## 3. Cliente ideal

Fornecedor industrial ou empresa de engenharia/logística de Manaus com 20–150 funcionários, 5–20 usuários frequentes e 30–100 documentos digitais vigentes no processo escolhido. Critérios são hipóteses de qualificação, não estatística de mercado.

Preferir organização com gestor acessível, documentação pesquisável e pouca burocracia de compra. Evitar primeiro projeto em multinacional com homologação longa, hospitais, dados de RH sensíveis e contratos de alta criticidade. Comprador: proprietário ou gerente de operações. Campeão: qualidade. Aprovadores técnicos: TI e segurança.

## 4. Arquitetura mínima

React/Vite/Tailwind → FastAPI → PostgreSQL/pgvector. Arquivos locais criptografados; extração por página e parágrafo; embeddings desacoplados; recuperação filtrada por organização e permissão; respostas literais e histórico privado. Ollama como opção local, interfaces para provedores externos. Não há necessidade inicial de Kubernetes, microserviços ou banco vetorial separado.

A demonstração sem modelo usa busca textual/SQLite e está rotulada. O piloto semântico exige PostgreSQL e embeddings reais. [Detalhes técnicos](ARQUITETURA.md).

## 5. Backlog MVP

| Prioridade | Entrega | Situação desta base |
|---|---|---|
| P0 | Autenticação, organização e papéis admin/leitor | Implementado; testes de acesso |
| P0 | Upload, biblioteca e estado de processamento | Implementado para PDF textual/TXT |
| P0 | Extração por página, chunking e embeddings | Implementado; provedor configurável |
| P0 | Busca semântica com filtro de acesso | Implementada via pgvector; validar com corpus real |
| P0 | Resposta, documento, página, trecho e fonte | Implementado em formato extrativo |
| P0 | Recusa sem evidência e distinção de falha técnica | Implementado; calibrar recuperação em português |
| P0 | Histórico privado, exclusão e expiração | Implementado; rotina de limpeza precisa ser agendada |
| P0 | Logs básicos sem conteúdo documental | Implementado; revisar operação/retention com TI |
| P0 comercial | Benchmark de tempo, proposta e fechamento | Preparados como protocolo; ainda não executados |
| P0 piloto | Aprovação TI, contrato, TLS, backup e teste de modelo | Pendentes no ambiente do cliente |

## 6. Critérios de aceite

Critérios propostos para negociar antes do piloto, não resultados alcançados:

- Demo: login → pergunta → evidência aberta em menos de 2 minutos, com ambiente já preparado.
- Respostas exibidas devem conter apenas trechos existentes em documentos acessíveis; documento e página conferidos manualmente.
- Acesso cruzado entre organizações, leitura de arquivo restrito, histórico alheio e reutilização de fonte excluída devem falhar em todos os testes.
- Upload inválido deve explicar a falha; indisponibilidade do provedor não pode ser chamada de “informação não encontrada”.
- Avaliação com 50 perguntas novas: 30 respondíveis, 10 sem resposta e 10 com ambiguidade, limites ou instruções maliciosas. Meta inicial: encontrar a fonte correta no top 5 em ≥90% das respondíveis, ≥90% de recusa nas sem resposta e nenhum vazamento na amostra. Uma amostra sem falha não prova segurança universal.
- Medir tempo total **até o usuário confirmar a fonte correta**, não somente tempo do servidor.
- Sucesso comercial sugerido: redução ≥50% da mediana de tempo, sem piorar a taxa de acerto, adesão de pelo menos 5 usuários e intenção de renovação com preço definido. Se só ficar rápido porque responde errado, reprovar.

O ponto de corte vetorial é parâmetro experimental. Similaridade não é probabilidade de verdade. Não vender uma garantia absoluta de que o sistema não erra.

## 7. Demonstração em 120 segundos

| Tempo | Ação |
|---|---|
| 0–15 s | Mostrar o aviso de dados fictícios e explicar a tarefa: encontrar informação com fonte. |
| 15–40 s | “Quem aprova compras superiores a R$ 10.000?” Mostrar gerente + diretor financeiro e abrir PC-002, página 2. |
| 40–60 s | “Qual procedimento deve ser realizado em caso de acidente?” Mostrar trecho fictício de PS-003, página 2; não executar instruções reais. |
| 60–80 s | “Qual é a periodicidade da manutenção preventiva?” Mostrar 30 dias, com escopo explícito TR-01. |
| 80–95 s | “E onde está escrito isso?” Reexibir a evidência anterior e abrir a página. |
| 95–110 s | Perguntar sobre reembolso de passagens: mostrar recusa. |
| 110–120 s | Perguntar: “Quanto tempo sua equipe levaria hoje para encontrar e conferir isso?” Convidar para diagnóstico com corpus autorizado. |

Não apresentar tempo da demo textual como benchmark de inferência local. Não demonstrar apenas perguntas memorizadas: deixar o cliente propor questões dentro do escopo e registrar falhas.

## 8. Estratégia comercial

**Oferta:** Piloto de Inteligência Documental, 30 dias, uma área, até 50 documentos textuais, até 10 usuários, preparação da base, configuração, uma sessão de treinamento e relatório antes/depois. Vender: “Encontre em segundos informações que hoje estão espalhadas em procedimentos, manuais e documentos internos.”

**Preço para testar:** R$ 3.500 pelo piloto, 50% na contratação e 50% na entrega do relatório acordado. Renovação hipotética a partir de R$ 900/mês, sujeita a volume e suporte. Hardware, licenças existentes, OCR em massa e integrações não incluídos. Não é cotação de mercado nem recomendação de assumir obrigações sem apurar custos.

**Conta crítica:** no cenário de 52,8 horas, a R$ 35/h de custo carregado, capacidade bruta recuperada = R$ 1.848/mês. Se apenas 50% vira trabalho útil adicional, benefício efetivo = R$ 924/mês: uma mensalidade de R$ 900 deixa quase nenhum ganho antes de infraestrutura. Essa conta **não justifica** a compra nessa configuração. É necessário demonstrar maior frequência, impacto de atrasos ou menor custo de entrega; não maquiar ROI.

Fórmula: benefício efetivo = usuários × buscas/dia × dias/mês × minutos economizados ÷ 60 × custo/hora × fator de aproveitamento. Benefício líquido = benefício efetivo − mensalidade − infraestrutura − administração interna. Payback = implantação ÷ benefício líquido, apenas quando positivo. Não somar ganho de tempo e redução de pessoal como se fossem benefícios independentes.

**Aquisição:** selecionar 20 fornecedores industriais/engenharias locais por contatos autorizados, associações empresariais e listas públicas; priorizar 5 reuniões por indicação. Abordagem individual: “Estou validando uma forma de reduzir o tempo gasto procurando regras em procedimentos. Podemos observar três buscas que sua equipe faz hoje? Se houver perda relevante, proponho um piloto de 30 dias com medição antes e depois.” Nenhuma mensagem foi enviada nesta tarefa.

**Objeções:** “Já temos Copilot” → comparar com a solução contratada; “dados não podem sair” → desenho local aprovado e sem saída de rede; “IA inventa” → evidências e avaliação de erros, sem promessa absoluta; “não temos orçamento” → quantificar a perda ou encerrar; “e se você sair?” → exportação, documentação, backup, suporte definido e possibilidade de entrega on-premise.

## 9. Principais riscos

Vazamento por erro de permissão; documentos obsoletos; falsa confiança em citação verdadeira mas irrelevante; inferência lenta em CPU; PDFs sem texto; suporte consumir a margem; retenção de cópias/backup; homologação de TI longa. [Controles e limites](SECURITY.md).

## 10. Plano de execução de 7 dias

| Dia | Resultado necessário |
|---|---|
| 1 | Cinco convites qualificados; duas conversas; mapear usuário, comprador e alternativa atual. |
| 2 | Observar buscas e apurar custo; selecionar um processo, sem receber documentos sem autorização. |
| 3 | Preparar demo e avaliação de 50 perguntas; comparar busca textual com embeddings locais. |
| 4 | Testar permissões, fontes, recusas e hardware; documentar limitações e orçamento de operação. |
| 5 | Demonstrar para dois potenciais compradores e apresentar escopo fechado do piloto. |
| 6 | Ajustar proposta; obter patrocinador, TI e condições de tratamento/retention. Não prometer SSO ou conectores inexistentes. |
| 7 | Buscar contratação e agendar baseline. Se não houver compromisso, registrar motivos e ajustar segmento/problema. |

Sete dias são plano de prospecção e preparação, não promessa de homologação ou venda concluída.

## 11. Não implementar agora

Marketplace, cobrança automática, gestão multirregional, aplicativo móvel, dashboards decorativos, agentes autônomos, fine-tuning, voz, WhatsApp, integração ERP, OCR complexo, conectores de todas as nuvens, aprovação automática de compras, liberação automática de máquinas e suporte irrestrito a formatos. SSO e ACL avançada só quando forem condição explícita de uma oportunidade comercial economicamente viável.

## 12. Cinco razões para fracassar

1. **Dor fraca:** pouca frequência e nenhuma perda financeira identificável.
2. **Alternativa suficiente:** SharePoint/Copilot ou simples organização de pastas resolvem por menos.
3. **Confiança insuficiente:** permissões, contratos, segurança e manutenção não passam pela TI.
4. **Qualidade documental ruim:** escaneados, revisões conflitantes e contexto ausente tornam as respostas inúteis.
5. **Economia de entrega ruim:** instalação, hardware, correções e atendimento custam mais do que o contrato paga.

O negócio pode fazer sentido como serviço de implantação com escopo estreito, mesmo se não fizer sentido como SaaS independente. O primeiro contrato e os resultados do piloto devem decidir essa evolução.
