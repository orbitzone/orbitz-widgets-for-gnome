# Backlog e próximas entregas

Registro inicial: 17/10/2026; estado atual revisado em 21/10/2026. A tabela original e os marcos históricos são preservados abaixo; o resumo atual prevalece para andamento. Prioridades propostas não constituem aprovação comercial. O agente trabalha quando acionado, sem monitoramento contínuo.

## Resumo atual

- OPS-01 (19/10/2026): fluxo econômico vigente em `docs/agents/workflow.md`; fila consolidada em `docs/sprint-backlog.md`. Esta política prevalece sobre acionamentos por tarefa descritos nos marcos históricos abaixo.

- INV-01: menu e invoice PDF PT/EN implementados; 17 testes novos e oito regressões planner aprovados na auditoria dirigida. QA visual de quatro páginas sintéticas aprovada; aplicação local e teste GTK real pendentes.

- RF-01: implementação e auditorias locais concluídas, validação gráfica/interativa integral pendente; não declarar conclusão integral.
- B-01: falhas históricas de testes resolvidas e verificadas; baseline corrigida 11/14 JS, suíte atual 17/17 Node aprovada.
- DEP-01: atualização local e rollback implementados/auditados; instalação conferida, plano zero arquivos e zero comandos pendentes. Não equivale a pacote de instalação limpa.
- VIS-01: padrão histórico implementado/auditado e arquivo instalado coincide com a fonte atual; aparência real após restauro ainda requer confirmação manual.
- BUG-01: encerrado por confirmação manual do usuário em 20/10/2026: o clique RAM não é mais um problema; CPU e SSD já haviam sido confirmados funcionando. Isso registra o resultado observado, sem alegar certificação gráfica ampla.
- BUG-02: diferenças históricas de dispositivos externos e alertas permanecem para análise própria, sem mudança semântica nesta entrega.
- B-02/B-03: há atualizador local e comandos migrados; distribuição/reinstalação limpa e consolidação integral ainda não validadas.
- CAL-06/07: o usuário confirmou que Google Calendar e Brasil · Datas comemorativas funcionaram após a atualização. Testes dirigidos registrados: CAL-06 18; CAL-07 31 mais regressão de dados externos. Calendly com conta real permanece sem confirmação; revisão independente média segue para fechamento da sprint.
- FX-01 e I18N-01: o conversor fiat/cripto está implementado na fonte com modal manual/inversão e polling de 4h; Fiat usa duas casas arredondadas e USD→cripto preserva frações pequenas. A configuração e a reconstrução em execução foram corrigidas, assim como gravação após renomear, descarte de respostas antigas e erros de JSON numérico extremo/inteiro excessivo. Backend usa CoinPaprika sem chave; catálogo cobre somente ativos precificados disponíveis no plano e atribuição fica na modal. O plano gratuito é pessoal; uso comercial voltado a clientes exige licença compatível. Testes dirigidos FX 24/24 passaram; teste GNOME/GTK visual e instalação desta revisão ainda pendentes. Idioma PT-BR/EN-US aguarda inventário das interfaces.
- STICKY-01: após novo pedido em 20/10, a política passou a `AUTOMATIC`: a barra translúcida aparece somente quando há overflow e some para notas curtas como “test 2”. Trilha transparente e altura natural contida foram preservadas. Quatro testes passam; smoke geométrico GTK e conferência visual/rolagem na instalação seguem pendentes.
- STICKY-02: Ctrl+clique abre caminhos locais existentes (arquivos abrem a pasta contêiner), URLs HTTP/HTTPS e e-mails mailto pelos aplicativos padrão; enquanto Ctrl está sobre destino válido, link fica em negrito e cursor vira pointer. Dez testes sintéticos e validação de sintaxe passaram; teste gráfico de aparência/abertura real pendente.
- STICKY-03: área de redimensionamento da nota ampliada para 28×28 px junto ao canto inferior direito, com cursor `se-resize` em toda a área; conteúdo tem margem inferior para evitar sobreposição. Quatro testes de contrato/gesto passaram; geometria e arraste GTK reais pendentes.
- WID-01: unificar os widgets separados do desktop em um único widget chamado Workspace, conforme pedido de 20/10/2026. Inventário do escopo e compatibilidade de configurações pendentes; não priorizado para sprint.
- WID-02: NÃO RESOLVIDO conforme relato do usuário em 20/10/2026. O requisito é que a escolha de fuso esteja acessível também no relógio digital e seja um dropdown completo com região/cidade, em vez de campo de texto. Há uma tentativa de implementação no checkout, mas o comportamento na interface do usuário não foi confirmado e não deve ser tratado como entregue; manter como pendência para retomar depois. Validação visual/aplicação continuam pendentes.
- CLOUD-01 (baixa prioridade/P3 proposta): incluir Google Drive e Zoho WorkDrive como itens de menu, com consulta de arquivos dentro do Orbitz e abertura local para formatos compatíveis. Autorização inicial OAuth pode usar browser; não pedir senha da conta nem exigir browser para navegação cotidiana. Escopo, formatos e permissões mínimos a definir.
- INT-01: criar aba Integrations ao lado de Settings e About como ponto central de estado e gestão de integrações, API keys, certificados e tokens; credenciais mascaradas e guardadas no cofre seguro. Prioridade ainda não definida.
- INV-01–04/WSP-01: GTK real de histórico/versões, chooser e fluxo de assinatura continua pendente; a auditoria funcional/PDF sintético não substitui esse teste.
- Revisão de 21/10/2026: ver evidências, correções e pendências atuais em `docs/sprint-backlog.md`. Alterações na fonte não foram instaladas por esta revisão; validar em GNOME real permanece separado dos testes automatizados.

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

