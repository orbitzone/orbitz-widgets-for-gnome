# Backlog e próximas entregas

Registro inicial: 17/10/2026; estado consolidado atualizado em 18/10/2026. A tabela original e os marcos históricos são preservados abaixo; o resumo atual prevalece para andamento. Prioridades propostas não constituem aprovação comercial. O agente trabalha quando acionado, sem monitoramento contínuo.

## Resumo atual

- OPS-01 (19/10/2026): fluxo econômico vigente em `docs/agents/workflow.md`; fila consolidada em `docs/sprint-backlog.md`. Esta política prevalece sobre acionamentos por tarefa descritos nos marcos históricos abaixo.

- INV-01: menu e invoice PDF PT/EN implementados; 17 testes novos e oito regressões planner aprovados na auditoria dirigida. QA visual de quatro páginas sintéticas aprovada; aplicação local e teste GTK real pendentes.

- RF-01: implementação e auditorias locais concluídas, validação gráfica/interativa integral pendente; não declarar conclusão integral.
- B-01: falhas históricas de testes resolvidas e verificadas; baseline corrigida 11/14 JS, suíte atual 17/17 Node aprovada.
- DEP-01: atualização local e rollback implementados/auditados; instalação conferida, plano zero arquivos e zero comandos pendentes. Não equivale a pacote de instalação limpa.
- VIS-01: padrão histórico implementado/auditado e arquivo instalado coincide com a fonte atual; aparência real após restauro ainda requer confirmação manual.
- BUG-01: CPU e SSD confirmados pelo usuário; clique RAM ainda reportado sem abertura, sem confirmação de reteste após restauro visual.
- BUG-02: diferenças históricas de dispositivos externos e alertas permanecem para análise própria, sem mudança semântica nesta entrega.
- B-02/B-03: há atualizador local e comandos migrados; distribuição/reinstalação limpa e consolidação integral ainda não validadas.
- Verificação completa atual: 71 Python, 17 arquivos Node e GJS/PangoCairo aprovados; diff check sem erros. Commit/push solicitados, execução pela ferramenta impedida por Git somente leitura e rede/DNS indisponível.

## Tabela inicial (histórico)

| ID | Prioridade sugerida / estado | Entrega e motivo | Aceite proposto / dependências |
|---|---|---|---|
| B-01 | P1 · proposto | Investigar e corrigir as três falhas JavaScript da baseline. Recuperar confiança na verificação antes de mudanças maiores. | Reproduzir cada falha; determinar defeito de produto, mock ou expectativa; corrigir causa sem enfraquecer testes; executar todos os arquivos JS de teste e verificações afetadas; registrar comandos, ambiente e resultados. |
| B-02 | P1 · proposto | Definir e validar instalação reproduzível de todos os componentes. Hoje não há pacote único atualizado e validado. | Definir ambiente alvo; inventariar dependências obrigatórias/opcionais, schemas, aplicativos e licenças; documentar instalação em ambiente limpo, desinstalação e rollback; verificar widgets, agenda, notas e preservação de dados sem usar pastas históricas. Depende da proposta de caminhos B-03. |
| B-03 | P1 · proposto | Consolidar caminhos históricos dos coletores e configurações. Reduzir dependência de diretórios de conversas. | Mapear comandos GSettings e módulos auxiliares sem copiar dados pessoais; propor destino canônico e migração reversível; validar em ambiente isolado; atualizar referências e documentação; só remover dependências antigas após evidência e autorização aplicável. Não apagar pastas históricas nesta entrega. |
| B-04 | P2 · proposto | Consolidar testes e evidências da agenda hoje distribuídos em diretórios externos. | Inventário com origem e cobertura; incorporar apenas testes/fixtures sem dados particulares; execução reproduzível em ambiente isolado; lacunas explícitas para calendário, tarefas, timesheets, lembretes e restauração. |
| B-05 | P2 · proposto | Validar recuperação e migração completa. Dados JSON, SQLite e credenciais têm ciclos separados. | Exercitar backup/restauração com dados sintéticos, concorrência e falha de escrita; comprovar preservação de vínculos; documentar SQLite/WAL e reconexão do cofre; não tratar backup JSON como backup completo. |
| B-06 | P2 · proposto | Construir matriz de compatibilidade e testes gráficos. Manifesto não equivale a suporte comprovado. | Acordar versões/sessões alvo; registrar execução isolada e limitações por GNOME e X11/XWayland; verificar ciclo do controlador, grupos, janelas, alertas e cancelamento. |
| B-07 | P3 · proposto | Revisar identidade/metadados e empacotamento/licenças. Manifesto conserva Desktop Clock/azclock v7. | Proposta explicita compatibilidade do UUID/schema, migração de configurações e créditos; revisar distribuição de vendor e Speedtest sem presumir permissão de redistribuição; decisão antes de alterar identidade. |

