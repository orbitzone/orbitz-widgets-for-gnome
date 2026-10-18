# Contexto persistente do projeto

Responsável: analista de requisitos/supervisor. Atualizado em 18/10/2026 com base na auditoria inicial, nos contratos e na baseline. Este índice organiza o conhecimento registrado; não significa leitura exaustiva de cada linha nem memória infalível. Conferir código e diff antes de orientar alterações. Não guardar dados pessoais, credenciais ou conteúdo do cofre.

## Onde encontrar cada informação

| Assunto | Fonte principal | Componentes relevantes |
|---|---|---|
| Produto e operação | `README.md` | Extensão, widgets, agenda, notas e lançadores |
| Plataforma e dependências | `stack.md`, `extension/metadata.json` | GJS/GNOME 42–44 declarados; GTK 3/4; Python; WebKit; libsecret |
| Requisitos e aceite | `docs/requirements.md` | Separação entre confirmado, observado e proposto |
| Prioridades e pendências | `docs/backlog.md` | RF-01 e propostas B-01 a B-07 |
| Decisões e restrições | `docs/decisions.md`, `AGENTS.md` | Persistência, licenças, instalação ativa e escopo |
| Equipe e propriedade de arquivos | `docs/agents/team.md` e contratos por papel | Supervisor, backend, frontend e auditor |
| Baseline reproduzida | `docs/audits/2026-10-18-baseline.md` | 44 Python; 12/15 JS; sintaxe de 78 arquivos; hashes iniciais |
| Shell e interação | `extension/extension.js`, `dragging.js`, `grouping.js` | Controlador, widgets, diálogos, mídia e grupos |
| Preferências | `extension/prefs.js`, `extension/settings/`, schemas | GSettings e UI GTK 4 |
| Agenda e interface | `extension/planner/calendar-app.py`, `*_ui.py`, `month_calendar.py`, `calendar_selector.py`, `planner_tools.py` | Tarefas, fontes, timesheets e recuperação |
| Domínio e dados da agenda | `extension/planner/store.py`, `timesheet.py`, `ui_state.py` | JSON, lock, gravação atômica, backups, CSV e rascunhos |
| Calendários externos | `extension/planner/apple_client.py`, `ics_client.py`, `external_store.py` | CalDAV/ICS somente leitura, cache, Secret Service |
| Alertas | `extension/planner/calendar.js`, `reminders.js` | Cache sincronizado, deduplicação e ciclo da extensão |
| Coletores | `widgets/`, `extension/stop-collectors.py` | Runtime limitado, worker compartilhado, métricas e cancelamento |
| Notas | `sticky-notes/postits.py`, `storage.py` | GTK, SQLite WAL e backups independentes |
| YouTube | `extension/youtube-widget/` | GTK/WebKit, HTML e servidor local com token |

## Invariantes a incluir nas tarefas afetadas

- Repositório não atualiza automaticamente instalação ativa. Preservar caminhos históricos até migração específica e validada.
- Tarefas/timesheets locais independem das fontes externas. Importação é explícita; credenciais não ficam nos JSON nem no repositório.
- Preservar atomicidade, locks, backups, vínculos, unidades e limites de processos/saída.
- Backup da agenda não inclui banco das notas nem cofre. Lembretes usam cache; sincronização externa depende da agenda aberta.
- UUID/schema herdados e manifesto não comprovam compatibilidade testada. Node/mocks não substituem execução GNOME/GTK.
- Não editar vendor, licenças, binários ou instalação ativa como parte da refatoração estrutural.

## Atualização e validade

Ao receber entrega: revisar diff e relatório; atualizar mapa dos módulos e contratos afetados; ligar requisito a tarefa, arquivos e evidência; registrar o que ainda não foi validado. Identificar o commit e alterações locais relevantes nas evidências. Se fonte divergir do código, registrar divergência e corrigir o contexto antes da próxima delegação. Consultar relatórios recentes em `docs/audits/`; não reutilizar resultados antigos como execução atual.

## Conteúdo mínimo do resumo de tarefa enviado aos agentes

Objetivo e requisito; comportamento esperado/exemplo; arquivos sob responsabilidade exclusiva; pontos de entrada e contratos com outros módulos; restrições de dados/segurança; critérios de aceite; testes relevantes e falhas já conhecidas; dependências, dúvidas e evidência de origem. Fornecer só o contexto pertinente, com referências para detalhes.

## Design/UX

Contrato em `docs/agents/designer-ux.md`; inventário/padrões/relatórios em `docs/design/` quando entregues. Comunicação exclusiva UX↔frontend; frontend transmite conclusões ao supervisor. Práticas de entrega pequena, contratos, propriedade dos arquivos, evidências e medição de desempenho confirmadas pelo usuário em 18/10/2026.

## Processo vigente

Autonomia, comunicação crítica, propriedade, critérios de conclusão e validações separadas: seção “Autonomia, colaboração e conclusão” em `docs/agents/team.md`, confirmada em 18/10/2026. Centralização do contexto não impede investigação técnica necessária; especialistas registram fontes/conclusões ao analista. UX permanece exclusivo ao frontend.

## Módulos backend extraídos durante RF-01