Atualização em 20/10/2026: usuário informou que o clique da RAM não é mais um problema. Encerrar BUG-01 por confirmação manual, limitada ao comportamento observado pelo usuário.

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

## CAL-04 — diagnóstico de falha após retorno Google (19/10/2026)

Observado: usuário chegou à página local “Autorização recebida”, mas conexão não foi concluída; inspeção limitada de metadados locais confirmou zero contas Google salvas. Callback não comprova troca de tokens/discovery/cofre. Mensagem exata do aplicativo solicitada, aguardando. Melhorar diagnóstico limitado por código OAuth conhecido sem incluir corpo remoto, error_description, tokens ou códigos. Não atribuir falta de secret/consentimento/cofre sem evidência. Configuração/autenticação permanecem pendentes de teste real.

CAL-04 atualização do usuário: o Orbitz permanece aguardando autorização, botão inativo, sem erro visível. A resposta anterior com “Google não verificou” era do navegador. Investigar callback antes de concluir causa; hipótese técnica testável: estado recebido atribuído depois de escrever a resposta pode ser perdido se a escrita falhar. Acrescentar progresso fixo por etapa e erros seguros, mantendo cancelamento/ACK e sem permitir tentativas concorrentes artificiais.

CAL-04: fontes corrigidas e revisão focada concluída; bug BrokenPipe foi reproduzido, mas causa única da tentativa real não certificada. Reteste manual pendente após atualização4arquivos; se persistir, coletar etapa/mensagem exibida no Orbitz sem credenciais. Evidência no parecer CAL-04.

## CAL-05 — Parâmetro ausente no cliente OAuth (19/10/2026)

Instalação atual conferida; probe público sem código válido confirmou invalid_request/client_secret ausente. Completar configuração do mantenedor localmente sem JSON no fluxo normal e sem versão do segredo; ferramenta privada + diagnósticos/testes. JSON Desktop será baixado pelo usuário; autorização real posterior pendente. Esta evidência substitui a hipótese de simples expiração/reinstalação.

CAL-05 evidência adicional: arquivo Desktop indicado pelo mantenedor foi validado localmente sem mostrar valores, ID correspondente e parâmetro presente. Segundo probe oficial com a configuração completa e o mesmo código fictício retornou invalid_grant, sem erro de parâmetro ausente. Isso confirma remoção do bloqueio de configuração, não autenticação/grant real. Preparação privada/testes/revisão em andamento; não inserir arquivo real, valores ou caminho pessoal na documentação.