## Recorte inicial de B-01

| Teste | Evidência histórica no README | Investigação necessária |
|---|---|---|
| `tests/test_storage_ui.js` | Mock sem `_updatesNote`. | Conferir contrato de `_renderStorage`, completar mock se correto e preservar assertivas de armazenamento. |
| `tests/test_stats_storage_click.js` | Região de clique esperada diverge da implementação. | Determinar comportamento desejado antes de alterar expectativa ou produto; registrar exemplo reproduzível. |
| `tests/test_widget_controller.js` | Mock sem `Calendar`. | Conferir ciclo do serviço de lembretes e dependências do controlador; validar abertura/encerramento repetidos. |

Essas descrições não são diagnósticos novos nem prova de que apenas os mocks estejam errados. A suíte não foi reexecutada nesta auditoria.

## Estado da missão de documentação

Entregues `requirements.md`, `backlog.md` e `decisions.md`, com inspeção estática e revisão documental. Preservados README e instruções anteriores. Nenhuma correção funcional, instalação, publicação ou automação foi realizada.

Próxima entrega recomendada: **B-01**, como investigação pequena com relatório das causas e correções proporcionais, mediante pedido de implementação. Em seguida, elaborar conjuntamente B-02/B-03 para que o destino dos arquivos e a migração façam parte da instalação reproduzível.

## RF-01 — Refatoração estrutural (18/10/2026)

Confirmado pelo usuário; em andamento na preparação/baseline. Backend e frontend atuarão em paralelo conforme `agents/team.md`, seguidos de integração do supervisor e auditoria independente. Não representa aprovação das demais propostas do backlog.

RF-01: baseline executada pelo auditor (44 Python, 12/15 JS; mesmas três falhas). Liberação de implementação enviada a backend/frontend; última consulta indica `waitingOnApproval` em ambos, sem operação detalhada pela ferramenta. Refatoração e auditoria final pendentes. Evidência: `audits/2026-10-18-baseline.md`.

## UX-01 — Inventário visual e revisão de usabilidade (18/10/2026)

Confirmado pelo usuário; preparação do agente concluída, diagnóstico pendente. Responsáveis: Design/UX e frontend, com comunicação direta exclusiva do UX ao frontend. Inventariar padrões observados, avaliar espaçamento, cores, tipografia, foco, estados, dimensões e transições. Aceite: relatório com evidências e limitações, critérios por achado e encaminhamento pelo frontend ao analista. Melhorias que mudam aparência/comportamento são separadas da RF-01 para avaliação de escopo.

### RF-01 — recebimento do inventário frontend

Frontend reportou inspeção sem alterações/testes e solicitou liberação. Supervisor reiterou explicitamente a liberação já dada, referenciando a baseline em `audits/2026-10-18-baseline.md`. Plano recebido: separar responsabilidades de Shell/painéis, diálogos de preferências/agenda, cartão das notas e módulos locais do YouTube conforme benefício e preservação de contratos; manter componentes coesos e legado necessário com justificativa. Execução por componentes e relatório final permanecem pendentes de evidência; não registrar inspeção como refatoração concluída.

### RF-01 — recebimento do inventário backend e baseline

Backend reportou revisão inicial de 27 arquivos próprios, sem mudanças ou testes; supervisor reiterou liberação expressa. Extrações planejadas: normalização iCalendar, análise pura UFW, pontos de entrada dos coletores e helper atômico somente onde contratos de persistência forem equivalentes. Preservar APIs/reexports, execução pelo worker e políticas de backup/lock; testes isolados de fronteiras críticas com dados sintéticos. Relatório final e execução ainda pendentes. Auditor confirmou a baseline reproduzida e aguarda estado estável para avaliação final.

### RF-01 — marco de implementação backend (18/10/2026)

Estado parcial: implementado sem validação integrada/auditoria. Backend relatou extrações em `calendar_events.py`, `credential_vault.py`, `atomic_json.py` e `widgets/firewall_patterns.py`, reexports preservados e main guards de cinco coletores. Inspeção do supervisor confirmou presença dos módulos/importações e alterações no checkout; não equivale a revisão funcional. Evidências relatadas pelo backend: 19 testes de auditoria/runtime, 7 testes iniciais de planner e 5 de entrypoints aprovados; teste adicional de concorrência ainda em validação no momento do informe. Comparação AST de 15 definições e sintaxe de 33 arquivos aprovadas segundo o agente. Aguardar relatório final com comandos/resultados, estado estável do frontend e auditoria independente antes de concluir RF-01.

