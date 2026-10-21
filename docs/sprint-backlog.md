# Fila de sprint e revisões

Atualizado em 21/10/2026. Lote lógico, sem agenda automática. Política: [workflow](agents/workflow.md). Prioridades de produto continuam em [backlog](backlog.md).

## Estado atual

INV-01–04 já auditadas; WSP-01 está implementado e auditado nas fontes. O usuário confirmou Google Calendar e Datas comemorativas em 20/10; em 21/10 confirmou que feriados persistem em todos os calendários e aprovou visualmente as Sticky Notes. A revisão independente consolidada deste lote não encontrou defeitos reproduzíveis. Permanecem pendentes os testes interativos de GTK para invoices/chooser e o aceite real de WID-02. O usuário autorizou publicar todas as alterações atuais.

| Item | Estado | Risco / responsável | Próxima ação |
|---|---|---|---|
| OPS-01 — fluxo econômico | Documentação ajustada | Baixo / supervisor | Aplicar nos próximos briefs; sem auditor ou UX para esta alteração |
| INV-01–04 — conjunto atual | Auditoria local concluída | Parecer INV-04 | Reusar evidência se o alvo não mudar; não reauditar por hábito |
| Invoices: histórico/versões e chooser em GTK real | 62 testes sintéticos passaram (PDF, histórico, versões, chooser/fluxos); GTK não inicializou neste processo, portanto interação/chooser nativos continuam sem validação | Frontend/usuário | Validar no Workspace instalado: gerar invoice de teste, abrir histórico/versões, exportar e abrir chooser; sem usar dados fiscais reais |
| CAL-06/07 — revisão média consolidada | Auditoria independente concluída sem defeito reproduzível; usuário confirmou Google, fonte de feriados funcionando e persistência em todos os calendários | Auditoria e validação do usuário concluídas | Fechado |
| CAL-01 — Calendly real | Integração por token implementada; conta real não confirmada | Usuário, se/quando desejar testar | Teste manual separado; não bloqueia funcionamento já confirmado do Google e da fonte pública |
| Formato decimal PT e rótulos de timesheets homônimas | Propostas opcionais | Baixo / frontend | Priorizar com futuro lote de UI; não ativar UX/auditor agora |
| STICKY-01 — borda e scrollbar translúcida sob demanda | Testes de contrato passam; usuário confirmou a apresentação atual das Sticky Notes como correta | Baixo / frontend | Fechado por validação do usuário |
| STICKY-02 — Ctrl+clique e feedback visual | Implementado; testes sintéticos passam; usuário confirmou que as Sticky Notes estão ótimas | Médio / frontend | Fechado por validação do usuário |
| STICKY-03 — alça de redimensionamento | Alvo 28×28 px junto à borda, cursor se-resize e gutter preservado; usuário aprovou a apresentação atual das Sticky Notes | Baixo / frontend | Fechado por validação do usuário |
| TERM-01 — foco automático do Tilix | Concluído conforme confirmação do usuário após atualização/reinício da sessão; testes dirigidos passaram e auditoria focada não encontrou bloqueio. | Médio / frontend | Fechado. Não generalizar a outras sessões/ambientes além do teste confirmado pelo usuário. |
| FX-01 — conversores fiat/cripto | Fiat chama latest Frankfurter; saída simplificada instalada. Frontend implementou na fonte modal acessível pelo widget, atualização manual, inversão persistida e polling 4h; testes dirigidos passaram. Cripto USD↔ativo selecionável continua pendente. Taxa Frankfurter é diária, não tempo real. | Médio / backend (latest/erros) + frontend (modal/polling/persistência); supervisor (requisitos e docs) | Instalação e verificação visual GNOME reais pendentes; confirmar os dois sentidos e persistência após reabrir. Sem histórico/previsão/fallback. Definir provedor/cobertura/licença/cadência cripto. Auditoria média agrupada no fechamento da sprint. |

## Cadastro de próxima tarefa