CAL-05 fechamento local: configuração privada do mantenedor preparada/check OK após permissão,35 testes/6 adversos e revisão sem impeditivo. Duas fontes instaladas ainda precisam atualização; reteste do login pendente. Não confundir preparação local com release público ou autenticação concluída.

## CAL-06 — Conteúdo dos dias marcados

Confirmado Google login/sincronização inicial pelo usuário; manter limites de casos não testados. Corrigir assimetria calendário/Agenda para feriados de outras fontes e atividades locais, distinguir seleção, melhorar legenda/tooltip. Ajuda opcional de ativação Calendar API do projeto para mantenedor. Frontend/testes em andamento; risco médio, revisão no fechamento.

CAL-06 implementado nas fontes com18 testes direcionados aprovados. Motivos das marcações alinhados ao conteúdo da Agenda; seleção distinguida e ajudaAPIopcional adicionada. Em 20/10/2026 o usuário confirmou que a integração Google Calendar funcionou na instalação atual. Essa confirmação cobre o fluxo usado, não todas as contas ou o Calendly. Revisão média agrupada permanece pendente.

## CAL-07 — Fonte padrão reativável

RC-29: Brasil·Datas comemorativas permanente em Gerenciar, toggle persistente, restauração do cadastro excluído, sem duplicação de assinatura legada; inativa não participa de fonte/sync/marcação. Backend/Frontend em paralelo com contrato alinhado, sem credenciais ou dados reais. Risco médio, revisão agrupada.

CAL-07 fontes e testes locais concluídos:31 testes dirigidos e regressão externa. Em 20/10/2026 o usuário confirmou que a fonte Datas comemorativas funcionou na instalação atual. A persistência do ciclo desativar→reabrir→reativar não foi explicitamente confirmada. Revisão média consolidada continua pendente no fechamento da sprint; reusar os testes documentados e não repetir a suíte sem mudança/falha concreta.

Proposta futura (fora CAL-07): guarda enabled em consumidores de alertas para fontes desativáveis que tenham eventos com horário. A fonte pública brasileira atual é de dia inteiro e já não produz alertas temporizados; não ampliar esta entrega nem exigir reload GNOME por hipótese.

## FX-01 — Widget único de conversão fiat/cripto (20/10/2026; escopo unificado em 21/10)

Solicitado pelo usuário; implementação fiat parcial e saída simplificada aplicada à instalação em 20/10. `widgets/fx_rates.py` usa a rota latest da Frankfurter v2; preset, catálogo pesquisável e inversão existem nas configurações. Na fonte atual, polling foi alterado de 1h para 4h, inclusive override runtime para widgets preexistentes; modal acionável pelo widget oferece atualização manual e inversão persistida. Verificações dirigidas Python/Node, sintaxe e diff-check passaram. A instalação dessas mudanças e a inspeção GTK/GNOME ainda estão pendentes; o usuário confirmou anteriormente que o widget apareceu, mas não a persistência da nova modal/cadência após reabrir. O widget mostra somente par e valor; Frankfurter publica referência diária em dias úteis, não preço em tempo real.

Escopo fiat confirmado: seleção de moeda fiduciária ofertada pela fonte, BRL → destino e inversão destino → BRL; preservar seleção/direção. Usar sempre a taxa mais recente disponível, sem previsão, busca de histórico ou fallback de valor antigo como atual. Modal acessível pelo widget com ação “Atualizar agora” e seletor/direção; polling automático em 14.400.000 ms. Em uso normal, renderizar apenas a conversão, sem metadados, com duas casas decimais arredondadas metade para cima (`0.19829 → 0,20`). Valores Fiat menores que `0.005` aparecem `0,00`. Esse arredondamento não se aplica à cotação USD→cripto: a taxa fornecida é exibida com precisão suficiente para não zerar ativos pequenos. A Frankfurter pode devolver o mesmo valor em várias consultas de quatro horas porque publica referência diária em dias úteis. Não aplicar limite estrito que rejeite automaticamente fins de semana/feriados; validar data internamente e nunca contornar indisponibilidade buscando datas históricas.