### RF-01 — marco de implementação frontend (18/10/2026)

Frontend relatou extrações de painéis GJS, Card GTK, cliente/cache e servidor YouTube, diálogo de fuso e tarefa→timesheet, além de reutilização de createComboRow. Relatou composição de 24 métodos validada com GJS/GObject e três testes históricos aprovados individualmente. Supervisor inspecionou o diff dos três testes: mocks foram completados; expectativas CPU/RAM passaram a refletir o comportamento observado de abrir hardware e ícone ativo passou a branco, coerente com README. Isso não cria novo requisito nem substitui auditoria. Relatório e verificações Python/GTK isoladas permaneciam pendentes no marco; não há conclusão integrada.

### UX-01 — diagnóstico recebido via frontend

Relatório inicial em `docs/design/2026-10-18-review.md`: oito achados estáticos A–H com critérios propostos. Nenhuma validação visual ou acessibilidade integral foi comprovada. Registrar melhorias como propostas separadas: cores/tipografia/contraste e dimensões, foco/modalidade, feedback de erro YouTube, nomes acessíveis, alvos/gestos das notas e animações. Cenário E (erro de chave sintética na aba Comentários) tem evidência estática concreta, mas requer reprodução isolada antes de classificação como defeito confirmado. Não implementar redesign sob RF-01.

### RF-01 — backend estável para integração

Relatório final recebido: `audits/2026-10-18-backend-refactor.md`. Revisados 27 originais (11 refatorados, 16 mantidos) e adicionados quatro módulos. Backend relatou 32 testes específicos aprovados (19 existentes, 8 planner incluindo concorrência, 5 entrypoints), 33 sintaxes e comparação AST das extrações/entradas. Supervisor conferiu relatório e fronteiras de escrita/reexports e atualizou README/stack. Não houve nova suíte global pelo supervisor. Backend declarou ausência de mutações/testes em curso; aguardar frontend estável para auditoria integrada. Validação gráfica e revisão independente continuam pendentes.

### RF-01 — estado integrado encaminhado ao auditor

Frontend declarou estado estável e entregou `audits/2026-10-18-frontend-refactor.md`: inventário original, 14 módulos, 12 entrypoints JS específicos aprovados, 5 testes Python sintéticos YouTube, sintaxe de 27 JS/7 Python, registro real GObject/Gtk4 e comparação dos corpos extraídos. Supervisor conferiu relatório/diff check e atualizou README/stack. Ambos os desenvolvedores estáveis; auditoria integrada solicitada ao auditor com relatório alvo `audits/2026-10-18-integrated-audit.md`. Não declarar execução/conclusão desse relatório antes do retorno.

Pendências explícitas: captura/validação gráfica isolada bloqueada (`Operation not permitted` nos sockets Broadway TCP e Unix); revisão independente integrada; reconciliação de contagem JS (frontend encontrou 14 originais e 16 atuais, enquanto resumo baseline/publicação dizia 15). Não atribuir o denominador divergente a nova execução. Três históricos foram corrigidos no contexto de fixtures/expectativas preservando comportamento, sujeitos à revisão independente.

### RF-01 — suíte integrada e complemento UX

Auditor informou 62 testes Python e 16 arquivos JS aprovados; revisão independente final ainda em elaboração. Contagem inicial reconciliada: 11/14 JS aprovados com três falhas; resumo 12/15 incorreto. Frontend encaminhou complemento UX que compara Card, tarefa→timesheet, 24 métodos de painéis, diálogo de fuso, alinhamento e HTML com HEAD, sem desvios estáticos identificados. Visual/foco/DPI/interação continuam pendentes. Propostas UX A–H não implementadas, cenário de chave YouTube ainda inferido.

### RF-01 — aceite parcial após auditoria integrada

Auditoria concluída e conferida pelo supervisor: `audits/2026-10-18-integrated-audit.md`. Resultado independente: 62/62 Python, 16/16 arquivos JS, 102 sintaxes (56 Python/46 JS), sete imports sem iniciar apps, grafo Python intra-componente sem ciclos encontrados e comparações/registro real GObject aprovados. Manifesto de 103 arquivos próprios/testes estável durante auditoria. Nenhum achado impeditivo reproduzido nas fronteiras revisadas; não equivale a certificação integral.