Uma linha por mudança: ID, escopo/arquivos, risco, responsável, critérios, evidência/testes e estado da revisão. Estados: planejada, em desenvolvimento, testes locais aprovados, auditoria pendente, revisada ou impedida. Para alto risco indicar operação bloqueada até revisão focada; para risco médio manter na fila de fechamento, sem ocultar pendência ao usuário.

## Fechamento do lote

1. Congelar alvo/diff e reunir testes/evidências dos responsáveis.
2. Acionar auditor uma vez para mudanças pendentes e integração; não repetir itens já revistos sem mudança.
3. Corrigir impeditivos e verificar somente o que foi afetado, ampliando se necessário.
4. Supervisor atualiza estados, limites, comando de atualização e roteiro de teste. Publicação segue autorização do usuário e revisões exigidas; nenhuma é disparada automaticamente.

## QA consolidado — 21/10/2026

Suíte Python completa: 267 testes aprovados e 3 pulados (dois cenários de socket bloqueados no sandbox e smoke de geometria GTK sem display acessível). Os 27 testes Node e os dois testes GJS passaram; `git diff --check` passou. Checagens dirigidas adicionais: FX 12/12, Sticky Links 10/10, `test_audit.py` 22/22; smoke de layout GTK passou nos testes de contrato e pulou a geometria pela falta de display. Auditoria independente consolidada concluída sem defeito reproduzível nos caminhos revisados. A rota e o formato da Frankfurter foram conferidos com a documentação oficial; consulta externa direta não foi possível neste ambiente.

GTK nativo para invoice/chooser e o seletor real de WID-02 permanecem pendentes de sessão interativa. O usuário validou as Sticky Notes e confirmou a persistência de feriados em todos os calendários, então esses itens foram fechados sem exigir teste GTK adicional. A revisão independente não encontrou defeitos reproduzíveis. O usuário autorizou publicar as alterações atuais; WID-02 continua explicitamente pendente e não é declarado concluído.

## WID-02 — Relógio mundial: requisito de seletor ainda não resolvido

Em 20/10/2026 o usuário informou que a opção continua aparecendo apenas no relógio analógico e reiterou que precisa estar disponível também no digital como dropdown com região/cidade, sem input manual. Embora exista tentativa de implementação local e testes sintéticos do catálogo, isso não atende como evidência de aceite. Manter pendente; quando retomado, verificar a página de configuração digital e a analógica na UI real, corrigir a exposição/seleção e só então atualizar o estado. O usuário pediu seguir outras implementações enquanto isso.

## WSP-01 — Orbitz Workspace (revisado, 19/10/2026)

Usuário aprovou todas as recomendações e ampliou identificação da timesheet. Um lote integrado, sem revisões por incremento; auditor independente ao final, antes de aplicar mudanças de dados/backup.

| Grupo | Escopo confirmado | Responsável | Risco / revisão |
|---|---|---|---|
| WSP-01A | Nome Orbitz Workspace, termos Agenda/Tarefas/Horas/Invoices, navegação visível e Hoje com compromissos/tarefas/timer | Frontend | Médio; integra no fechamento |
| WSP-01B | Nome/contexto da timesheet: cliente, contrato/projeto, departamento/centro de custo; fiscal separado; contexto em preview/PDF; alerta de possível duplicidade e pagamento manual independente de assinatura | Backend + frontend | Alto por persistência/faturamento; revisar antes de aplicar |
| WSP-01C | Backup/restauração do conjunto tarefas/horas/perfis/invoices/versões/estado UI, com proteção e recuperação; credenciais/calendários/Sticky Notes fora do escopo | Backend + frontend | Alto; revisar antes de restaurar/aplicar |

Fechamento: backend/frontend concluídos; uma auditoria integrada sem impeditivos reproduzidos, 169/169 testes Python e cenário completo temporário de backup/restauração aprovados. [Parecer](audits/2026-10-19-workspace-audit.md). Hashes finais conferidos pelo supervisor; UX não acionado. Plano de atualização: 21 arquivos, zero comandos. GTK/choosers reais e instalação pendentes; fechar/reabrir Workspace após aplicar, sem logout obrigatório. Nenhuma instalação ou publicação realizada.