Escopo atualizado pelo usuário em 21/10: fiat e cripto devem ser modos do mesmo widget **Conversor de moedas**, sem widget Bitcoin separado. Em modo cripto, USD → BTC é o padrão; permite selecionar ativo por nome/símbolo/ID estável e inverter para ativo → USD. Em modo fiat, preservar BRL → USD inicial, seleção/inversão de moedas, modal manual e polling automático de 4h. A lista cripto representa os ativos cotados e disponíveis no plano da fonte, não todas as criptomoedas existentes; IDs evitam colisões entre símbolos. Sem chave compartilhada.

Implementação atual na fonte: backend `widgets/fx_rates.py` e `widgets/currency-widget.py` consultam tickers CoinPaprika sem chave, validam data recente (máximo 1h), preço e identidade do ativo, sem cache/fallback; CLI conserva o contrato fiat e acrescenta `--mode crypto`, `--asset`, catálogo/resultado JSON. Frontend adiciona seletor Fiat/Crypto e controles de ativo/direção no mesmo Command Label, atribuição da fonte na modal e mantém atualização manual/cadência de 4h. A falha de Configure observada foi reproduzida: libadwaita 1.1 não oferece `Adw.SwitchRow`; foi substituído por `Gtk.Switch` dentro de `Adw.ActionRow`. No fluxo efetivo, um callback assíncrono do catálogo podia sobrescrever `ElementAdded` antes do debounce do Shell; agora o frontend preserva marcadores estruturais pendentes e compara a topologia salva com os elementos já criados. A revisão encontrou ainda que renomear invalidava o seletor e respostas antigas podiam substituir uma cotação após mudança de modo; ambos foram corrigidos com testes de lifecycle. O formatador agora preserva taxas pequenas no destino cripto. Os testes direcionados Python e JS passaram; validação gráfica GNOME e instalação ainda pendentes.

Limitação importante: a fonte CoinPaprika sem chave declara o nível gratuito para uso pessoal e exige plano/licença apropriada para redistribuição comercial dos dados. Portanto esta escolha técnica não autoriza apresentar o feed como liberado para uso comercial ou distribuição a clientes. Reavaliar provedor/licença antes de qualquer lançamento comercial; não embutir credenciais compartilhadas.

Critérios de aceite restantes: uma única entrada “Conversor de moedas”; Configure abre a página fiat/cripto em libadwaita 1.1/GNOME 42; escolha de categoria, ativo e direção persiste após reabrir; cálculo correto em ambos os sentidos; refresh manual consulta sem esperar timer; polling 14.400.000 ms; erros não mostram preço anterior como atual; precisão cripto própria preserva ativos baratos; atribuição CoinPaprika fica visível quando o modo cripto está ativo. Teste GTK/GNOME visual, instalação e conferência do usuário continuam pendentes.

## I18N-01 — Idioma PT-BR / EN-US em toda a interface (20/10/2026)

Solicitado pelo usuário; ainda não priorizado para uma sprint. Incluir seletor de idioma nas Settings, no canto superior esquerdo e na mesma linha do botão Add Widget à direita. Oferecer Português (Brasil) e English (United States), persistir a preferência e aplicar o idioma à interface do Orbitz.

Critérios para implementação: externalizar as strings atualmente em português para o catálogo PT-BR e fornecer traduções EN-US; cobrir toda interface mantida pelo Orbitz — preferências/settings, Orbitz Workspace, widgets e aplicações próprias, diálogos, mensagens de erro, estados vazios, tooltips, nomes acessíveis e notificações. Não traduzir conteúdo escrito pelo usuário nem nomes/textos vindos de serviços externos. Verificar ausência de strings da interface no idioma errado, expansão do texto, navegação e apresentação de datas/números por locale, preservando os dados armazenados.

Decisões pendentes: inventário dos componentes abrangidos, formato/caminho dos catálogos compatível com GJS, Python e GTK, comportamento após trocar idioma (imediato ou reabrir) e locale inicial para instalações existentes. Manter PT-BR como comportamento padrão na migração, salvo decisão posterior do usuário.