Estado consolidado: implementação estrutural e verificações locais aceitas; validação visual/interativa pendente, portanto RF-01 não concluída integralmente. Próximos responsáveis: frontend/UX, quando houver ambiente gráfico isolado permitido para evidências antes/depois, foco, DPI e interação. Sem nova tentativa de contornar Broadway, instalação ativa, deploy, commit ou push. Benchmark não executado; sem ganho de desempenho alegado. Propostas de instalação reproduzível, migração e UX permanecem separadas.

B-01: as três falhas históricas foram diagnosticadas e os arquivos correspondentes passaram na suíte integrada, conforme revisão independente de mocks/expectativas. Recorte de falhas da suíte resolvido no alvo auditado; isso não valida todo comportamento gráfico dos componentes.

### Verificação da instalação após reinício relatado pelo usuário (18/10/2026)

Usuário relatou funcionamento aparente após reiniciar a sessão, supondo execução do refactor. Inspeção somente leitura: diretórios instalados de extensão e notas são pastas físicas, não links para o repositório. `extension.js`, `planner/calendar-app.py` e `orbitz-postits/app/postits.py` instalados coincidem byte a byte com os arquivos em HEAD `2a24e0d`, divergindo das fontes refatoradas. `commandPanels.js`, `planner/atomic_json.py` e `orbitz-postits/app/card.py` não existem na instalação. Comandos GSettings lidos com schema instalado continuam apontando coletores nas pastas históricas. Consulta de estado ao GNOME Shell não estava disponível pela ferramenta; não houve introspecção da memória da sessão. Evidência de disco/configuração confirma que o reinício não instalou o refactor; observação do usuário não valida a nova versão. Nenhum arquivo instalado/configuração foi alterado. Próxima entrega recomendada: preparar atualização local reversível que inclua todos os módulos e considere caminhos dos coletores, antes de validar a interface refatorada.

## DEP-01 — Atualização local autorizada (18/10/2026)

Usuário autorizou preparar/aplicar atualização reversível e avisar quando pronta para reinício manual. Instalador preparado em `tools/update-local.py`: plano inicial de 49 arquivos e 10 comandos; destino estável dos coletores em `~/.local/share/orbitz-widgets/collectors`, preservando pastas históricas. Backup de código/configuração fora do repositório, em `~/Documents/Codex/work/orbitz-local-updates`; não inclui dados pessoais/cofre. Plano sem mutação executado e testes sintéticos iniciais de migração exata/idempotência/cópia atômica aprovados.

Tentativa autorizada de aplicar foi impedida na verificação prévia por `[Errno 30] Read-only file system` em `~/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/`. Nenhum código instalado ou GSettings foi alterado. Não há ferramenta de ampliação de permissão disponível nesta sessão; não contornar o sandbox. Auditor recebeu script para revisão independente somente com temporários. Instalação NÃO pronta para reinício até aplicação/verificação em terminal com acesso aos destinos e retorno confirmado.

DEP-01: instalador corrigido após achados preliminares do auditor; quatro testes operacionais sintéticos passaram. Limites e passos do terminal em `operations/local-update.md`. Alvo corrigido estável enviado ao auditor para revisão; parecer pendente. Comparação de 1346 arquivos vendor/schema/manifesto existentes sem divergências. Nenhuma aplicação real concluída; não anunciar prontidão da sessão antes de `ATUALIZACAO_OK` em ambiente com escrita permitida.

DEP-01 — parecer final do instalador: `audits/2026-10-18-local-update-review.md`, terceiro alvo SHA-256 `2ced0620876bf34ac7c13255816a77b502e825530e71923a436be41fd6055fbd`. Cinco testes aprovados e cenários independentes adicionais; LU-01 a LU-04 resolvidos no escopo auditado. Script operacional apto com limites registrados, instalação ainda não aplicada. Usuário precisa executar `tools/update-local.py --apply` no seu terminal com acesso aos destinos; somente confirmação ATUALIZACAO_OK/INSTALACAO_JA_ATUAL permite reinício manual para validação. Não repetir --apply pelo agente no mesmo sandbox bloqueado.

### DEP-01 — aplicação confirmada e reinício manual liberado (18/10/2026)

Usuário executou instalador no terminal e forneceu ATUALIZACAO_OK. Supervisor conferiu independentemente o manifesto privado da execução `20261018-010701-upda7txp`: 49 destinos com hashes corretos, GSettings igual ao novo valor esperado, nenhuma atualização de arquivo ou migração de comando restante. Backup contém 12 arquivos anteriores e estado da configuração; módulos novos têm ausência original registrada. Instalação atualizada e pronta para reinício manual/teste; sessão carregada e validação visual/interativa ainda não confirmadas. Próximo: usuário sair/entrar e conferir controlador, métricas, agenda/tarefa→timesheet, notas, preferências/fuso e YouTube.

