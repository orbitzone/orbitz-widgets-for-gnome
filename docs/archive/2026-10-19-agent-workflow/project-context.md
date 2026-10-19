> HISTÓRICO — snapshot anterior à revisão de 19/10/2026; não são instruções vigentes. Consulte docs/agents/workflow.md.

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

## Identidade Orbitz própria — ID-01

Pedido usuário: projeto próprio atribuído a Felipe Santiago/orbitzone, com origem azclock menos destacada e GitHub Orbitz principal. Nova identidade em preparação: nome Orbitz Widgets for GNOME; UUID orbitz-widgets@orbitzone.github.io; URL https://github.com/orbitzone/orbitz-widgets-for-gnome; schema org.gnome.shell.extensions.orbitz-widgets; versão própria1. Instalação atual ainda legada até migração explícita; não executar update antigo contra metadados incompatíveis. Créditos concentrados em docs/credits.md, licenças e gettext legado preservados. Migrador terá plano/preparo/rollback e ativação manual separada; listas Shell somente snapshot, sem troca automática. RC-13/D22 definem aceite; bugs RAM/EXT mantidos separados.

ID-01 GTypes:20 registros explícitos OrbitzWidgets evitam colisão de tipos persistentes do legado, com classes JS/exports preservados. Reporte integrado auditor:83 Python/18 Node/2 testes GJS/110 sintaxes passaram, revisão final pendente neste marco. Plano sem flags retornou stateplan/2chaves, sem preparo/ativação, com warnings dconf de runtime somenteleitura. Instalação ativa continua legado; não liberar reinício para testar identidade nova sem confirmar preparo/descoberta/ativação. Guia identity-migration separa operações.

ID01 consolidada: fontes com identidade Orbitz/Felipe/GitHub, schema novo compatível e20 nomes GType próprios; origem e licenças preservadas em docs/credits.md. Migrador plano/preparo/rollback+updater identityaware auditados, ID-A01 resolvido (11 testes específicos finais após global de 83/18 arquivos Node/2 testes GJS). Guia docs/operations/identity-migration.md pronto. Ainda NÃO preparada/ativada na instalação real; solicitar execução --prepare e conferir retorno antes de orientar ativação/reinício. Sem commit/push desta etapa. RAM/EXT e visual permanecem pendentes independentes.

ID-01 preparada realmente pelo usuário: execução `20261018-020439-gq2pgf2a`. Hashes da árvore nova corretos, árvore antiga intacta, configs dos dois schemas conferidas pelo supervisor. Apenas legado selecionado; nova identidade não ativada. Acesso ao estado GNOME indisponível à ferramenta (exit2 sem detalhe); confirmar descoberta via terminal antes da troca. Não repetir prepare.

ID-01 ativada pelo usuário: info GNOME mostrou Orbitz State:ENABLED após disable legado/enable novo. Supervisor confirmou seleção exclusiva do UUID Orbitz em enabled-extensions; legado não selecionado. Pode testar sem outro reinício; instalação antiga/backup preservados. Aceite gráfico e dados pelo usuário ainda pendentes.

BRAND-01 implementa SVG original `extension/media/orbitz-logo.svg` (anel/órbita/satélite cyan/teal), About via Gio.FileIcon e version-name1.0 com version inteiro 1. Backend whitelist explícita metadata/asset e testes rollback; auditoria ainda em conclusão neste marco. Screenshot usuário mostra página legada; arquivos About instalados do UUIDnovo coincidem com fonteOrbitz antes de nova marca. Sempre fechar preferências velhas e abrir explicitamente `gnome-extensions prefs orbitz-widgets@orbitzone.github.io`. Não declarar logo instalada antes de update/hashes.

BRAND-01 auditada, nenhum impeditivo reproduzido:9 testes updater/1 Node identidade/1 GJS (20 pares GType), SVG seguro/local renderizado. Preview apenas evidência, fonte é SVG próprio em media. Plano confirmado3 arquivos/0 comandos. Instalação ainda precisa atualização do usuário; depois fechar/reabrir prefs pelo UUID Orbitz, sem logout obrigatório. Validar página GTK real e versão 1.0; legado e licenças preservados.

BRAND-01 aplicada pelo usuário na execução `20261018-021732-_vzv_1d9`; plano atual zero arquivos/comandos confirma fonte/instalação sincronizadas. Usuário relatou aparente normalidade. Revisão curta pré-commit passou identidade Node, GJS 20 pares, schemas strict, 9 testes updater e diff check; sem nova global. Orbitz ativo/legado desativado preservados; RAM/EXT não declarados resolvidos.