WSP-01 PDF QA (supervisor): geradas duas amostras exclusivamente sintéticas PT/EN em `work/workspace-pdf-qa`, renderizadas por `/usr/bin/pdftoppm` e inspecionadas as quatro páginas. Contrato longo/acentos/XML literal/departamento/contexto e destinatário fiscal distintos ficaram legíveis, sem corte/sobreposição; cabeçalhos repetidos/rodapés separados. Caso 8h × BRL125,50 =1004,00 conferido. Hashes das fontes em `work/workspace-pdf-qa/source-hashes.json` para conferência final. Evidência limitada às amostras, não à interface GTK nem a documentos pessoais. Skill PDF aplicada; marcador registrado antes da criação.

## CAL-01 — integrações e About (revisado, 19/10/2026)

RC-22. Backend: clientes Google/Calendly, autenticação/cofre e testes. Frontend: conectar/sincronizar/desconectar, erros e investigação da identidade About. Risco alto em credenciais: uma revisão focada ao final, antes da aplicação. UX não acionado. Nenhuma conta real, instalação ou publicação alterada. Dependências de credenciais externas serão documentadas.

Fechamento CAL-01: [auditoria focada](audits/2026-10-19-calendar-audit.md) sem impeditivos reproduzidos,35 testes aprovados/2skips ambientais de socket, identidade Node e integração temporária com backup/desconexão aprovados. Hashes finais conferidos. About não regrediu na fonte/artefato Orbitz instalado; conteúdo da captura corresponde ao legado, acionamento exato pendente de teste visual. Plano10arquivos/0comandos, nenhuma aplicação. Reabrir Workspace e abrir prefs explicitamente por UUID após atualização; sem logout obrigatório. OAuth/PAT/cofre/GTK reais pendentes.

## CAL-02 — orientação da conexão Google (testes locais aprovados, 19/10/2026)

RC-24. Frontend: passos com links oficiais, seletor JSON identificado, nome sugerido, validação/estado dinâmico e autorização habilitada quando pronta. Backend/auth intactos; testes afetados agora, revisão média agrupada no próximo fechamento. Sem UX/auditor automáticos nem aplicação instalada. Supervisor mantém README/guia.

CAL-02: nove testes frontend aprovados (inclui JSON Desktop válido/inválido/ausente, estados de prontidão e regressões de cancelamento), sintaxe/diff conferidos. Uma fonte a atualizar, zero comandos. Autenticação/cofre intactos; revisão média permanece agrupada para fechamento. GUI real e aplicação pendentes; fechar/reabrir Workspace, sem logout.

## CAL-03 — Login Google direto (revisado, 19/10/2026)

RC-25 substitui importação de JSON no fluxo normal CAL-02. Backend configura cliente público fornecido pelo usuário, frontend simplifica diálogo, especialistas preservam cancelamento/auth/cofre. Testes afetados e uma revisão focada de autenticação antes de aplicar; semUX/global automático. Supervisor revisa README/guia para distinguir mantenedor de usuário final. Sem login real/instalação/publicação por inferência.

CAL-03 encerramento das fontes: [parecer focado](audits/2026-10-19-google-login-audit.md) sem impeditivo reproduzido;30 testes aprovados e2skips de sockets,4hashes conferidos. Plano2arquivos/0comandos. Sem login/GTK/cofre reais ou aplicação; fechar/reabrir Workspace após aplicar, sem logout obrigatório. CAL-02 foi substituído no fluxo público; revisão média daquele diálogo removido não exige auditoria separada.

CAL-04 (em investigação): erro pós-callback real, zero conexões Google salvas; diagnóstico seguro das falhas tokenendpoint, sem mudar grants/credenciais/protocolo. Testes direcionados agora; revisão média agrupada. Mensagem Orbitz do usuário ainda necessária para causa exata.