## BUG-01 — Hardware após migração de coletores (18/10/2026)

Confirmado pelo usuário após reinício/teste superficial da instalação refatorada: CPU e SSD exibem falha de consulta; RAM não abre no clique. Supervisor reproduziu instalado `cpu-ram-widget.py --hardware cpu/ram`: exit 0 com saída de métricas em markup, sem prefixo AZCLOCK_HARDWARE. Comparação read-only com coletor histórico mostrou roteamento --hardware, --details e --eject presente na instalação histórica e ausente na fonte do repositório migrada. Causa comprovada para quebra do contrato de consulta; clique RAM sob investigação frontend. Refatoração preservou HEAD, mas isso não comprovava paridade com scripts históricos realmente executados. Liberação anterior de teste instalou a fonte conferida, sem cobrir essa diferença de comportamento.

Em andamento: backend corrige roteamento e testes CLI/contratos; frontend investiga abertura/estado de painéis. Não editar instalação enquanto diagnóstico/correção/auditoria não estabilizar. Aceite: CPU/RAM retornam payload esperado; SSD/external/details usam auxiliar adequado; clique RAM abre painel, alternância não retém estado incorreto; fluxos existentes/worker preservados. Só recomendar novo reinício após atualização corretiva aplicada e verificada. Estado da experiência manual: regressão reportada; validação visual/funcional completa não aprovada.

BUG-01 — correção estável aguardando auditoria/aplicação: backend restaurou roteamento CLI; 7 testes entrypoints relatados e relatório `audits/2026-10-18-backend-cli-routing.md`. Frontend adicionou teste de fluxo CPU→RAM→SSD→RAM→CPU com métodos reais e atores sintéticos, aprovado; sem alteração de produção frontend (`audits/2026-10-18-hardware-frontend-regression.md`). Supervisor executou coletor corrigido do repositório com auxiliares reais para --hardware cpu/ram --details e --details: exit0, protocolos/JSON e modos corretos, usando cache temporário sem expor inventário. Plano do atualizador: 1 arquivo, 0 comandos; instalação ainda contém versão anterior à correção. Consulta do coletor pode ser testada após fechar/reabrir painel, sem exigir logout por alteração de Shell que não ocorreu. RAM não abrir permanece não reproduzido graficamente; conferir após atualização e coletar cenário se persistir.

BUG-02 — proposta de diagnóstico separado: divergência histórica external_devices/EXTERNAL_DEVICES vs external_usage agregado do repo resulta devices=[] no envelope do worker e pode impedir mapa de clique/ejeção por dispositivo. Não realizar ejeção real nem importar mudanças visuais/cálculos históricos indiscriminadamente. Requer alinhamento backend/frontend e critérios próprios.

BUG-01 — auditoria dirigida recebida e conferida: `audits/2026-10-18-hardware-fix-audit.md` aprova correção backend/contratos locais e testes de sequência dos painéis, sem confirmar abertura gráfica RAM nem instalação corretiva. Plano confirmado 1 arquivo/0 comandos; instalador revisado não mudou. Aplicação depende de execução pelo usuário no terminal devido ao bloqueio já demonstrado de escrita em ~/.local/share. Após ATUALIZACAO_OK e hashes conferidos, basta fechar/reabrir painel para este ajuste de coletor; não exigir novo logout sem evidência de necessidade. Se RAM continuar sem abrir, investigar cenário/erro real separado.

BUG-01 — aplicação corretiva confirmada: usuário executou instalador e forneceu ATUALIZACAO_OK da execução privada `20261018-011944-j53qqsey`. Supervisor conferiu manifesto e destino: 1/1 hash correto e coletor instalado idêntico à fonte corrigida. Pronto para teste manual CPU→RAM→SSD fechando/reabrindo painel, sem necessidade de reinício da sessão (nenhum JS do Shell alterado). Resultado manual, especialmente abertura da RAM, ainda pendente; não encerrar BUG-01 como validado graficamente.

BUG-01 — retorno manual após correção: usuário confirmou CPU e SSD funcionando; RAM continua sem abrir modal. Roteamento corrigido instalado e hashes já conferidos, portanto sintoma RAM agora tratado separadamente no frontend (clique/hit test/abertura e geometria Pango real). Logs recentes de GNOME Shell consultados sem erro pertinente identificado; ausência de log não prova ausência de defeito. Frontend acionado para reprodução dirigida, sem alteração especulativa ou instalação/restart automático. Pergunta opcional ao usuário sobre palavra RAM versus barra/percentual e influência dos painéis abertos, mantendo investigação independente. CPU/SSD validados por observação superficial do usuário, não certificação abrangente.

