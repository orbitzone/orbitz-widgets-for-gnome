# RF-01 — revisão estrutural frontend — 18/10/2026

Estado: **implementado com verificações específicas aprovadas; auditoria integrada e validação visual pendentes**. Responsável: frontend. Base de comparação: `HEAD`/`2a24e0d`, checkout compartilhado; documentação e mudanças backend já existentes foram preservadas. Liberação recebida após a baseline do auditor (44 Python e 12/15 JS); esses números são históricos, não nova execução frontend.

## Entrega e contratos

- `extension/extension.js`: 24 métodos de construção/renderização/inspeção de painéis extraídos para `extension/panels/`. `commandPanels.install` compõe os métodos no protótipo **antes** de `GObject.registerClass`, rejeita colisões e mantém classe, herança, nomes, estado e ciclo de vida. A extensão mantém execução/cancelamento, polling, arraste, widgets, mídia e controlador; esses fluxos dependem do estado da sessão e não foram repartidos em wrappers artificiais. O arquivo passou de 3361 para 2444 linhas; isso descreve a separação, não um ganho de desempenho.
- `settings/TimeZoneDialog.js`: diálogo e detecção opcional de GWeather separados da base de páginas. `SubPage` importa ambos; a dependência ausente continua desabilitando a pesquisa. `createComboRow` idêntico em `TextLabelSubPage` e `DigitalClockSubPage` foi centralizado na classe base. `WidgetSubPage` conserva sua implementação distinta de seleção por índice. Valores, tradução e persistência existentes não mudaram.
- `planner/task_timesheet_ui.py`: revisão, escolha, sugestão de horários, confirmação de sobreposição e registro da tarefa concluída extraídos da janela. `CalendarWindow.register_task` delega. `store.modify`, payload, vínculos, rascunhos e gestão das abas continuam com os contratos existentes.
- `sticky-notes/card.py`: cartão GTK, texto, undo, geometria, timers e flush separados de `Postits`, que conserva armazenamento e ciclo da aplicação. `postits.py` continua importando/expondo `Card` e sendo o ponto de entrada. Nenhuma mudança em SQLite/backups.
- `youtube-widget/youtube_api.py`: chave local, consultas, normalização e cache; `youtube_server.py`: handler HTTP; `youtube-widget.py`: GTK/WebKit e ciclo do servidor. O corpo de `main` e das funções extraídas foi preservado. Permanecem os mesmos endpoints, token no caminho, Origin loopback exata, limites, mensagens, cache e permissões. Nenhuma leitura de segredo real foi feita.

Novos módulos são obrigatórios ao empacotar as fontes. O repositório **não atualiza** a instalação ativa, e não houve instalação, reload GNOME, commit ou push.

## Inventário de todos os arquivos frontend originais

Revisão estrutural por responsabilidades, dependências e pontos de entrada. “Manter” não afirma ausência absoluta de defeitos nem validação visual. Backend, vendor, binários, imagens, traduções, licenças, schemas e metadata ficam fora desta propriedade.