CAL-04 fechamento: defeito callback reproduzido em fixture (falha no envio perdia código/negação validados), corrigido registrando estado antes da resposta. Progresso fixo, falha reabilita botão, erros de token sanitizados. Revisão focada:36 testes aprovados/2skips socket e8 cenários adversos,6hashes conferidos; [parecer](audits/2026-10-19-google-callback-audit.md). Plano4arquivos/0comandos. Login real/causa exclusiva do usuário não comprovados. Instalação pendente; fechar/reabrir Workspace, sem reinício de sessão.

CAL-05/RC-27 em implementação: causa client_secret ausente confirmada no endpoint oficial com código fictício e rede autorizada, sem conta/token real. Backend configuração privada mantenedor+tool+diagnóstico; revisãofocada antes aplicar. Caminho JSON real solicitado por texto, nunca conteúdo/chat. UI normal loginGoogle intacta, distribuição pública pendente.

CAL-05 revisado: [parecer](audits/2026-10-19-google-client-config-audit.md),35pass/2skips/6 adversos,6hashes. Configuração real do mantenedor preparada após permissão, check e permissões privadas conferidos pelo supervisor; auditor usou só fixtures. Plano2arquivos/0comandos para instalação; login real pendente. Reabrir Workspace após aplicar, sem logout.

CAL-06/RC-28 em desenvolvimento: usuário confirmou loginGoogle, mas feriados/tarefas/horas marcados não aparecem na fonte ativa da Agenda. Frontend alinhar conteúdo/legenda/tooltips/rotas e link de ativação opcional; backend/auth intactos. Testes afetados agora, revisão média no próximo fechamento; semUX/auditor automático.

CAL-06 testes locais aprovados:18 testes (7novos+11frontend), AST/diff check; fonte estável,5arquivos/0comandos. Revisão média continua na fila para fechamento, sem convocação adicional por incremento. GUI/aplicação pendentes. Reabrir Workspace após atualizar, sem logout; conferir dias com feriado de outra fonte e atividade local.

Validação manual do usuário em 20/10/2026: Google Calendar funcionou na instalação atual. Confirma o fluxo usado pelo usuário; não generalizar a todas as contas, versões ou ao Calendly. A revisão média permanece no fechamento consolidado.

CAL-07/RC-29 em implementação: fonte pública padrão permanente com Ativar/Desativar e adoção/restauração idempotente. Backend estado/persistência; frontend gerenciamento/filtros/sync/cancel/Agenda. Testes afetados agora, revisão média agrupada; nenhuma nova auditoria/UX ou aplicação automática.

CAL-07 testes locais aprovados:31 dirigidos (7persistência+16frontend+8atividade) e regressão dados externos, sintaxe/diff. Plano3arquivos/0comandos. Risco médio, revisão na fila de fechamento; sem auditor/UX extra. Sem dados reais ou instalação alterados. Teste manual: reabrir→Gerenciar→fonte padrão recuperada→Desativar→reabrir e confirmar desativada→Ativar. Sem logout necessário.

Validação manual do usuário em 20/10/2026: a fonte Brasil · Datas comemorativas funcionou na instalação atual. Não há confirmação explícita do ciclo desativar→reabrir→reativar; manter esse caso como teste manual opcional de fechamento. A revisão independente média continua agrupada para a sprint.

## WID-02 — relógio mundial adicional

Implementação local: opção na configuração do relógio digital para ativar o relógio secundário, escolher cidade/região em catálogo pesquisável e mostrar a localidade com hora formatada. O catálogo vem da base tzdata do sistema e não depende de GWeather; o mesmo seletor substitui o campo manual de sobrescrita de fuso nos relógios digitais e analógicos. Testes do catálogo e formatação/timezone passam. Risco médio; revisão independente fica no fechamento da sprint. GTK/preferências e visual ainda não conferidos em sessão real; não instalado.