## STICKY-01 — Acabamento visual da nota adesiva (20/10/2026)

Solicitado pelo usuário a partir de capturas da janela Sticky Notes; ainda não priorizado para uma sprint. O requisito inicial de barra invisível foi atualizado: trilho transparente e indicador limpo/translúcido, exibido somente quando houver overflow. UX recomendou inicialmente preservar `ALWAYS`, mas após o usuário apontar a barra indevida em nota curta (“test 2”), frontend adotou `AUTOMATIC`; a altura natural continua contida (`propagate_natural_height(False)`). O indicador usa `rgba(22,22,22,0.20)`, hover/foco `0.30` e ativo `0.40`. O CSS mantém transparente o trilho e neutraliza decoração no `TextView`, viewport, overflow e junction. Quatro testes passaram; a validação de rolagem/visibilidade na instalação ainda depende do usuário.

Critérios de aceite: nenhuma borda/linha separadora ou trilho sólido aparece ao redor da área de texto; a barra translúcida só aparece quando o conteúdo excede a área visível, some quando não há mais overflow e fica mais perceptível em hover/arraste/foco; texto comprido continua rolável por mouse e teclado, sem aumentar a altura do cartão. Preservar conteúdo, salvamento, cabeçalho, tamanho e alça de redimensionamento. Quatro testes direcionados passam; o smoke GTK que verifica texto curto→longo→curto e geometria foi pulado por falta de display. Aplicação e confirmação manual pendentes.

## STICKY-02 — Abrir caminhos, URLs e e-mails por Ctrl+clique (20/10/2026)

Pedido confirmado: permitir Ctrl+clique em uma referência dentro do texto de Sticky Notes para abrir caminho local no gerenciador de arquivos, URL no navegador padrão ou e-mail no cliente padrão. Clique normal continua editando a nota.

Critérios: detectar a referência lógica sob o cursor mesmo se houver quebra visual; abrir apenas caminhos existentes e esquemas HTTP/HTTPS/mailto validados pelo serviço URI do desktop, sem shell/comando; falhas de abertura não alteram nem removem texto. Enquanto Ctrl está pressionado sobre destino válido, destacar somente o link em negrito e usar cursor pointer; restaurar ao soltar Ctrl, sair, editar ou perder foco. Implementado em módulo de resolução separado e integrado ao `TextView`; caminhos de arquivo abrem a pasta que os contém. Dez testes cobrem Ctrl/clique normal, hover e liberação da tecla, alcance do destaque, caminhos com espaços/acentos, texto multilinha, URI inválida e falha de abertura simulada. `py_compile` e diff check passaram; interação gráfica e abertura pelos aplicativos padrão não foram executadas.

## STICKY-03 — Alça de redimensionamento acessível (20/10/2026)

Pedido confirmado: aproximar a seta de redimensionamento da borda e facilitar o acerto do ponteiro. Frontend implementou alvo de 28×28 px dentro de um `Gtk.Overlay`, ancorado a 2 px dos cantos; o ícone fica aproximadamente a 6 px da borda e toda a área mostra cursor `se-resize`. O conteúdo recebe 30 px de margem inferior para não ficar sob o alvo, sem mudar o tamanho inicial configurado. Quatro testes sintéticos verificam tamanho/posição do alvo, cursor e preservação do gesto no canto sudeste; teste geométrico real foi pulado sem display. Conferência da posição, arraste e tamanho do cartão ainda pendente na sessão do usuário.

## WID-01 — Unificar os widgets de desktop em Workspace (20/10/2026)

Solicitado pelo usuário a partir da captura do widget de relógio/data/clima; ainda não priorizado para uma sprint. Reunir os widgets atualmente separados do desktop em um único widget de topo chamado **Workspace**, usando a captura como referência para uma superfície visual unificada. O pedido inclui os widgets existentes de relógio, clima e outros módulos de desktop.

Critérios para implementação: apresentar os módulos do escopo dentro de um único widget configurável, sem janelas de desktop independentes para cada módulo; permitir reconhecer e configurar cada seção sem misturar seus controles; preservar dados e preferências existentes ou migrá-los de modo reversível; manter carregamento, atualização, acessibilidade e interação dos módulos que continuarem incluídos.