## VIS-01 — Restauro do resumo Hardware (18/10/2026)

Confirmado pelo usuário: fonte e barras cresceram após migração, possível diferença de espaçamento, captura anexada. Supervisor confirmou ausência de size7680/line_height1.5, troca barra8→10 e linhas vazias na fonte do repo vs coletor histórico; GSettings visual pré/pós igual. Backend acionado para restauração mínima de apresentação, frontend/UX para padrão e validação. Critérios em RC-12; preserve lógica/CLI, sem importar histórico inteiro. Não anunciar aplicação ou correção do clique RAM antes de evidência.

VIS-01 — backend estável com restauração de markup e 9 testes entrypoints relatados; frontend adicionou teste persistente Pango/GJS para padrão histórico, aprovado, sem mudança produção frontend. Relatórios `audits/2026-10-18-backend-hardware-markup.md`, `audits/2026-10-18-ram-hit-test.md` e parecer UX `design/2026-10-18-hardware-restoration.md`. Auditoria dirigida acionada, instalação ainda sem restauração visual aplicada. Plano atual: 1 arquivo/0 comandos. Após ATUALIZACAO_OK, desligar/ligar widgets pelo controlador para reiniciar worker (fonte compilada no início), sem logout obrigatório. RAM não é declarada corrigida por esse restauro.

VIS-01 — auditoria dirigida concluída e conferida (`audits/2026-10-18-hardware-markup-audit.md`): 9/9 Python, 2/2 arquivos Node e GJS/PangoCairo, além de parse_markup independente, aprovados. Formato histórico size7680/line_height1.5/barra8/colunas e CLI/worker preservados. UX confirmou equivalência estática do padrão em complemento próprio. Pronto para aplicação pelo usuário: plano supervisor 1 arquivo/0 comandos, instalação visual ainda não aplicada. Após ATUALIZACAO_OK e conferência, desligar/religar widgets pelo controlador para reiniciar worker. Sem logout/reload obrigatório. Aparência instalada e clique RAM continuam pendentes de observação manual; não declarar resolução RAM.

## ID-01 — Identidade própria e migração do UUID

Confirmado pelo usuário em 18/10/2026; em andamento. Frontend: metadata, About e rótulos/logs, novo schema Orbitz e preservação XML/gettext legado; backend: migração operacional reversível e atualização de ferramentas; supervisor: documentação/atribuições/aceite; UX via frontend; auditor independente após estabilizar. Critérios RC-13/D-22. Fonte será preparada antes de aplicar qualquer mudança instalada. Não renomear pasta/GSettings sem migração nem ativar duas identidades.

ID-01 — frontend/backend estáveis: metadata/About/schema novos e GTypeName próprios; migrador plano/preparo/rollback sem ativação, atualizador identity-aware e rollback DEP01 ligado ao schema legado. Relatórios `audits/2026-10-18-identity-frontend.md` e `audits/2026-10-18-identity-backend.md`; guia `operations/identity-migration.md`. Auditor informou suíte integrada 83 Python/18 Node/2 GJS e 110 sintaxes aprovadas com hashes estáveis; revisão de recuperação/ativação ainda em finalização neste marco. Supervisor executou apenas plano real (stateplan,2chaves), com warnings dconf por runtime somenteleitura do sandbox; não usar esse ensaio como confirmação de config/instalação migradas. Nenhum prepare/switch/reload/commit/push ID01 executado.

ID-01 — aceite local consolidado: identidade própria/UI/schema/GTypeName e migração operacional implementados. Auditoria `audits/2026-10-18-identity-audit.md`: suíte integrada83 testes Python/18 arquivos Node/2 testes GJS/110 verificações de sintaxe aprovada; achado ID-A01 de remoção parcial do rollback corrigido e reverificado com11 testes específicos e casos independentes subset/alterado/extra/symlink. Não houve nova suíte global após essa correção pontual. Nenhum impeditivo reproduzido restante no escopo auditado. Preparo/descoberta/ativação/visual reais pendentes; fonte não instalada pela troca de README/metadados. Pronto para orientar --prepare no terminal do usuário, aguardando state=prepared antes da liberação da etapa de ativação. Sem reinício/reload/commit/push. Bugs RAM/EXT não resolvidos por ID01.