## INV-01 — menu da agenda e invoice

Pedido do usuário: mover arquivadas/restauração para menu na linha da data e gerar PDF PT/EN de horas × taxa com emitente/cliente persistentes. RC-15/D-24 definem critérios; módulos separados de domínio/perfil/PDF e formulário/menu. Backend estável com 11 testes dirigidos; frontend integra e trata revisão UX. Supervisor inspecionou quatro páginas de PDFs sintéticos PT/EN (7h × 125,50 = 878,50), com acentos e descrições longas legíveis. ReportLab do sistema 3.6.8 e DejaVu; Poppler do sistema utilizado porque o empacotado requer glibc indisponível.

Perfis privados separados em invoice-profiles.json (emitente/idioma globais; cliente/taxa/moeda por timesheet), persistidos após PDF salvo, cancelamento não grava. Sem mutação de horas nem integração fiscal. Plano local neste marco: 6 arquivos, 0 comandos; instalação ainda anterior. Auditoria integrada e validação GTK real permanecem distintas. Após aplicar, fechar/reabrir agenda; não reiniciar sessão por esta mudança Python.

INV-01 consolidação: frontend estável, parecer UX estático sem impedimento após ajustes de largura/atalhos/prévia/foco. Auditor informou 17 testes novos e oito regressões planner aprovados; não houve execução global repetida. QA visual documentada em `docs/audits/2026-10-18-invoice-pdf-qa.md`; relatórios backend/frontend e revisão UX disponíveis. Validação GTK/AT/chooser nativo real pendente. Não instalada: plano 6 arquivos/0 comandos; usuário aplica pelo atualizador e fecha/reabre agenda, sem logout obrigatório. Nenhum commit/push executado.

INV-01 — auditoria independente concluída sem impeditivo reproduzido no escopo: `docs/audits/2026-10-18-invoice-audit.md`. Supervisor conferiu os oito hashes do alvo e o plano de seis arquivos/zero comandos. Código apto para atualização local; aplicação e teste GTK real ainda pendentes. Reabrir agenda após aplicação, sem logout.

## INV-02 — seleção de período em calendário único (19/10/2026)

Usuário pediu três modos (mês, histórico, específico) e seleção visual de intervalo em um calendário. RC-16/D-25: mês civil; histórico default; dois cliques início/fim inclusivos, crossmês/ano, navegação não seleciona, intervalo incompleto bloqueia revisão. Frontend/UX implementam componente isolado para não alterar MonthCalendar da agenda, que seleciona dia ao navegar. Domínio/perfis/PDF preservados; auditor após estabilidade. Atualização local/teste real ainda pendentes.

INV-02 frontend estável: `invoice_period_ui.py` isola modelo date/calendar e calendário da invoice; `invoice_ui.py` envia bounds ISO existentes. Dez testes de período e seis regressões frontend aprovados pelo desenvolvedor. Achado UX de invalidação por navegação/foco corrigido com comparação semântica de modo/mês/extremos; sem alteração da seleção, preserva prévia. Auditoria dirigida em andamento. Plano atual: dois arquivos/zero comandos; reabrir agenda após aplicar, sem logout.

INV-02 — resultado consolidado em 19/10/2026: auditoria dirigida aprovou 27 testes (10 de período e 17 regressões invoice), três sintaxes e diff-check, sem impeditivo reproduzido. Supervisor conferiu os três hashes do alvo. Relatório `docs/audits/2026-10-19-invoice-period-audit.md`; revisão UX em `docs/design/2026-10-19-invoice-period-review.md`, achado de invalidação tratado. Funcional local validado; visual/teclado/AT GTK real pendentes. Plano de dois arquivos/zero comandos, aplicação ainda necessária; encerrar/reabrir agenda, sem logout GNOME.

RC-17 (19/10/2026): usuário reforçou conclusão obrigatória com comando completo de atualização em cada entrega de código. Supervisor deve responder de forma autossuficiente, distinguir implementação/instalação, informar ATUALIZACAO_OK, reabertura/reinício e teste. Documentação somente dispensa aplicação/reinício. Contratos `docs/agents/project-owner.md` e `team.md` atualizados; evitar respostas finais vazias após relatórios internos tardios.

## INV-03 — histórico local (19/10/2026)