Definições necessárias antes da implementação: inventariar todos os widgets atuais e confirmar se “todos” inclui desempenho/sistema, rede, mídia e lançadores; definir grade, posição, redimensionamento e liga/desliga das seções; decidir se aplicativos separados como Sticky Notes e YouTube permanecem fora do widget unificado. O nome Workspace coincide com o Orbitz Workspace de agenda/horas/faturamento e precisa de diferenciação clara na interface. Sem prioridade ou sprint atribuída.

## WID-02 — Relógio mundial adicional (20/10/2026)

Solicitado pelo usuário; requisito ainda não resolvido/aceito. O usuário relatou que a opção de fuso aparece somente no relógio analógico e pediu que também esteja no relógio digital, usando dropdown completo com a região/cidade da timezone em vez de input. Existe implementação tentativa no checkout que inclui catálogo pesquisável; isso não substitui a observação do usuário nem comprova que o controle esteja visível e utilizável nos dois relógios. Não marcar concluído até reproduzir e validar a configuração digital e analógica na interface.

Critérios para aceite: a opção aparece em relógios digitais e analógicos; escolher uma região por nome/localidade e fuso horário em lista pesquisável, sem exigir GWeather; persistir a escolha após reiniciar; atualizar a hora sem bloquear a interface; aplicar regras de horário de verão e mudanças de offset, sem alterar o relógio local. Testes de catálogo/formatação passam, mas o requisito de interface permanece aberto; validação GTK e visual real aguardam reprodução do relato e correção.

## CLOUD-01 — Integração de arquivos Google Drive e Zoho WorkDrive (20/10/2026)

Solicitado pelo usuário e classificado como baixa prioridade (P3 proposta), sem sprint atribuída. Adicionar Google Drive e Zoho WorkDrive como itens de menu no Orbitz. Usar o nome WorkDrive: Zoho Docs foi descontinuado. A interface do Orbitz deve permitir consultar arquivos sem abrir browser durante o uso normal; primeira autorização OAuth pode abrir o browser do sistema para o consentimento.

Escopo inicial proposto: conexão/desconexão de conta, lista de recentes e favoritos, busca de arquivos, estado da conexão e abertura de formatos compatíveis no aplicativo local padrão. Não solicitar senhas dos serviços; guardar e remover tokens conforme o cofre seguro existente. Solicitar permissões mínimas e explicar o alcance do acesso antes de conectar.

Critérios para implementação: permitir navegar/consultar os arquivos selecionados dentro do menu/painel do Orbitz; manter listagem e busca responsivas, com estados de erro/offline claros; abrir localmente tipos de arquivo compatíveis sem lançar browser. Documentos nativos dos editores web podem exigir o browser para edição colaborativa completa; sinalizar essa limitação sem simular suporte nativo. Decidir escopos OAuth, suporte a arquivos compartilhados, formatos, cache/localização temporária, revogação de tokens e requisitos de verificação dos provedores antes de desenvolver.

## INT-01 — Centro de integrações (20/10/2026)

Pedido confirmado: adicionar uma aba **Integrations** ao lado de **Settings** e **About**, centralizando a descoberta e gestão de todas as integrações externas e suas credenciais, para não espalhar os pontos de configuração pela aplicação. Inventariar serviços existentes e planejados (por exemplo, calendários, Google Drive/Zoho WorkDrive, YouTube e provedores de cotações) antes de declarar cobertura completa.

Escopo: catálogo de serviços com estado conectado/desconectado/ação necessária, conta ou identificador associado, permissões concedidas e ações disponíveis para conectar, configurar, renovar/substituir credenciais ou desconectar/revogar. Centralizar a entrada e gestão de API keys, certificados e tokens; telas específicas dos recursos devem levar à integração correspondente, sem duplicar formulários de credenciais. Manter preferências funcionais próprias do recurso no seu contexto quando isso não for uma credencial.