Observados no checkout em 18/10/2026, ainda pendentes de integração/auditoria final: `extension/planner/calendar_events.py` (normalização iCalendar), `credential_vault.py` (cofre), `atomic_json.py` (gravação atômica compartilhada) e `widgets/firewall_patterns.py` (análise pura UFW). Chamadores históricos mantêm reexports segundo informe backend; confirmar no relatório final. Não presumir que esses módulos já estejam na instalação ativa.

## Módulos frontend durante RF-01

Marco relatado pelo frontend e arquivos presentes no checkout: `extension/commandPanels.js`/`panels/`, `settings/TimeZoneDialog.js`, `planner/task_timesheet_ui.py`, `sticky-notes/card.py`, `youtube-widget/youtube_api.py` e `youtube_server.py`. Integração e validações finais pendentes; não inferir implantação. Revisão UX estática inicial em `docs/design/2026-10-18-review.md`, recebida via frontend, com oito achados e validação visual pendente.

Backend declarou estado estável em RF-01; inventário e evidências por arquivo em `docs/audits/2026-10-18-backend-refactor.md`. README e stack agora descrevem os quatro módulos backend novos. A previsão de 57 testes Python é contagem do backend anterior aos novos testes frontend, não resultado integrado executado.

Frontend estável: inventário dos 14 módulos novos, testes específicos e limites em `docs/audits/2026-10-18-frontend-refactor.md`; README/stack atualizados. Auditoria integrada encaminhada, ainda sem resultado. Captura GTK bloqueada nos sockets Broadway; revisão visual pendente. Contagem histórica JS divergente em reconciliação pelo auditor: resumo 12/15 vs inventário de 14 originais.

Errata confirmada pelo auditor: baseline JS efetiva **11/14 aprovados**, três falhas; resumo anterior 12/15 incorreto. Suíte integrada relatada: **62 Python e 16 arquivos JS aprovados**, revisão final em elaboração. Complemento UX confirma equivalência estática das extrações listadas, sem aprovação gráfica.

## Resultado consolidado RF-01

Auditoria independente final recebida: `docs/audits/2026-10-18-integrated-audit.md`. 62/62 Python, 16/16 arquivos JS e 102 sintaxes; manifesto de 103 fontes/testes estável; nenhum impeditivo reproduzido no escopo revisado. Supervisor registrou aceite parcial das verificações locais. Visual/interação pendentes (Broadway bloqueado); sem benchmark nem conclusão integral da RF-01. Próximos responsáveis frontend/UX para evidência gráfica isolada quando permitida. Os estados anteriores “relatório em elaboração” documentam marcos anteriores, substituídos por este consolidado.

## Responsabilidade de prontidão

Supervisor confere instalação e caminho de teste após cada atualização e informa explicitamente se pode reiniciar sessão, se basta reabrir aplicativo ou se há impedimento. Regra RC-10/D-19 e contrato project-owner. DEP-01 só pode ser liberada após confirmação real do instalador; o comando fornecido ao usuário não comprova aplicação.

DEP-01 aplicada pelo usuário em 18/10/2026 e verificada pelo supervisor: 49 hashes instalados corretos, configuração migrada conferida, zero arquivos/comandos pendentes. Reinício manual liberado para carregar o refactor; não houve reinício automático. RF-01 continua aguardando observação gráfica/interativa após nova sessão. Backup privado fora do repositório: execução `20261018-010701-upda7txp`.

BUG-01: correção de roteamento do coletor CPU estável/auditada em `docs/audits/2026-10-18-hardware-fix-audit.md`; instalação corretiva pendente. 1 arquivo/0 comandos no plano do instalador. Testes CLI reais do repositório retornam protocolos CPU/RAM/SSD corretos; clique RAM real não reproduzido graficamente. Correção não altera Shell: fechar/reabrir painel é teste inicial após instalar, sem logout obrigatório. Divergência de dispositivos externos registrada separadamente como BUG-02.

VIS-01: padrão histórico confirmado RC-12/D20: resumo Hardware usa markup monospace size7680(7,5pt), line_height1.5, oito células, sem linhas vazias. Padding L/R20 mantido; configurações antes/agora iguais. Backend restaura apresentação, frontend/UX formalizam padrão; código auditado/aplicação ainda pendentes neste marco. Worker lê/compila scripts no início: após atualizar apresentação, reiniciar widgets pelo controlador para recriar worker, sem exigir logout por mudança exclusiva Python. RAM clique permanece não resolvido até teste específico.

VIS-01 corrigida no código/auditada: `docs/audits/2026-10-18-hardware-markup-audit.md`;9 Python/2 Node/GJS/Pango passaram, UX confirmou formato estático. Pronta para atualização local de 1 arquivo, ainda dependente do terminal do usuário por sandbox. Reinício necessário do worker via controlador de widgets, sem logout obrigatório. Padrão visual histórico registrado em RC-12/D20 e `docs/design/2026-10-18-hardware-restoration.md`. RAM permanece pendente manual.

## Consolidação antes de commit/push — 18/10/2026

Documentação de produto atualizada para distinguir estado atual dos marcos históricos. Nova execução completa:71 Python/17 Node/GJS-Pango aprovados. Plano do atualizador: zero arquivos e zero comandos; fonte visual coincide com instalada, sem inferir sessão carregada/validação manual. CPU/SSD confirmados; RAM ainda pendente. Git fetch bloqueado por .git somente leitura; consulta ls-remote falhou DNS; nenhum commit/push feito pela ferramenta.