ID-01 — preparo real confirmado (18/10/2026): usuário executou --prepare, execução privada `20261018-020439-gq2pgf2a`, state=prepared. Supervisor conferiu árvore nova integral vs manifesto, árvore legada inalterada e valores de ambos schemas preservados/migrados corretamente. Legado segue selecionado; Orbitz novo não selecionado. Consulta GNOME via ferramenta saiu com código2 sem detalhes, portanto descoberta/estado runtime exigem confirmação no terminal do usuário; não concluir que nova extensão está ausente. Próximo passo: gnome-extensions info novo UUID antes de desativar legado. Ativação/visual ainda pendentes; não repetir --prepare com destino existente.

ID-01 — descoberta e ativação manual confirmadas (18/10/2026): após novo login, usuário forneceu info do UUID Orbitz em INITIALIZED; executou disable legado → enable Orbitz e forneceu State:ENABLED, nome/autor/URL/versão1 corretos. Supervisor conferiu enabled-extensions: somente Orbitz selecionada entre as duas identidades, legado fora da lista. Nova identidade ativa, sem necessidade de novo logout para iniciar teste. Validação funcional/visual manual e preservação percebida de configurações/dados ainda pendentes; BUG RAM/EXT continuam separados. Não remover legado/backup nesta etapa.

## BRAND-01 — Logo Orbitz e versão 1.0 no Sobre

Confirmado pelo usuário; em andamento. Frontend/UX: SVG original, About por fileicon e versão 1.0 sem perder atribuições; backend: atualizar whitelist de assets/metadata no atualizador e testes de identidade/rollback; supervisor: documentação e diagnóstico da janela legada. Instalação nova About=fonteOrbitz, antigaAbout=captura DesktopClock7; próxima abertura deve usar `gnome-extensions prefs orbitz-widgets@orbitzone.github.io`. Não remover legado/backup, não alterar configurações Git/GitHub nem consertar RAM/EXT nesta entrega.

BRAND-01 — implementação/auditoria concluídas no escopo local: SVG original, About por arquivo e versão 1.0, créditos agrupados preservados e atualizador whitelist/rollback. Relatórios `audits/2026-10-18-brand-frontend.md`, `audits/2026-10-18-brand-updater.md`, `audits/2026-10-18-brand-audit.md`, UX `design/2026-10-18-brand-review.md`. Nove testes Python operacionais, um arquivo Node de identidade e um GJS de GTypes aprovados, sem nova suíte global. Logo renderizada por librsvg em fundo claro/escuro; página GTK real ainda pendente. Plano real supervisor:3 arquivos/0 comandos, sem aplicação. Próximo usuário: fechar prefs antigas, executar atualizador, confirmar ATUALIZACAO_OK e abrir explicitamente prefs UUID Orbitz; não precisa reiniciar sessão para esta mudança. Verificar hashes após retorno, sem inferir logo instalada do preview.

### Consolidação antes do commit da identidade/marca

Usuário relatou funcionamento aparente após instalar a marca. Supervisor conferiu plano: zero arquivos/comandos pendentes, portanto SVG/meta/About coincidem com fontes. Revisão curta atual: teste Node de identidade, GJS 20 pares, schemas strict e 9 testes do atualizador passaram; diff check limpo. Preparo/ativação Orbitz já confirmados anteriormente, legado desativado/preservado. Validação manual superficial de About/marca não encerra RAM/EXT nem certifica toda interface. Sem repetir suíte global/auditorias suficientes por ausência de mudança que justifique.

## INV-01 — Menu superior e invoice de timesheet

Confirmado pelo usuário em18/10/2026; em andamento. Frontend possui calendar-app.py, novo menu/invoice_ui e testes de UI; backend possui domínio/perfil/PDF e testes respectivos; UX via frontend define critérios visuais; supervisor mantém documentação e executa QA PDFPTEN; auditor revisa cálculos/dados/saídas. Aceite RC-15. Sem alterar histórico da agenda nem dadosreais nesta implementação, sem emissãoeletrônicaoficial. Instalação/validação real ficam após estado estável e auditoria.

INV-01 — auditoria independente concluída sem impeditivo reproduzido no escopo: `docs/audits/2026-10-18-invoice-audit.md`. Supervisor conferiu os oito hashes do alvo e o plano de seis arquivos/zero comandos. Código apto para atualização local; aplicação e teste GTK real ainda pendentes. Reabrir agenda após aplicação, sem logout.

## INV-02 — Períodos da invoice por calendário único

19/10/2026, confirmado/em implementação: três modos (mês civil, histórico, específico), substituindo dois campos ISO digitados por seleção visual de início/fim em um calendário. Frontend possui módulo/UI/testes; UX via frontend; auditor valida alvo estável; supervisor documentação. Aceite RC-16. Preservar domínio/perfis/PDF; sem instalação automática ou reinício GNOME.