Pedido: consultar/baixar/excluir invoices no menu por empresa/cliente/mêsano. RC-18/D-26: novas exportações guardam cópia exata privada e snapshot; grupo empresa=timesheet, cliente distinto por identidade e mês/ano de emissão explícito, período de serviços separado. Download cópia local; exclusão confirmada só do registro gerenciado, sem tocar exportação externa/horas/perfis. Backend cria armazenamento, frontend integra menu/UI/exportação, UX via frontend, auditor após estabilidade. Não importar PDFs antigos nem alterar renderer por esta tarefa; sem implantação automática.

INV-03 marco: frontend estável com oito testes de histórico e seis regressões frontend, incluindo fluxo com acervo real temporário e bytes PDF sintéticos. Backend entregou dez testes e listagem apenas metadata/stat; ações validam hash. Auditor identificou entrada None no snapshot de um metadata corrompido abortando a lista (sem apagar dados), correção encaminhada ao backend antes da integração final. Revisão UX estática favorável, com texto vazio/tudo ilegível corrigido; opções menores de formatação/rótulos no backlog.

INV-03 auditoria: IH-A01 (snapshot.entries=[null] derruba listagem) corrigido pelo backend com validação estrutural localizada, 11 testes específicos; reverificação independente pendente. IH-A02 reproduzido: escolher arquivo dentro do acervo como destino da nova exportação pode sobrescrever emissão anterior; frontend recebeu guarda antes do writer. Sem acesso a dados reais ou prejuízo externo nas reproduções. Ambos impedem conclusão enquanto não reverificados.

INV-03 — conclusão local em 19/10/2026: auditoria independente aprovou 47 testes de invoices (incluindo 11 histórico backend e nove histórico frontend), seis sintaxes e diff-check. IH-A01/IH-A02 resolvidos e reverificados; nenhum impeditivo remanescente no escopo. Supervisor conferiu os seis hashes finais. Relatório `docs/audits/2026-10-19-invoice-history-audit.md`; revisão UX estática separada. Funcional local e integridade aprovados; GTK/AT/chooser/confirmações reais pendentes. Listagem metadata/stat e hash nas ações, sem benchmark. Plano de quatro arquivos/zero comandos, ainda precisa aplicação local. Após ATUALIZACAO_OK, encerrar/reabrir agenda, sem logout; testar gerar uma invoice sintética, consultar/salvar cópia/cancelar exclusão e excluir somente registro de teste. PDFs antigos não importados automaticamente. Nenhuma instalação, commit ou push executado nesta etapa.

## INV-04 — fluxo assistido gov.br (19/10/2026)

Usuário aprovou proposta após consulta a fontes oficiais: API direta restrita a órgãos públicos; portal gratuito ao cidadão com conta prata/ouro. Implementar ações explícitas copy+abrirportal, importar versão apresentada como assinada e abrir VALIDAR, sem upload/login automático ou guardar senha. RC-19/D-27: bytes originais/versões preservados, versões privadas e estado pendente; nenhum hash/importação/abrirsite significa assinatura válida. Backend armazenamento compatível; frontend histórico/helper com UX, auditor após estabilidade. Nenhuma mudança de renderer/perfis ou emissão fiscal. Aplicação e GTK real ainda pendentes.

INV-04 marco estável: backend dez testes novos de versões e 11 regressões histórico; frontend cinco testes novos de fluxo/integração temporária e nove regressões histórico. APIs alinhadas; versões sob versions/ com metadados próprios e original v1 preservado. Escolha técnica do diálogo separado “Original e versões…” aceita pelo supervisor e registrada em D-27; sem mudança de escopo nem promessa de equivalência visual. UX revisou textos/estados sem falsa validação; ajustes locais de rótulo/wrap/foco tratados. Auditoria integrada solicitada; nenhuma instalação/portal/assinatura real executados.

INV-04 — conclusão local em 19/10/2026: auditoria independente aprovou 62 testes de invoices (15 novos), seis sintaxes e diff-check, sem impeditivo reproduzido. Supervisor conferiu seis hashes finais; relatório `docs/audits/2026-10-19-invoice-signatures-audit.md`. Original v1 e versões privadas preservados, cancelamentos/URLs fixas/vínculos e estado pendente verificados com dados temporários. Não houve assinatura, validação criptográfica, acesso real a portais/contas ou dados pessoais. GTK/AT/browser real e ações manuais nos serviços permanecem pendentes. Plano quatro arquivos/zero comandos; aplicação ainda necessária, seguida de fechar/reabrir agenda, sem logout. Teste manual: histórico→selecionar invoice→Assinar com gov.br→salvar cópia/portal; depois importar PDF escolhido com confirmação e consultar Original e versões/VALIDAR. Estado importado permanece pendente. Nenhuma instalação, commit ou push executado nesta entrega.