| Arquivo | Decisão e justificativa |
|---|---|
| `extension/extension.js` | Refatorar painéis; preservar orquestração e demais classes que compartilham estado de sessão/GSettings. |
| `extension/dragging.js` | Manter: máquina de estado pequena para arraste, independente e já extraída. |
| `extension/grouping.js` | Manter: planejamento puro de hierarquia/grupos, já testável isoladamente. |
| `extension/utils.js` | Manter: acesso/conversão GSettings e catálogo canônico de presets; separar tabelas estáticas não reduz responsabilidade de comportamento nesta entrega. |
| `extension/prefs.js` | Manter: entrada de preferências e lista de widgets; HomePage/WidgetRow/diálogo de adição integram o mesmo fluxo, sem duplicação idêntica demonstrada com adição de elementos. |
| `extension/settings/AboutPage.js` | Manter: página de informações/importação/exportação; parser/validação já isolados em SettingsImport. Preservar créditos. |
| `extension/settings/AnalogClockSubPage.js` | Manter: controles do relógio analógico e grupos de ponteiros. |
| `extension/settings/CommandLabelSubPage.js` | Manter: especialização curta dos controles de comando. |
| `extension/settings/DialogWindow.js` | Manter: base reutilizável pequena de diálogos de preferências. |
| `extension/settings/DigitalClockSubPage.js` | Refatorar: herdar controle de alinhamento idêntico; conservar composição de controles. |
| `extension/settings/SettingsImport.js` | Manter: fronteira coesa de leitura limitada, parse e validação de configurações. |
| `extension/settings/SubPage.js` | Refatorar: extrair busca/diálogo de fuso e centralizar controle de alinhamento duplicado. |
| `extension/settings/TextLabelSubPage.js` | Refatorar: herdar controle de alinhamento idêntico; conservar composição da página. |
| `extension/settings/WidgetSettingsPage.js` | Manter: lista de elementos e seu diálogo de adição compartilham o fluxo da página; presets diferem da adição de widgets. |
| `extension/settings/WidgetSubPage.js` | Manter: aparência/grupos do contêiner; controle de âncora usa índice e não é a duplicação de alinhamento textual. |
| `extension/settings/WidgetsData.js` | Manter: adaptador compartilhado pequeno do estado observado pelas páginas. |
| `extension/planner/calendar.js` | Manter: serviço ativo de lembretes/cache/cartões; coleta de elegibilidade já separada em reminders.js. |
| `extension/planner/reminders.js` | Manter: cálculo puro de lembretes e deduplicação. |
| `extension/planner/planner.js` | Manter: implementação legada paralela, não importada pelo ponto de entrada atual; não remover histórico nem unificar com serviço ativo sem tarefa de migração. |
| `extension/planner/calendar-app.py` | Refatorar fluxo tarefa→timesheet; manter janela como dona de abas, seleção, renderização e diálogos curtos de gestão das próprias páginas. |
| `extension/planner/calendar_selector.py` | Manter: seletor/popover reutilizável com dimensionamento abaixo do campo. |
| `extension/planner/editor.py` | Manter: editor legado isolado, com seu ciclo de salvamento e undo; não fundir com notas SQLite independentes. |
| `extension/planner/external_ui.py` | Manter: controlador das fontes externas, sincronização assíncrona e diálogos que compartilham cancelamento/contexto; integrações/dados continuam nos módulos backend. |
| `extension/planner/month_calendar.py` | Manter: calendário mensal customizado coeso; riscos de foco/redraw são propostas UX separadas. |
| `extension/planner/planner_tools.py` | Manter: ferramentas de consulta de arquivadas/restauração; transações continuam no backend. |
| `extension/planner/timesheet_ui.py` | Manter: editor integrado de uma timesheet, rascunhos e timers da página; domínio já separado em timesheet.py. |
| `extension/notes-widget/notes-widget.py` | Manter: wrapper curto para abrir o aplicativo instalado; preservar caminho histórico operacional. |
| `extension/youtube-widget/youtube-widget.py` | Refatorar API e HTTP; manter janela, políticas WebKit, fullscreen e encerramento do servidor no entrypoint. |
| `extension/youtube-widget/index.html` | Manter: cliente de uma única página/resposta HTML tokenizada; extrair assets exigiria ampliar a superfície de GET sem benefício necessário nesta RF-01. Sem alteração de CSS/DOM/player. |
| `sticky-notes/postits.py` | Refatorar cartão vs aplicação; manter app/dados/monitores/shutdown neste ponto de entrada. |

## Novos módulos

| Arquivo | Responsabilidade |
|---|---|
| `extension/commandPanels.js` | Composição e proteção contra colisões antes do registro GObject. |
| `extension/panels/common.js` | Estrutura compartilhada dos painéis de atualização e tooltips acessíveis a labels/botões. |
| `extension/panels/updates.js` | Validação/apresentação de pacotes e ações de atualização. |
| `extension/panels/temperatures.js` | Categorias, distribuição dos sensores, diálogo e apresentação térmica. |
| `extension/panels/storage.js` | Detalhes de hardware, volumes e saúde de armazenamento. |
| `extension/panels/resources.js` | Pressão, serviços e processos, incluindo ranking e ações. |
| `extension/panels/network.js` | Detalhes de tráfego/qualidade e coluna de teste de velocidade. |
| `extension/panels/docker.js` | URLs e apresentação de contêineres. |
| `extension/panels/firewall.js` | Painel de evidências e ciclo de inspeção de firewall. |
| `extension/settings/TimeZoneDialog.js` | Pesquisa/seleção de local/fuso e disponibilidade GWeather. |
| `extension/planner/task_timesheet_ui.py` | Revisão e registro de tarefa concluída em timesheet. |
| `sticky-notes/card.py` | Uma nota GTK: edição, opções, geometria, timers e salvamento. |
| `extension/youtube-widget/youtube_api.py` | API, configuração local e cache de sugestões. |
| `extension/youtube-widget/youtube_server.py` | Fronteira HTTP local tokenizada e cache em memória. |

