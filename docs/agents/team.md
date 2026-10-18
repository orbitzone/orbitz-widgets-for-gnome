# Equipe e fluxo de trabalho

Autorização do usuário: 18/10/2026. Este chat é o supervisor de requisitos/documentação. Há quatro chats dedicados: backend, frontend, auditor de segurança/desempenho/DevOps e Design/UX. IDs dos chats:

- Supervisor: `01a14cdf-dbce-7990-a8db-a482e49b4975`.
- Auditor: `01a14cfd-f9ef-7ac3-a8ed-d5f7d9a31e66`.
- Backend: `01a14cfe-1021-73b2-b031-b1ae67f7687e`.
- Frontend: `01a14cfe-1f6d-7733-b2b8-cac3d8275670`.
- Design/UX: `01a14d0f-088b-7cc2-a4c3-f34f483c21a1`.

## Fluxo

1. Supervisor delimita entrega, critérios e propriedade exclusiva dos arquivos.
2. Backend e frontend trabalham simultaneamente em áreas distintas; alinham interfaces diretamente quando necessário e reportam ao supervisor. Nenhum altera arquivo reservado ao outro sem transferência explícita.
3. Desenvolvedores reportam alterações e testes ao supervisor; supervisor avalia integração e atualiza documentação como parte da entrega. Achados críticos podem ser tratados diretamente com o responsável, mantendo o supervisor informado conforme as regras abaixo.
4. Supervisor encaminha estado estável ao auditor. Achados voltam ao supervisor e são distribuídos aos responsáveis; repetir verificações afetadas até concluir ou registrar bloqueio real.

A comunicação foi explicitamente autorizada pelo usuário, inclusive respostas dos agentes ao supervisor. As mensagens podem iniciar novas execuções; não estabelecem serviço permanente. Nenhuma automação foi solicitada. Chats compartilham checkout: não fazer commits concorrentes, sobrescrever alterações nem executar testes globais durante mutações sem coordenação.

## Primeira tarefa: RF-01 — revisão estrutural de todo código próprio

Estado: confirmado. Objetivo: revisar todos os arquivos próprios e refatorar os que se beneficiam de separação de responsabilidades, com código limpo e rastreável. Arquivos já coesos podem permanecer iguais com justificativa; não reescrever dependências, imagens, binários, traduções ou licenças.

Critérios: inventário por arquivo/componente com decisão manter/refatorar e justificativa; interfaces e comportamento preservados; módulos com responsabilidades claras; ausência de importações quebradas/ciclos; testes relevantes e suíte integrada registrados; falhas históricas separadas de regressões; revisão independente de segurança e desempenho. Testes JS historicamente falhos devem ser diagnosticados, nunca desativados. Ganhos de desempenho exigem medição; modularidade por si só não prova ganho.

Primeiro registrar baseline estável com auditor; depois liberar backend/frontend simultaneamente. Desenvolvedores podem inspecionar e planejar enquanto aguardam liberação. Supervisor integra resultados e solicita auditoria final. Sem deploy, instalação ativa, commit ou push nesta tarefa.

## Estado da execução inicial

Baseline do auditor concluída em 18/10/2026: 44/44 testes Python aprovados, 12/15 arquivos de teste JS aprovados e sintaxe de 78 arquivos conferida (`docs/audits/2026-10-18-baseline.md`). Supervisor enviou liberação de implementação a backend/frontend. Na última consulta, ambos estavam com status da ferramenta `waitingOnApproval`; a operação pendente não foi identificada pelo retorno. Refatoração e auditoria final ainda não estão concluídas. Não interpretar mensagem de liberação como prova de execução.

## Contexto e pesquisa centralizados (18/10/2026)

Por instrução do usuário, o analista mantém o contexto persistente em `docs/project-context.md` e centraliza descoberta ampla, pesquisas externas e análise de impacto. Envia resumo de tarefa com referências, contratos, propriedade de arquivos e testes aos especialistas. Backend/frontend solicitam ao supervisor informação que faltar em vez de repetir pesquisa ampla.

Leitura local necessária à alteração, investigação de falhas dos próprios testes e verificação independente do auditor continuam necessárias: o resumo não substitui conferir o código atual. Auditor comunica lacunas ao supervisor e pode inspecionar evidências e código pertinente para fundamentar achados. Pesquisa externa ampla continua com o supervisor, que identifica fontes, data e incertezas. Não prometer conhecimento integral infalível ou atualização sem execução: documentação é atualizada durante trabalho acionado e recebimento de entregas.

## Design/UX e práticas confirmadas (18/10/2026)