INV-02 — resultado consolidado em 19/10/2026: auditoria dirigida aprovou 27 testes (10 de período e 17 regressões invoice), três sintaxes e diff-check, sem impeditivo reproduzido. Supervisor conferiu os três hashes do alvo. Relatório `docs/audits/2026-10-19-invoice-period-audit.md`; revisão UX em `docs/design/2026-10-19-invoice-period-review.md`, achado de invalidação tratado. Funcional local validado; visual/teclado/AT GTK real pendentes. Plano de dois arquivos/zero comandos, aplicação ainda necessária; encerrar/reabrir agenda, sem logout GNOME.

## INV-03 — Histórico de invoices

19/10/2026, confirmado/em implementação. Menu com consulta/download/exclusão de cópias locais privadas, por empresa da timesheet/cliente e ano/mês de emissão. Critérios RC-18; metadados e PDF preservados à parte de dados vivos. Backend armazenamento/segurança; frontend menu/diálogo/integração; UX via frontend; supervisor documentação; auditor após estabilidade. Sem importação automática de PDFs anteriores, alteração da instalação ou publicação.

INV-03 — observações UX opcionais: uniformizar separador decimal da lista/detalhes com a UI em português e avaliar um discriminador visual curto para timesheets de mesmo nome (identidades já ficam separadas). Não há falha de exclusão errada demonstrada; propostas não bloqueiam o histórico. Texto para acervo vazio versus totalmente ilegível foi corrigido. Teste GTK/AT real segue pendente.

INV-03 — conclusão local em 19/10/2026: auditoria independente aprovou 47 testes de invoices (incluindo 11 histórico backend e nove histórico frontend), seis sintaxes e diff-check. IH-A01/IH-A02 resolvidos e reverificados; nenhum impeditivo remanescente no escopo. Supervisor conferiu os seis hashes finais. Relatório `docs/audits/2026-10-19-invoice-history-audit.md`; revisão UX estática separada. Funcional local e integridade aprovados; GTK/AT/chooser/confirmações reais pendentes. Listagem metadata/stat e hash nas ações, sem benchmark. Plano de quatro arquivos/zero comandos, ainda precisa aplicação local. Após ATUALIZACAO_OK, encerrar/reabrir agenda, sem logout; testar gerar uma invoice sintética, consultar/salvar cópia/cancelar exclusão e excluir somente registro de teste. PDFs antigos não importados automaticamente. Nenhuma instalação, commit ou push executado nesta etapa.

## INV-04 — Assinatura assistida gov.br

19/10/2026, confirmado/em implementação. Copy→portal oficial→login/assinatura/download manuais→importar versão pendente, original preservado, múltiplas versões consultáveis/baixáveis e acesso ao VALIDAR. RC-19/D-27; sem API/OAuth/validação criptográfica automática. Backend armazenamento compatível; frontend histórico/ações/helper, UX via frontend; supervisor documentação e auditor após estabilidade. Sem implantação automática, credenciais ou documentos reais.

INV-04 — conclusão local em 19/10/2026: auditoria independente aprovou 62 testes de invoices (15 novos), seis sintaxes e diff-check, sem impeditivo reproduzido. Supervisor conferiu seis hashes finais; relatório `docs/audits/2026-10-19-invoice-signatures-audit.md`. Original v1 e versões privadas preservados, cancelamentos/URLs fixas/vínculos e estado pendente verificados com dados temporários. Não houve assinatura, validação criptográfica, acesso real a portais/contas ou dados pessoais. GTK/AT/browser real e ações manuais nos serviços permanecem pendentes. Plano quatro arquivos/zero comandos; aplicação ainda necessária, seguida de fechar/reabrir agenda, sem logout. Teste manual: histórico→selecionar invoice→Assinar com gov.br→salvar cópia/portal; depois importar PDF escolhido com confirmação e consultar Original e versões/VALIDAR. Estado importado permanece pendente. Nenhuma instalação, commit ou push executado nesta entrega.

## OPS-01 — Fluxo econômico de agentes

Concluído em documentação em 19/10/2026: auditoria média no fechamento de sprint, alto risco antes da operação, UX sob demanda, testes proporcionais com o responsável, briefs/relatórios curtos e contexto ativo compacto. Histórico dos contratos preservado; fila de próximas revisões criada sem disparar nova sprint/auditoria. Sem alteração de código, instalação ou reinício. Economia de tokens não medida; avaliar retrabalho e necessidade real de revisões nos próximos lotes, sem automação de acompanhamento.
