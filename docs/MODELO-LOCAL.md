# Um modelo open source básico é viável?

**Sim para recuperar e apresentar evidências em um piloto delimitado. Ainda não há validação de qualidade deste projeto com inferência real.** Minha escolha inicial é embeddings locais pequenos e resposta extrativa, com gerador opcional. O objetivo é resolver a consulta com baixo custo e rastreabilidade, não demonstrar um chatbot sofisticado.

## Escolha e motivação

| Componente | Proposta | Avaliação crítica |
|---|---|---|
| Embeddings | Qwen3-Embedding 0.6B, via Ollama | 0,6 bilhão de parâmetros, multilíngue, licença Apache 2.0 e saída até 1024 dimensões. É um candidato plausível a busca em português; os benchmarks públicos não comprovam precisão nos documentos de um cliente. |
| Resposta inicial | Texto literal dos trechos recuperados | Dispensa gerador, reduz latência e impede criação de frases pelo LLM. Ainda pode selecionar evidência errada, incompleta ou obsoleta. |
| Seletor opcional | Qwen3 4B via Ollama | Usar apenas para escolher trechos recebidos. Precisa superar o baseline em teste cego; se só adicionar atraso ou instabilidade, remover. |
| Gerador de 0,6B | Não adotar como padrão | A leveza não demonstra competência para regras com exceções, negações e diferentes alçadas. Não há benchmark deste domínio que autorize confiar nele. |

Fontes primárias: [Qwen3-Embedding 0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B), [Qwen3 4B](https://huggingface.co/Qwen/Qwen3-4B), [modelo no Ollama](https://ollama.com/library/qwen3-embedding:0.6b), [API de embeddings](https://docs.ollama.com/api/embed). Consultadas em 15/09/2026. Não são alegações de que sejam os modelos mais recentes ou melhores em todos os cenários.

## Hardware e custo

Um embedding de 0,6B pode ser experimentado em CPU, mas velocidade depende de processador, memória, tamanho dos lotes e concorrência. Estimativa apenas dos pesos: 0,6 bilhão × 2 bytes ≈ 1,2 GB em FP16, **sem** runtime e ativações. A quantização reduz pesos, mas pode alterar resultados. Não equiparar tamanho do download ao consumo total de memória.

Para um gerador de 4B em 4 bits, o limite aritmético dos pesos é cerca de 2 GB; consumo real é maior e inclui cache de contexto, buffers e serviço de embeddings. Começar com contexto curto e 1–3 consultas simultâneas, medir antes de prometer SLA. Não há necessidade demonstrada de comprar GPU antes de vender o piloto.

“Sem custo por token” não significa gratuito: energia, máquina, atualização, monitoramento e suporte continuam existindo. Se cada cliente exigir hardware e suporte personalizados, a margem pode ser inferior à de uma API aprovada ou de uma implantação de ferramenta já contratada.

## Como a implementação usa o modelo

1. Extrai somente texto por página, em parágrafos e janelas de até 1200 caracteres.
2. Calcula embeddings em lotes de 16 e grava o perfil do modelo.
3. Consulta pgvector com organização e papel filtrados antes dos resultados.
4. Recupera até 5 trechos acima de limiar experimental.
5. Sem gerador, mostra trechos literais. Com seletor, só aceita evidência devolvida que exista na lista permitida e no texto recuperado.
6. Reconfere acesso antes de responder e antes de abrir fonte.

O Qwen de embeddings recebe instrução curta em inglês na consulta, conforme orientação do autor; os documentos permanecem no idioma original. Trocar modelo exige reindexação. O projeto não baixa pesos automaticamente nem usa documentos para treinar.

## Aprovação baseada em teste, não no nome do modelo

Separar perguntas de calibração das perguntas de avaliação. O conjunto deve conter sinônimos, erros comuns de digitação, siglas, exceções, valores de fronteira, equipamentos diferentes, perguntas sem resposta e documentos com instruções maliciosas. Testar compra de **exatamente** R$ 10.000 versus acima desse valor, manutenção do TR-01 versus equipamento ausente e fontes com revisões divergentes.

Comparar: busca textual → embeddings 0,6B extrativos → embeddings + seletor 4B. Medir fonte correta no top 5, correção avaliada pelo dono do procedimento, recusas corretas, falsos positivos e tempo até a fonte correta ser conferida. Propor P95 de resposta até 10 segundos com 3 usuários simultâneos como meta a negociar, não desempenho já alcançado.

Se os embeddings simples resolverem, ficar com eles. Se o seletor pequeno errar, não adicionar mais prompts indefinidamente: melhorar corpus/chunking, reduzir escopo, testar modelo maior ou abandonar a geração. Segurança depende também da aplicação e da implantação; modelo local não corrige vazamento entre organizações.