O usuário aprovou as recomendações do supervisor: entregas pequenas por componente; contratos de entradas/saídas/erros antes de mudanças compartilhadas; propriedade exclusiva dos arquivos; conclusão acompanhada de código, testes, documentação e auditoria; alegações de desempenho sustentadas por comparação medida.

Design/UX comunica-se exclusivamente com frontend. Frontend reporta diretamente ao UX para revisão visual/interação e mantém os relatórios de código e decisões ao supervisor. Backend/frontend mantêm o alinhamento técnico já autorizado; UX não substitui supervisão de requisitos nem auditoria independente. Frontend encaminha necessidades de pesquisa e mudanças de escopo ao analista.

Fluxo de UI: supervisor fornece escopo → frontend e UX alinham padrões/aceite → frontend implementa em pequenas entregas → UX revisa evidências → frontend reporta ao supervisor → supervisor atualiza documentação e encaminha ao auditor. Revisão visual pendente deve constar explicitamente quando houver apenas análise estática. Refatoração RF-01 preserva comportamento/aparência; melhorias de UX que os alterem são registradas separadamente para avaliação de escopo.

Propriedade: UX escreve somente em `docs/design/`; frontend escreve código da sua área; supervisor mantém documentação de produto. Não há transferência implícita de arquivos. Não há novos agentes além dos explicitamente solicitados.

## Autonomia, colaboração e conclusão — regras vigentes

Confirmadas pelo usuário em 18/10/2026. Esta seção esclarece as regras anteriores e prevalece em caso de conflito de coordenação; preserva os limites de instalação ativa, dados, publicação e propriedade dos arquivos.

### Autonomia sem gargalos

O supervisor fornece objetivo, critérios, contexto suficiente e dependências. Cada especialista escolhe a implementação dentro da sua área e escopo, lê o código necessário, investiga falhas e executa verificações pertinentes sem pedir aprovação de cada passo. O analista centraliza pesquisa ampla, mas isso não impede investigação técnica necessária: se aguardar informação bloquear a tarefa ou comprometer segurança/correção, o especialista pode consultar fontes primárias pertinentes e registrar fonte, data, motivo e conclusão para o analista. Não repetir pesquisas disponíveis e atuais.

Não esperar o supervisor para uma correção local, reversível e já abrangida pela tarefa. Mudança de requisito, contrato público incompatível, migração de dados, transferência de arquivo ou conflito entre decisões exige alinhamento com os responsáveis; continuar trabalho independente enquanto a decisão estiver pendente. Silêncio não equivale a aprovação. Dúvidas de produto/escopo chegam ao usuário pelo supervisor quando necessárias.

### Responsabilidades e comunicação

| Papel | Decide/executa | Entrega aos demais |
|---|---|---|
| Analista/supervisor | Contexto, decomposição, critérios, integração e documentação; usuário mantém decisão de escopo/prioridade de produto. | Resumo de tarefa e registro atualizado de decisões, evidências e pendências. |
| Backend | Domínio, persistência, coletores e integrações; preserva contratos/dados. | Código e testes da área; formatos, erros e compatibilidade alinhados com frontend. |
| Frontend | Componentes e implementação da interface, integração e viabilidade técnica. | Código/testes; evidências ao UX e conclusões ao supervisor; contratos alinhados com backend. |
| Design/UX | Padrões visuais, experiência e critérios de revisão, considerando plataforma e acessibilidade. | Achados e revisão ao frontend; não implementa código nem decide sozinho escopo de produto. |
| Auditor | Métodos e conclusões independentes de segurança, integridade e desempenho. | Achados com gravidade, reprodução, evidência, cobertura/limites e resultado da nova verificação. Não implementa correções de desenvolvimento. |

Supervisor↔backend/frontend/auditor e backend↔frontend permanecem autorizados. Para achados críticos ou esclarecimentos indispensáveis à verificação, auditor↔backend/frontend também está autorizado pelo pedido de colaboração e independência; registrar conclusões ao supervisor, sem aguardar repasse para interromper uma operação insegura. A comunicação exclusiva UX↔frontend permanece: frontend transmite achados urgentes de UX ao responsável/supervisor. Não ampliar essa rede a outros chats nem criar agentes adicionais.

Frontend resolve viabilidade técnica em conjunto com UX; UX define os critérios de experiência da tarefa, sem impor solução técnica fora do escopo. Divergência que afete comportamento/aceite é registrada e encaminhada ao supervisor. Não exigir revisão estética para alterações sem impacto visual, nem afirmar aprovação visual por teste de lógica.

### Trabalho em pequenas entregas