## Testes e diagnóstico dos três históricos

Nenhuma expectativa foi apagada para ocultar falhas. Diferenciar correção da fixture de atualização da especificação do teste:

- `test_storage_ui.js`: fixture incompleta, agora com `_updatesNote`, botão, scroll, ações, PolicyType e `connect`. As assertivas originais de SMART, alerta, capacidade, EXT, partição não montada e validação continuam. Tooltips agora são associados ao **ator do cartão**: o botão de limpeza também possui tooltip, portanto índice global não identifica o volume. A assertiva de `foto.jpg` exige o tooltip do cartão EXT correto; a de inodes exige o cartão do volume montado correto.
- `test_widget_controller.js`: mocks `Calendar` e D-Bus completados; o mock verifica encerramento de Postits por `Activate` com `NO_AUTO_START`. Expectativa do ícone ativo corrigida para branco, conforme requisito/documentação de `README.md`, seção Controlador e interação. Mantidos startup pausado, posição, timers, Play/Stop, ciclos, cancelamento e rollback.
- `test_stats_storage_click.js`: expectativa antiga anulava CPU/RAM. A implementação já retorna `cpu`/`ram` e a documentação observada em `README.md`, tabela Widgets, registra detalhes CPU/RAM. Esta entrega preserva **comportamento observado**, sem inventar aprovação de um novo requisito de clique: teste agora explicita CPU/RAM/SSD/EXT, espaço vazio e ejeção com UTF-8/prefixos. Se o produto desejar CPU/RAM inertes, isso requer decisão funcional própria; não houve alteração desse comportamento na RF-01.

### Inventário dos testes JS originais

| Arquivo | Decisão |
|---|---|
| `test_action_tooltip.js` | Adaptado para executar método do módulo real; mesmas assertivas de sinais/ciclo. |
| `test_dialog_dismiss.js` | Adaptado para procurar handlers nos módulos e no entrypoint; preserva cinco backdrops e cliques dentro/fora. Ainda usa extração textual localizada. |
| `test_pressure_ui.js` | Adaptado para módulo real; valida colunas, ausência e rejeição de payloads. |
| `test_processes_layout.js` | Adaptado para módulo real; mantém ranking, limite, tooltips e estados. |
| `test_quality_ui.js` | Adaptado para módulo real; mantém ausência ICMP, destinos e validação. |
| `test_services_ui.js` | Adaptado para módulo real; mantém escopos, detalhes e validação. |
| `test_storage_ui.js` | Adaptado conforme diagnóstico acima. |
| `test_temperature_layout.js` | Adaptado para módulo real; mantém distribuição, cardinalidade e ausência de duplicação. |
| `test_stats_storage_click.js` | Expectativas do comportamento observado corrigidas, conforme acima. |
| `test_widget_controller.js` | Fixtures e requisito de ícone corrigidos, conforme acima. |
| `test_command_output.js` | Mantido: execução/limite/limpeza não movidos. |
| `test_group_layout.js` | Mantido: geometria e agrupamento não movidos. |
| `test_grouping.js` | Mantido: planejamento puro não alterado. |
| `test_super_ctrl_drag.js` | Mantido: máquina de arraste/modificadores não alterada. |

Divergência de contagem encontrada na revisão: `git ls-files 'tests/*.js'` lista **14 arquivos originais**, e a tabela nominal da baseline também lista 14, embora seu resumo informe 12/15. Este relatório preserva o resumo como informação recebida, sem tratar o denominador como nova evidência; supervisor/auditor devem reconciliar a contagem na execução integrada. Com os dois testes novos, há 16 entrypoints `test_*.js` no estado atual.

