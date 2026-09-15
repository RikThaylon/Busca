# Registro de validação — 15/09/2026

## Executado nesta implementação

- Backend com SQLite: **11 testes passaram; 1 teste exclusivo de PostgreSQL/pgvector foi pulado**, pois o ambiente local não dispõe desse serviço.
- Frontend: compilação de produção Vite concluída.
- Corpus: cinco documentos fictícios processados e prontos para consulta.
- Casos backend: três perguntas da demo com página 2 verificável; repetição da evidência; perguntas sem resposta; isolamento entre duas organizações; RBAC e documento restrito; revogação por exclusão e expiração; histórico privado; criptografia dos textos; login/logout/origem/rate limit; PDF falso e extensão não permitida; falha de provedor distinta de ausência de evidência; rejeição de texto inventado e recorte de qualificadores pelo seletor.

## Testes de interface

Dois testes automatizados em DOM simulado verificam consulta → fonte/página → continuação e ausência de evidência sem fonte inventada. Eles não medem layout, contraste, interação em navegador real ou tempo de uso humano.

## Não validado aqui

- **Inspeção visual desktop/mobile:** o navegador conectado bloqueou `http://localhost:5173` com `ERR_BLOCKED_BY_CLIENT`. Não houve captura visual aprovada.
- **Inferência real:** nenhum modelo Ollama foi baixado/executado nesta sessão; nenhuma API externa foi chamada. Precisão em português, latência, consumo de RAM/VRAM e concorrência permanecem sem medição.
- **Integração PostgreSQL local:** workflow preparado com serviço pgvector. O teste usa embeddings controlados e não substitui teste de qualidade com modelo real.
- **Implantação:** Docker, TLS, restauração de backup, firewall, antimalware e homologação do cliente não foram executados neste ambiente.
- **Resultados comerciais:** nenhum cliente entrevistado, mensagem enviada, contrato fechado ou ROI real medido nesta tarefa.

## Avaliação necessária antes do piloto

Usar o conjunto de 50 perguntas e os critérios do plano comercial; medir tempo até a fonte ser confirmada; testar casos de fronteira, equipamento ausente e versões conflitantes. Em interface, verificar 1440×900 e 375×812, teclado/foco dos diálogos, zoom de 200%, ausência de rolagem horizontal e legibilidade. Aprovar a implantação com o responsável de TI. Não confundir presença de testes no repositório com execução bem-sucedida do CI: consultar o resultado associado ao commit.
