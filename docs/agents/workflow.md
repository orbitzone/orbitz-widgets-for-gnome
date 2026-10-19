# Fluxo vigente — economia de contexto e revisão por risco

Atualizado em 19/10/2026 por pedido do usuário. Prevalece sobre rotinas anteriores de auditoria/UX por tarefa. Equipe e canais: [team.md](team.md).

## Execução e comunicação

- Supervisor lê o contexto atual, delimita objetivo, critérios, risco e arquivos; aciona somente os especialistas necessários. Tarefa pequena pode ser executada diretamente dentro da propriedade combinada, sem criar agentes ou ritos adicionais.
- Brief curto: objetivo, arquivos, contrato, aceite e verificações. Referenciar documentação existente em vez de reenviar o histórico. Especialistas leem só os trechos necessários e investigam autonomamente no escopo.
- Comunicação por mudança de contrato, bloqueio real, achado crítico ou entrega final. Evitar mensagens de ciência, repetição de status e repasses idênticos a toda a equipe. Backend/frontend podem alinhar APIs diretamente.
- Aguardar conclusão por eventos/cursor; não repetir consultas sem mudança, nem fazer leituras completas de chats para acompanhar progresso. Um relatório compartilhado basta; não copiar seu conteúdo inteiro para mensagens e vários documentos.
- Relatório normal: até cerca de 150 palavras com arquivos, resultado, verificações e pendências; ampliar somente para reproduzir achado relevante. Um relatório consolidado por sprint; pequenas tarefas ficam na fila, sem arquivo de auditoria por incremento.

## Testes e auditoria

Desenvolvedor continua responsável por testes proporcionais da própria mudança. Isso não é uma auditoria independente e não deve ser adiado até o sprint terminar.

| Risco | Durante a tarefa | Auditor independente |
|---|---|---|
| Baixo: documentação, rótulos, espaçamento sem mudança de dados | Revisão local e verificações pertinentes; sem testes artificiais | Somente se aparecer evidência de problema; não é gate para teste local |
| Médio: interface/fluxo e lógica sem os efeitos de alto risco abaixo | Testes afetados + smoke de integração; registrar pendência na fila | Uma rodada consolidada no fechamento da sprint, antes de publicar o lote |
| Alto: exclusão/gravação sensível, migração/backup/instalador, credenciais/autenticação, execução de comandos, regras monetárias ou confiança de assinaturas | Testes direcionados e evidências antes da aplicação | Revisão focada antes de aplicar a operação afetada; fechamento reutiliza essa evidência se o alvo não mudou |

- Classificar pelo efeito real, não só pelo nome do arquivo. Dúvida relevante mantém a mudança na categoria mais cautelosa até esclarecimento técnico; não inventar risco crítico sem evidência.
- Sprint é lote lógico de tarefas relacionadas, sem calendário ou automação. Supervisor mantém [fila](../sprint-backlog.md), propõe agrupamento e fecha com o usuário quando o lote estiver pronto; pedido de release/publicação também exige fechar a fila pertinente.
- Não acionar auditor ao iniciar toda tarefa. Enviar um único alvo estável no fechamento ou um pedido focado quando houver gatilho de alto risco.
- Auditor usa testes já documentados como evidência, faz verificação independente dos riscos relevantes e executa integração uma vez no fechamento. Não repetir a mesma suíte em todos os papéis sem mudança/falha que justifique.
- Correção de achado: repetir cenário e testes afetados; nova execução ampla só quando a correção afetar integração ou existir incerteza concreta. Achado que ameaça dados/segredos impede a operação afetada, sem bloquear trabalho independente seguro.
- Registrar separadamente implementação, testes locais, auditoria pendente/concluída, teste visual e instalação. Mudança média pode ser disponibilizada para teste local com pendências explícitas; isso não autoriza publicar um lote ainda sem a revisão necessária.

## Design/UX sob demanda

- Frontend aplica padrões existentes e faz a revisão básica de layout, teclado, foco e estados. Não chamar UX automaticamente a cada tarefa.
- Acionar UX somente para redesign solicitado, decisão visual/experiência realmente ambígua ou defeito com evidência. Canal exclusivo frontend↔UX preservado.
- Uma revisão focada por lote quando acionado, até três achados priorizados por impacto. Não pedir nova rodada para cada correção pequena nem relatórios extensos de hipóteses.
- Sem captura/execução permitida, UX pode esclarecer uma questão estática delimitada; não produzir inventário genérico nem alegar aprovação visual. Pendências de pixels/AT ficam registradas sem repetir tentativas gráficas bloqueadas.

## Fechamento e limites

Supervisor atualiza apenas documentos afetados e mantém o contexto atual curto; histórico fica em relatórios/arquivo, carregado só quando necessário. Não exigir atualizar todos os documentos em toda tarefa.

A resposta final informa conclusão, evidências/limites e instalação. Em entrega de código: comando completo do atualizador, resultado esperado, reabertura/reinício e teste curto. Documentação somente dispensa atualização/reinício. Não emitir respostas vazias ou reabrir tarefa apenas para confirmar relatório interno tardio sem mudança material.

Preservar dados, licenças, propriedade de arquivos e autorização de instalação/publicação. Nenhum agente monitora continuamente. Esta política não muda modelo/plano nem promete percentual de economia; reduzir frequência, contexto e repetição é o mecanismo adotado.