Dividir por comportamento/componente verificável; iniciar apenas o necessário para concluir a próxima entrega independente. Paralelismo deve respeitar dependências e propriedade exclusiva dos arquivos. Backend/frontend alinham entradas, saídas, erros e compatibilidade antes de alterar interfaces compartilhadas. Transferência de propriedade precisa ser explícita e registrada; não editar simultaneamente o mesmo arquivo.

Reportar marcos, bloqueios, mudanças de contrato e conclusão, evitando mensagens repetidas sem informação nova. Relatório mínimo: tarefa/requisito, o que mudou, arquivos e contratos afetados, verificações com resultado, limitações, pendências e próximo responsável. Se mensagens estiverem impedidas por permissões da ferramenta, registrar no relatório compartilhado e declarar o bloqueio; não presumir entrega da mensagem. Autonomia de papel não contorna permissões da plataforma.

### Criticidade e auditoria

Distinguir defeito reproduzido, risco inferido e melhoria opcional. Uma operação com risco concreto de perda/corrupção de dados, exposição de credenciais, execução indevida ou regressão impeditiva deve ser interrompida na área afetada, preservando evidências e trabalho independente seguro. Auditor comunica prontamente ao responsável e supervisor; desenvolvedor corrige e auditor verifica novamente. Não elevar hipótese sem evidência a vulnerabilidade confirmada.

Achados que impedem satisfazer critérios ou tornam a entrega insegura impedem sua conclusão. Melhorias opcionais seguem ao backlog com impacto e prioridade sugerida, sem bloquear tarefas não afetadas. Auditor pode avaliar pequenas entregas estáveis antes do fim de toda a RF-01; mudanças posteriores no alvo exigem verificar novamente o que foi afetado. Desempenho só é alegado com comparação reproduzível e ambiente identificado.

### Definição de conclusão

Uma entrega só fica concluída quando critérios de aceite estão atendidos; verificações proporcionais passaram; documentação afetada está atualizada pelo supervisor; achados impeditivos foram resolvidos e verificados novamente; pendências e limites estão explícitos. Registrar separadamente: validação funcional, visual e segurança/integridade/desempenho, com evidência ou indicação justificada de não aplicável. Uma aprovação não substitui as outras. Se faltar uma validação exigida, manter implementado sem validação ou pendência específica; não chamar de concluído por mera entrega de código.

Essas regras descrevem a execução quando acionada. Não criam monitoramento contínuo, notificações periódicas, deploy automático ou autorização de acesso a dados reais.

## Estado consolidado RF-01 — auditoria recebida em 18/10/2026

Backend/frontend estáveis, inventários e documentação integrados. Auditoria independente concluída em `docs/audits/2026-10-18-integrated-audit.md`: 62/62 testes Python, 16/16 arquivos JS, 102 sintaxes, imports e comparações aprovados no escopo local; nenhum achado impeditivo reproduzido. Aceite parcial do supervisor: funcional local/estrutural e revisão delimitada de segurança/integridade sustentados pelas evidências. RF-01 permanece implementada com validação visual/interativa pendente, não concluída integralmente. Frontend/UX são responsáveis por evidências em ambiente isolado permitido; não repetir tentativas bloqueadas nem usar sessão ativa sem nova condição/autorização. Desempenho não medido. Baseline JS corrigida por errata: 11/14 aprovados, três falhas.

## Comunicação obrigatória de prontidão para teste

O supervisor é responsável por informar, ao término de cada atualização, se está pronta para teste e se o usuário deve reiniciar a sessão. Desenvolvedores reportam componentes afetados, necessidade de instalação/reabertura/reinício e roteiro de teste; auditor reporta evidências e impedimentos; frontend leva critérios visuais do UX ao supervisor. Supervisor confirma aplicação e versão instalada antes de liberar reinício manual. Atualização não aplicada ou parcialmente recuperada nunca é anunciada como pronta. Não reiniciar sessão automaticamente, nem exigir logout quando basta reabrir o componente. Esta regra foi solicitada explicitamente pelo usuário em 18/10/2026.

## ID-01 — propriedade temporária dos arquivos

Para a identidade própria solicitada em 18/10/2026: frontend possui `extension/metadata.json`, UI About/rótulos/logs, novo schema Orbitz (legado preservado) e testes JS pertinentes; backend possui `tools/update-local.py`, novo `tools/migrate-identity.py` e testes operacionais. Supervisor possui README/stack, créditos e documentação de produto; UX atua via frontend e escreve docs/design; auditor verifica alvo estável e escreve relatórios. Ninguém aplica instalação/ativa/desativa GNOME nesta etapa. Preparação e ativação manual serão separadas; nunca manter duas identidades ativas. Créditos/licenças antigos não são removidos.