Critérios para implementação: nunca mostrar segredos completos por padrão nem gravá-los em texto claro, logs ou configurações comuns; reutilizar o cofre seguro/Secret Service do Orbitz, mostrar valores mascarados e oferecer substituição/remoção explícita. Certificados devem ser apresentados com tipo, validade/estado e ações seguras, sem expor chaves privadas. Indicar erros de autorização/expiração de modo acionável e preservar integrações existentes durante a migração para a nova tela. Ainda sem prioridade de sprint.

## TERM-01 — Foco automático do Tilix nas ações interativas (20/10/2026)

Pedido confirmado: quando ações do Orbitz abrem Tilix para confirmação/autorizações, dar foco à nova janela para que o usuário só precise pressionar Enter. Abrange painéis de atualizações, processos, firmware RAM e limpeza, além do lançador btop. Preservar os comandos e a confirmação existente; não autoexecutar ações.

Implementação local fecha o diálogo antes de criar o processo filho, evitando disputa com o grab modal, e reabre o diálogo se o spawn falhar. Testes focados passaram; auditoria independente não encontrou bloqueio para teste local. Em 20/10/2026, o usuário confirmou que aplicou/reiniciou e considerou a tarefa concluída. Fechar com base nessa confirmação, sem generalizar para outros ambientes/sessões.

## FX-01 — formatação com centavos e precisão cripto (21/10/2026; estado corrigido)

Usuário esclareceu para Fiat: preservar centavos e limitar a duas casas, arredondando metade para cima (`0.19829 → 0,20`, `5.04 → 5,04`, `83060.16777893 → 83.060,17`); valores Fiat abaixo de `0.005` aparecem `0,00`. A primeira formulação desse registro dizia aplicar centavos também ao cripto, mas foi corrigida após verificar que USD→ativo pequeno era exibido como `0,00`. Regra atual: a cotação unitária USD→cripto mantém dígitos fornecidos; ativo→USD usa duas casas. JSON preserva taxa original. Sem efeito em invoices. Instalação e validação visual pendentes.

## FX-02 — calculadora na modal (21/10/2026)

Pedido confirmado: informar um valor livre na modal e ver o total convertido para o par/sentido selecionado, fiat ou cripto. Campo inicia em 1 e recalcula ao digitar, sem nova consulta de rede. Aceita vírgula decimal e milhares brasileiros (`1.000,50`), ou ponto decimal sem agrupamento; `1.000` significa mil. Zero permitido; vazio, negativo, notação científica e entradas malformadas não geram total. Valor digitado é temporário na modal, não salvo nas configurações. Resultado com duas casas e separadores pt-BR. Multiplicação decimal exata da taxa JSON original via BigInt, arredondando metade para cima somente no total; nunca calcular sobre o valor unitário exibido. Atualizar/inverter invalida o total até resposta válida; erro não mantém total antigo. Sem efeito em invoices ou gravação financeira.

Implementação fonte e verificações dirigidas concluídas (19 testes Python FX, Node modal/erros/calculadora e composição; sintaxe/diff). Revisão focada independente concluída sem defeito bloqueador reproduzido; auditor confirmou os exemplos de multiplicação e arredondamento também no GJS real. Instalação e validação visual/interativa GNOME pendentes.


## FX-03 — precisão completa na calculadora cripto (21/10/2026)

Pedido confirmado pela captura: o total cripto não deve desaparecer como `0,00`. Na calculadora em modo Crypto, em ambos os sentidos, exibir o produto decimal da quantidade pela taxa recebida sem limite de duas casas nem notação científica; remover apenas zeros finais. A cotação unitária USD→ativo também preserva as casas fornecidas; ativo→USD permanece em centavos. A formulação inicial deste registro que mantinha a cotação unitária do widget em centavos foi supersedida pela correção de 21/10, testada em `widgets/currency-widget.py`. Exemplo: `400 × 0.000016273845678 = 0,0065095382712 BTC`. Sem inventar precisão além da taxa recebida.

Implementado na fonte com BigInt; testes Node da calculadora/modal e composição aprovados. Revisão média agrupada no fechamento; instalação e validação visual GNOME pendentes.