Novos testes: `tests/helpers/command_panels.js` carrega fábricas/métodos reais; `test_panel_composition.js` verifica instalação, herança, dispatch entre métodos e colisões; `test_settings_alignment.js` verifica herança, quatro seleções, tradução e persistência; `test_frontend_modules.py` verifica cinco contratos sintéticos do YouTube sem GTK, sockets, API externa ou chave real.

### Comandos e resultados desta execução

- `node tests/<arquivo>.js`, individualmente para `test_storage_ui`, `test_temperature_layout`, `test_widget_controller`, `test_stats_storage_click`, `test_pressure_ui`, `test_services_ui`, `test_processes_layout`, `test_quality_ui`, `test_action_tooltip`, `test_dialog_dismiss`, `test_panel_composition`, `test_settings_alignment`: **12 arquivos aprovados**. Reexecuções só ocorreram ao corrigir fixtures/código afetado.
- `python3 -m unittest discover -s tests -p test_frontend_modules.py -v`: **5/5 aprovados**.
- `node --check`: **27 arquivos JS novos/alterados aprovados**, incluindo helpers/testes e módulos. `ast.parse`: **7 arquivos Python de produção novos/alterados aprovados**.
- Comparação AST com `git show HEAD:<arquivo>`: classe Card, oito definições YouTube e fluxo tarefa→timesheet iguais, neste último apenas renomeando `self`→`window`. Os **24 métodos GJS extraídos estão presentes integralmente uma única vez** nos módulos.
- `gjs /tmp/orbitz_gobject_composition.js "$PWD/extension"`: **24 métodos registrados em GObject real**, herança e chamada de um método a outro aprovadas, sem abrir Shell ou janela.
- `gjs /tmp/orbitz_timezone_import.js "$PWD"`: **classe TimeZoneDialog registrada com Gtk4/Adw reais**. GWeather indisponível neste ambiente; caminho de pesquisa com biblioteca instalada não executado.
- `git diff --check -- <arquivos frontend rastreados alterados>`: aprovado, sem erros de whitespace.
- Nenhuma suíte integrada foi rodada pelo frontend durante mutações paralelas. Backend informou estabilidade em 18/10/2026 e relatório próprio; próximo passo é a suíte/auditoria independente coordenada pelo supervisor.

## Validação visual, segurança e limites

Funcional: métodos/cálculos em Node, contratos HTTP/API sintéticos, registro real GObject/Gtk4 e preservação estrutural verificados. Isso não substitui execução interativa GTK/WebKit/GNOME.

Visual: **pendente**. `broadwayd --address 127.0.0.1 --port 18085 :5` falhou ao criar socket: `Operation not permitted`. Tentativa isolada por IPC Unix, com `XDG_RUNTIME_DIR=/tmp/orbitz-frontend-gtk-runtime` e `--unixsocket=.../http.socket`, também recusou `Error binding ... Operation not permitted`. Nenhuma permissão foi contornada; nenhuma sessão ativa ou dado pessoal foi usado. Não há capturas antes/depois, prova de foco, pixels, contraste, animações ou DPI.

Segurança/integridade: testes específicos preservam fronteira token/origem e chave sintética com modo 0600 e rejeição de symlink. Corpos de validações e cancelamento preservados; auditoria independente permanece com auditor. Nenhum ganho de desempenho foi alegado ou medido.

UX: `docs/design/2026-10-18-review.md`, recebido do UX, contém inventário e propostas A–H. Achados de foco, tema/contraste, dimensões, modalidade, relações acessíveis, alvo/gestos e animações permanecem separados da RF-01. Cenário de erro de salvar chave na aba Comentários apontado estaticamente **ainda não foi reproduzido**; não tratado como defeito confirmado nem corrigido nesta refatoração. Encaminhado ao supervisor para triagem. UX recebe o marco final e o limite de captura.

Próximos responsáveis: supervisor integra documentação/mapa dos novos módulos e encaminha estado estável ao auditor; auditor executa suíte integrada e revisão independente. Frontend responde aos achados; UX revisa evidência visual quando houver ambiente isolado permitido. Não declarar RF-01 integralmente validada antes dessas etapas.
