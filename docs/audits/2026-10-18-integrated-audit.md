# RF-01 — auditoria integrada independente — 18/10/2026

Estado: verificações locais funcionais/estruturais e revisão de regressões de segurança/integridade aprovadas no alvo abaixo; validação visual/interativa pendente. Nenhum achado impeditivo de código reproduzido nesta auditoria. Não equivale à conclusão integral de RF-01 enquanto faltar a validação visual exigida.

## Alvo, fontes e estabilidade

HEAD: `2a24e0d6875063cfee9412b1c9545181f999d3ad`, com alterações locais backend/frontend/documentação listadas abaixo; sem commit de entrega. Supervisor encaminhou ambos como estáveis, sem testes/mutações em curso. Lidos os relatórios backend/frontend, baseline e `docs/design/2026-10-18-review.md`, inclusive o complemento UX de equivalência estática recebido no encerramento; ele sustenta equivalência delimitada e mantém pendência visual, sem exigir repetição dos testes suficientes. O auditor não alterou código, dependências, dados pessoais, instalação, sessão GNOME ou licenças; editou somente este relatório e a errata da baseline.

Execução UTC: `2026-10-18T03:46:12.011678+00:00`; data local 18/10/2026, America/Sao_Paulo. Ambiente `Linux-6.8.0-138-generic-x86_64-with-glibc2.35`; Python `3.10.12`; Node `v24.15.0`.

Manifesto SHA-256 de todos os arquivos .py/.js/.html próprios e de testes, excluindo vendor e __pycache__, capturado antes da suíte e comparado ao final de toda auditoria: **nenhum código alterado**. Novos módulos necessários à distribuição constam do manifesto. Documentação pode receber coordenação paralela e não é coberta pela afirmação de estabilidade do código.

## Contagem corrigida e execução atual

A baseline nominal tinha 14 arquivos JS, 11 aprovados e três falhas; o resumo 12/15 era erro aritmético do auditor. Conferidos enumeração inicial salva, tabela nominal e `git ls-files 'tests/*.js'` (14 originais). Errata explícita acrescentada, preservando o texto histórico. A suíte atual contém 16 entrypoints `tests/test_*.js`, dois novos. O helper JS não é entrypoint de teste. Nenhuma falha histórica foi apagada; três arquivos continuam na suíte.

Python atual: **62/62 testes aprovados**, código 0, 2,507 s informados pelo unittest. São 44 anteriores + 13 novos backend + 5 novos frontend. JavaScript: **16/16 arquivos aprovados**. Sintaxe: **102 arquivos** (56 Python, 46 JS), zero falhas.

Comandos executados:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
# Cada entrypoint tests/test_*.js, lexicalmente, sem interromper na primeira falha:
node tests/<arquivo>.js
# Cada .js próprio e de testes (inclusive helper), sem vendor:
node --check <arquivo.js>
git diff --check
git ls-files 'tests/*.js'
gjs /tmp/orbitz_gobject_composition.js "$PWD/extension"
gjs /tmp/orbitz_timezone_import.js "$PWD"
```

Python: `ast.parse(read_text(), filename=path)` em todos os .py próprios/testes. Importação sem iniciar aplicativos: `importlib.util.spec_from_file_location` + `exec_module` para calendar-app, task_timesheet_ui, postits, card, youtube-widget, youtube_api e youtube_server, ajustando temporariamente `sys.path` para cada componente. Todos passaram. Importação não criou janela nem consultou cofre/rede. Grafo estático AST de imports locais em planner, widgets, sticky-notes e youtube-widget: nenhum ciclo intra-componente encontrado; não é análise completa de imports dinâmicos de terceiros.

Comparação estrutural independente: `git show HEAD:<arquivo>`, `ast.parse`, `ast.dump` sem atributos de localização. Igualdade de CalendarError/seis funções iCalendar, Vault, oito funções UFW, classe Card, classe MissingAPIKey/cinco funções API e make_handler. Cinco corpos de entrada dos coletores iguais aos corpos de main, excluindo imports/definições/docstring do nível superior; display apenas realocado. Fluxo register_task igual após substituição AST de self por window. Os 24 métodos dos painéis comparados por texto integral, incluindo async, permanecem idênticos ao HEAD. Imports/reexports/captura de dependências foram lidos separadamente; equivalência de corpo não comprova por si só todo ambiente de execução.

A primeira tentativa de comparação AST incluía indevidamente a docstring de módulo de segurança entre instruções executáveis; ajustado o método da comparação, sem mudar código. Uma tentativa Node `child_process.execFileSync('git', ...)` retornou `spawnSync git EPERM`; operação registrada como bloqueada e não repetida por Node. A comparação textual final foi feita com leitura Git já permitida pela ferramenta de shell e Python, sem mudar permissões ou tocar sessão ativa. Uma enumeração inicial do comparador omitia cabeçalho async; incluído antes da verificação final 24/24. Esses erros de método não foram classificados como defeitos do produto.

## Resultados por entrypoint JS

| Arquivo | Código |
|---|---:|
| `tests/test_action_tooltip.js` | 0 |
| `tests/test_command_output.js` | 0 |
| `tests/test_dialog_dismiss.js` | 0 |
| `tests/test_group_layout.js` | 0 |
| `tests/test_grouping.js` | 0 |
| `tests/test_panel_composition.js` | 0 |
| `tests/test_pressure_ui.js` | 0 |
| `tests/test_processes_layout.js` | 0 |
| `tests/test_quality_ui.js` | 0 |
| `tests/test_services_ui.js` | 0 |
| `tests/test_settings_alignment.js` | 0 |
| `tests/test_stats_storage_click.js` | 0 |
| `tests/test_storage_ui.js` | 0 |
| `tests/test_super_ctrl_drag.js` | 0 |
| `tests/test_temperature_layout.js` | 0 |
| `tests/test_widget_controller.js` | 0 |

## Revisão dos contratos e segurança/integridade

- **Falhas históricas:** armazenamento completa os atores ausentes do mock, preserva assertivas de SMART/capacidade/alertas/partição inválida e liga a assertiva de tooltip ao ator do volume/EXT correto, evitando confundi-lo com o botão de limpeza. Controlador completa Calendar/D-Bus; espera branco conforme comportamento já existente e documentação; mantém ciclos, rollback/cancelamento e acrescenta verificação NO_AUTO_START/Activate. Clique CPU/RAM troca expectativa antiga nula por cpu/ram: método não foi modificado nesta entrega e já retornava esses valores no HEAD. É alinhamento ao comportamento observado, não prova de requisito novo aprovado; eventual alteração funcional requer decisão do supervisor. Não houve redução de validações para mascarar falha nova.
- **Composição GJS:** commandPanels instala em classe derivada de Label antes de GObject.registerClass, injeta dependências explícitas e rejeita colisões em métodos próprios. Os 24 métodos são expostos uma vez nos oito módulos; superfícies de polling/cancelamento permanecem no entrypoint. Node verifica instalação/herança/dispatch/colisão. GJS real verificou os 24 métodos após registro e chamada entre métodos; Gtk4/Adw registraram TimeZoneDialog, GWeather ausente. Esse script GJS testa descritores/registro, enquanto Node testa o instalador real; nenhum dos dois executa o Shell completo.
- **Worker/main:** worker inalterado compila os mesmos arquivos e executa namespace __main__/__file__, com saída limitada a 8192 bytes e envelopes anteriores. main guarda os cinco scripts; importação não amostra/dorme/spawna/imprime. CPU testada com o contrato exec real do worker e leituras sintéticas; demais prefixos/fallbacks cobertos. Nenhuma leitura de EXTERNAL_DEVICES existia antes para ser preservada nesses scripts. Não alterados agendamento, heartbeat, unidades ou lógica de limites.
- **Atomicidade/locks/backups:** atomic_json mantém temporário no diretório destino, modo 0600, serialização/flush/fsync antes de replace e fsync do diretório; limpeza em finally. store mantém lock em modify e snapshot anterior ao replace, verificação de fingerprint/hash na restauração e retenção de 60. ui_state/external_store mantêm seus locks durante leitura/mutação/escrita. Falhas de serialização/replace preservam original; fsync posterior ao replace pode falhar depois da substituição, como no código anterior: não há promessa de rollback. Suíte reproduziu concorrência de oito processos sem perda, restauração com snapshot, retenção e arquivo danificado preservado.
- **Dados independentes:** tarefas/timesheets e SQLite não passaram a depender de calendários externos; storage.py e timesheet.py mantidos. Testes cobrem vínculo sem duplicação, cronômetro em meia-noite, CSV protegido e rascunhos independentes de contas/cache.
- **Credenciais/HTTP:** Vault mantém corpo e acesso gi/Secret tardio; classe reexportada mantém identidade. YouTube mantém token no caminho, bind 127.0.0.1, Origin loopback exata, limite de corpo, cache limitado e leitura/gravação de chave com NOFOLLOW/0600. Clientes CalDAV/ICS mantêm validações de URLs, DNS/redirect e limites; normalização comum mantém identidade/classe de erro. Suíte usa chaves/feeds sintéticos e mocks, sem rede/cofre real. Nenhum segredo foi registrado.
- **Preservação da UI extraída:** Card e fluxo de registro de tarefa mantêm corpo; herança do combo de alinhamento é coberta com seleções, tradução e persistência. Scripts de importação verificam resolução dos novos módulos; não validam foco, pixels ou comportamento interativo.

## Achados, riscos e melhorias

**Defeitos reproduzidos no alvo:** nenhum impeditivo identificado no escopo auditado. Erro documental de contagem da baseline corrigido por errata (gravidade baixa, evidência acima); não é regressão funcional.

**Riscos/limites inferidos:** empacotar somente arquivos antigos quebra imports — todos os novos módulos precisam acompanhar os chamadores, como documentado pelos responsáveis/supervisor. Não foi ensaiada reinstalação. Imports dinâmicos GJS e a sessão real não foram integralmente executados. Não há conclusão de segurança integral do produto a partir destes testes. Nenhuma hipótese foi promovida a vulnerabilidade confirmada.

**Melhorias opcionais/preexistentes:** propostas UX A–H do relatório de design permanecem com supervisor/frontend, sem redesign nesta RF-01. Erro de feedback da chave na aba Comentários segue observação estática, não reprodução gráfica nesta auditoria. Não amplia escopo nem bloqueia a revisão estrutural pelo simples fato de ser proposta.

## Conclusão por dimensão e próximo responsável

| Dimensão | Conclusão | Limite |
|---|---|---|
| Funcional local/estrutural | Aprovada nas verificações executadas: 62 Python, 16 JS, 102 sintaxes, imports/registro/comparações descritos | Sem ciclo completo real GNOME/GTK/WebKit |
| Visual/interação | **Pendente** | Broadway TCP e Unix recusados previamente com Operation not permitted; não repetidos nem contornados; nenhuma captura antes/depois/pixels/foco/DPI |
| Segurança/integridade | Sem regressão impeditiva identificada nas extrações e fronteiras revisadas; testes locais aprovados | Revisão delimitada, sem certificação integral, segredos, rede real ou testes destrutivos |
| Desempenho | Sem alegação de ganho ou perda medida | Nenhum benchmark comparável; tempo da suíte não mede desempenho do produto |

Supervisor recebe este relatório para integrar o aceite e manter explícita a validação visual pendente; frontend/UX são próximos responsáveis por evidência visual em ambiente isolado permitido. Não há correção impeditiva encaminhada, nem autorização para deploy, instalação, commit ou push.

## Estado local e manifesto do alvo

`git status --short` no encerramento (documentação auditada também aparece como não rastreada):

```text
 M README.md
 M extension/extension.js
 M extension/planner/apple_client.py
 M extension/planner/calendar-app.py
 M extension/planner/external_store.py
 M extension/planner/ics_client.py
 M extension/planner/store.py
 M extension/planner/ui_state.py
 M extension/settings/DigitalClockSubPage.js
 M extension/settings/SubPage.js
 M extension/settings/TextLabelSubPage.js
 M extension/youtube-widget/youtube-widget.py
 M stack.md
 M sticky-notes/postits.py
 M tests/test_action_tooltip.js
 M tests/test_dialog_dismiss.js
 M tests/test_pressure_ui.js
 M tests/test_processes_layout.js
 M tests/test_quality_ui.js
 M tests/test_services_ui.js
 M tests/test_stats_storage_click.js
 M tests/test_storage_ui.js
 M tests/test_temperature_layout.js
 M tests/test_widget_controller.js
 M widgets/cpu-ram-widget.py
 M widgets/firewall-widget.py
 M widgets/processos-widget.py
 M widgets/rede-widget.py
 M widgets/seguranca-widget.py
 M widgets/temperaturas-widget.py
?? AGENTS.md
?? docs/agents/
?? docs/audits/
?? docs/backlog.md
?? docs/decisions.md
?? docs/design/
?? docs/project-context.md
?? docs/requirements.md
?? extension/commandPanels.js
?? extension/panels/
?? extension/planner/atomic_json.py
?? extension/planner/calendar_events.py
?? extension/planner/credential_vault.py
?? extension/planner/task_timesheet_ui.py
?? extension/settings/TimeZoneDialog.js
?? extension/youtube-widget/youtube_api.py
?? extension/youtube-widget/youtube_server.py
?? sticky-notes/card.py
?? tests/helpers/
?? tests/test_collector_entrypoints.py
?? tests/test_frontend_modules.py
?? tests/test_panel_composition.js
?? tests/test_planner_backend.py
?? tests/test_settings_alignment.js
?? widgets/firewall_patterns.py
```

| Arquivo | SHA-256 |
|---|---|
| `extension/commandPanels.js` | `723b9aad61565ed8c4e07e848144b74c75090a27135961ac7778bd543a9638b1` |
| `extension/dragging.js` | `5c5c20efbb6e257701fae07fd6113539c18b81ca144be8d563cd1379d8491e3b` |
| `extension/extension.js` | `242c2b9be7116b946fda3814d4dcc4ad13156048afcb1d128c1bd28620ff0525` |
| `extension/grouping.js` | `52cb3475ee8304c7cac84c8cc2480dcabc233043656c12499dde75fca0c8188e` |
| `extension/notes-widget/notes-widget.py` | `8805c1566e5aac7d1c3a07be3ed8a21e01451cff375d4b989675968d59a14ee6` |
| `extension/panels/common.js` | `c11ec5dcd9a0edd53209b0792479cf72c01b10496bcbc94b8a76487f13985511` |
| `extension/panels/docker.js` | `a1e4d3a885fb251927eaf850ed4610a7102f18b4d0a052d9abd72b708b08496e` |
| `extension/panels/firewall.js` | `238658f8577c5799f025cf928ecf536c562b3b36f368eb97d8440ca369618e65` |
| `extension/panels/network.js` | `ab80f44596498d1a60285e3d31f2033e7517a60c9221e7d6930e818280aad07f` |
| `extension/panels/resources.js` | `f4f294be9ee029f16121c70e0dbc93132c4df988b73f508c9698cd9634aed88a` |
| `extension/panels/storage.js` | `53e0cfcfacf7b5bebbc8faf55da986a4650d4585ece59e5f83dacfb5fe24e9f0` |
| `extension/panels/temperatures.js` | `243a6581374fa9322566dd08d2409ec393fccb0f79336fc516c7465be098b9b0` |
| `extension/panels/updates.js` | `dad78bce10dcd27dedc5c3ace21e00ba4080f3058444aa606b3b7e5abb75fb51` |
| `extension/planner/apple_client.py` | `b534006cf20338281aca16fbac33b860a480c119b8e6b8c6181109e267c2e088` |
| `extension/planner/atomic_json.py` | `b77e84f4083b4ee3968e8af96c3e609399577012a1f3ff918ab3b671f65711ca` |
| `extension/planner/calendar-app.py` | `fb716adf726507ba371c27e7ff8f1d23e0f4e45d74e872e5fa1d09fdea31afec` |
| `extension/planner/calendar.js` | `d4bf7acc2a97add8887953772dad5caa6c7847a4c56fdf849290538314926178` |
| `extension/planner/calendar_events.py` | `3ab977747fec333efeb2ab73fd279d4a31d6fa5d522fb1447d02596b59b7be7d` |
| `extension/planner/calendar_selector.py` | `230a43e4f02f941c6f1d6be628c5134032f1b7f60b30110f85c5e036ca899b98` |
| `extension/planner/credential_vault.py` | `0a9cf28278dc58125591f7ae6b66eb13801e482d2d2e581805fbac8807d54858` |
| `extension/planner/editor.py` | `742ccab8b0f9c135697800173dd8ce1d57edeac75e230e85d4b8277f8e57cfe9` |
| `extension/planner/external_store.py` | `09713a2747ec576e44c7e0957b638c351c264c275adf778833585267eac8ced7` |
| `extension/planner/external_ui.py` | `634682750194927739a04a803cc5c6a960364b08c4ea51b301110435e40549ab` |
| `extension/planner/ics_client.py` | `58226a71d617e77a1e6ffba54981f0a7ff9b40f72209316665840e8d98a4e73b` |
| `extension/planner/month_calendar.py` | `df5f27216ad1203315c37eae081d2b160f7e5f7d9a048ceb40933602151903bc` |
| `extension/planner/planner.js` | `65e48522ece6c4e81bae249d7509875288f048dbcaf7e4f4a104c0bfe954aaa4` |
| `extension/planner/planner_tools.py` | `685dc0f6d79b1fc272d18cb00f85e1bd33c43ece5fdb7548ae811c5c4e74edd4` |
| `extension/planner/reminders.js` | `ee02354d6014c1794c94de5480447c724eb268ae37b3214a12c044d08b2e8c8d` |
| `extension/planner/store.py` | `9e057e43c9d1681b416a496d63b2a3c5bda91ceff0fb45360c743387245c0417` |
| `extension/planner/task_timesheet_ui.py` | `2cc9dae1b9ef19c3d9e93db2190761002ccc3b375e3a87210410fb767bf60b97` |
| `extension/planner/timesheet.py` | `89cc5dc287a140bb32678ca8889d4f4b9578e9bf5e314f1043d9c1bd649b9bde` |
| `extension/planner/timesheet_ui.py` | `a4f79586d3bd1bf9ca3cc166ecf5aeacd5c54eeb0898581ba46cc477788fb6aa` |
| `extension/planner/ui_state.py` | `17758418cb40ddd05f68f167c296b348c8f68b1b842860ca5e17b7e259f9eaa0` |
| `extension/prefs.js` | `1744d946044737f248cdc8712d6c67ff199e8aef9749ed1d69af72919a955b38` |
| `extension/settings/AboutPage.js` | `de5c009b532d59dc335becd8a1a780c13f70089fa3f802f5f00ed3abf1d8f360` |
| `extension/settings/AnalogClockSubPage.js` | `9ab81b88dd50f0c333ea6f2116aa8ddf8f14076600875ec6296ce83262c1588b` |
| `extension/settings/CommandLabelSubPage.js` | `4d3863eeeaf408b62bbfc5c9348fba90b85656c3ac770d52d619327bbd7088f5` |
| `extension/settings/DialogWindow.js` | `9a43f0548ef4e74b3a75964f6a560336a732211ee256523e2abedfd7482362c7` |
| `extension/settings/DigitalClockSubPage.js` | `d32a58d4099a308fa2f2d8db3e6580c230e6f40fd8571cfc3e959bac0df7aea6` |
| `extension/settings/SettingsImport.js` | `ee8c7ceebe28f346c0a0efd4e6d78639f4c413e309b297ee8f83a62f2749cf5f` |
| `extension/settings/SubPage.js` | `ce7e8cd791ead1cd53ef3192e3d9db8db5f7c5e563ea2555114a015229a3970a` |
| `extension/settings/TextLabelSubPage.js` | `c843936dc0ff33c3bd30f072fe29b03bc3ea2dfd6f5e5986fb50a3892b8f47cf` |
| `extension/settings/TimeZoneDialog.js` | `6c30f7fe1e6c23493bc3d5bd534264c09c20af554a9e492a40456d2095389649` |
| `extension/settings/WidgetSettingsPage.js` | `3543e54069f262d222fa640fa8c2947e9642e1960922aa0e3d90c0cea77d6779` |
| `extension/settings/WidgetSubPage.js` | `c289dd72cf94c617c8550dab9e53fe54b70b6fbcfd27b5ab8b654e05502fe308` |
| `extension/settings/WidgetsData.js` | `0d32280a935975d85e4855ff8e7dc080f279158121a60144b8320d3572f3590d` |
| `extension/stop-collectors.py` | `cd19e4500d49e93ea47cea44894f2b7407b644abd4687e468c761561921e6515` |
| `extension/utils.js` | `24c9035bcfa6221f7248c84a2cfdfabd6cb4d0e6add5d5b7d426cd16acae4e33` |
| `extension/youtube-widget/index.html` | `a703631857838a2fdb5c6bd6706cefba931b45db02c3d1b29f0202307a35bfab` |
| `extension/youtube-widget/youtube-widget.py` | `242ea3afe2a1be93516a19d445eca1d892fc803be04960d82fd2444e5fc5d7d1` |
| `extension/youtube-widget/youtube_api.py` | `d653541aefb9ae28cca0c6eadd16f4a805af2d50fefa29a99b4eb34d9c4345a7` |
| `extension/youtube-widget/youtube_server.py` | `b5cd44ecd193017ff86626d56dfa8d964a185ad178245456d35925b3704d7383` |
| `sticky-notes/card.py` | `6605a687682cfe65d4d7b274a845ce17d091d68646ff54bc0959e2a06ad87543` |
| `sticky-notes/postits.py` | `247e7e9bbafde87c5441b3a53fd4eccd7d0914bfefa7e282c593b41259446551` |
| `sticky-notes/storage.py` | `61ca17c573ade36556496a5d907885e4328157abf34776bcf636c0e950b67be6` |
| `tests/helpers/command_panels.js` | `d17cd71ebac46cc85f273690d0d77b8766f2ebf1e393ca7375221ca53e44cede` |
| `tests/test_action_tooltip.js` | `98eeaa731f3e21379d5cc1745f233755c88920bdb1958d4e020630dfda2fa997` |
| `tests/test_audit.py` | `ee3b573599a8b827ce6bdf21d50cf5b553cc3682aabd8e4234903bfbfcf5c408` |
| `tests/test_collector_entrypoints.py` | `29692ae4180b22feda8e4f22341317d1003c1409c80b77bddc7a7a780d3d50fc` |
| `tests/test_command_output.js` | `d67ba8f235b061007c62827b648cd33af7a8fc0371f32092a378a9e80b275966` |
| `tests/test_dialog_dismiss.js` | `1804c141896a88bb432dd0eff8e2b9cc10386f0aeca5788045cd5f89fadbfff4` |
| `tests/test_eject.py` | `854405501e9cfc1165bfc13d339f7252954656103109a669257560ca0a07f3f7` |
| `tests/test_external_devices.py` | `e2f018c72f1b3bc2afb0ec0e62a367d73d91e6f5cd308c0efd3fd5d3f985f383` |
| `tests/test_frontend_modules.py` | `5e7839c624e780df9959dd2e3cc516d7ae31a48e75d19c968496b8fe2e8036ee` |
| `tests/test_group_layout.js` | `4052e80931300676b84642aac71274905a2d1bc8d8bfa057afd15f2091595044` |
| `tests/test_grouping.js` | `4376a7ef2c312c0646cadb096c753063131962de31b4eb3953bbd7eb66b7debf` |
| `tests/test_network_quality.py` | `2a9fca64fbdec9c9b499e509d82d2555300e5d2f885c827945275eba3ba2a407` |
| `tests/test_panel_composition.js` | `4140bae63693b126a55f3961e984e892c44514305c0ff1e93154ade0ff39365f` |
| `tests/test_planner_backend.py` | `6238ba3aa6bc21a634a66559f46efe9ab10d8826646fb5183cb28f1864242330` |
| `tests/test_pressure.py` | `254e63ebb3e9974877463215b954d7189fc16fa0cd6e3985b713193af5187a17` |
| `tests/test_pressure_ui.js` | `14308c30e95d868181601e8ecc1761b9dac689d2668d58924ab0e73c94e70a80` |
| `tests/test_processes_layout.js` | `1aa395e5c7a24bfc0ce50c0754f1060415e9c1f81dc9289acbfb28bc111d2712` |
| `tests/test_quality_ui.js` | `2d8f007f99e157f03ecabac04e8a534d17b34bbfa1480af2199d2ad416ca8878` |
| `tests/test_services.py` | `65dec842131cd99556dbf3787c55883ed8f578dd58ccd72944a11b4dda5b4cb3` |
| `tests/test_services_ui.js` | `d68ac167206c4938c7c4828789a1d84329045530384d67603ff44da52a417865` |
| `tests/test_settings_alignment.js` | `2cde1a338459de4d8c0cb69daee0ae0cd02bec19a74238b290fa8649a8fa2c07` |
| `tests/test_stats_storage_click.js` | `843529da37f68556ac4f27dade94f651482d02fdbcc31ef03e17bdce10414d48` |
| `tests/test_stop_collectors.py` | `277697151ef877487d2c8f9565884dab743b642cc5e6bb5aa71eb9e5b8e7a6bb` |
| `tests/test_storage.py` | `13b59b9cda34933089de731efae6779b2a622df4e156aaed3f1ff7b612ec66b2` |
| `tests/test_storage_ui.js` | `62d446e067688204de3915cc6e5e73a22859e18c3ae3ce1313524f9018d510ca` |
| `tests/test_super_ctrl_drag.js` | `509ba7e341abd04543d193da04a595e84d770f6b9cad64f61d5f7e8d8f2961af` |
| `tests/test_temperature_layout.js` | `c4c7724e80133d84206f65ce53daf70f227d0ad364849a316c4c01871f58dede` |
| `tests/test_widget_controller.js` | `501326887e8c01e85397184f444a239734c189a2cd5b24d1b43a33eb91e19172` |
| `widgets/armazenamento-widget.py` | `99aaabd341d8186674770aa47b1057b8a0796812bc97b23266721e2d14bff337` |
| `widgets/atualizacoes-widget.py` | `0ff8630f5e2805a817476d26f58f8d304fc33c6399a029432d28284734aa8e5f` |
| `widgets/clima-widget.py` | `796a9d4e0cc1e18c092d8d566213e668996d17214574e6341d5240b07684eedd` |
| `widgets/conexoes-inspect.py` | `9734879c7761840ca55a2072b65389a350c1b98e5078c2da6773463cf765e6f6` |
| `widgets/cpu-ram-widget.py` | `01be3e61be1154d965ee65ffb272f2a6f6880e178de31c2304bfa1d0804b864c` |
| `widgets/docker-widget.py` | `bd41cb3b8112ae78a5e2b829314c07cd835d801ae9ea49b49c9dde081358e812` |
| `widgets/external_storage.py` | `11fcfeee7b398e783015c5ce25d754399bb0ca8b0c2337ee4ee5ff2a46c61dc8` |
| `widgets/firewall-widget.py` | `c5ff91a79972a470a2449bd037fb3f7a71e470758b8b66c21fa572a92d8bd704` |
| `widgets/firewall_patterns.py` | `c454dc8d3c9223545c8d20f10f7b49d5479c671a68dcd0fdc7cd08b8a3b35be1` |
| `widgets/hardware-details.py` | `5d9dd595465688f87fe3b9954898e4ee0684536359e06a76a587821e7ea3ed5b` |
| `widgets/limpeza-linux.py` | `c970b51faa382c148a2d708284a54c992c4f123de5cb4ab709c4c75fb83237b0` |
| `widgets/metrics-worker.py` | `4bcbe5a6a6cb41d6f6023593a63d93337109a948d651293ac7ea890e5b7941a1` |
| `widgets/network_quality.py` | `5fa5fed4757954b90aa214c8e3d39d652cb5a4444e59996e9c0304d787e39905` |
| `widgets/pressure_metrics.py` | `9c9beb16778f4dae6f3a2f8f81a82aa6d2d8500b69df7d9f121a21a8609b0a47` |
| `widgets/processos-widget.py` | `c02e2a4d5cc7995fafec3a81938c4273606b4cae673c7237e56ae7cd2e24f876` |
| `widgets/rede-widget.py` | `ec9dc1c4fc8920ab2ef6f7c250124e73558d9bd5eac0fd78f9b5822bb6f30fac` |
| `widgets/seguranca-widget.py` | `4ffdbc7ba0e860c43549e01896378b686a09ba3106267015882d7b257c582e8a` |
| `widgets/servicos-widget.py` | `b8e877a87ad0782e452f083b3a63578bc13792fe0061ab01c969884c56e65912` |
| `widgets/temperaturas-widget.py` | `164a212c71d9e5d9999c3cb3842da7459e8f87739b63e8f775e29d6a56b48f56` |
| `widgets/widget_runtime.py` | `3a62d9c4e54ba6e41d787d82b351c71049d7092a0d32fc21b2c8390067c49ba2` |

Logs temporários: `/tmp/orbitz-integrated-audit/` (results.json, manifesto, grafo de imports, equivalências AST e saída integral por entrypoint); não são dependência da entrega. Saída Python da execução atual:

```text
test_cache_rejects_symlink_and_nonfinite_time (test_audit.RuntimeTests) ... ok
test_cache_roundtrip_and_invalid_name (test_audit.RuntimeTests) ... ok
test_eof_does_not_execute_and_enter_does (test_audit.RuntimeTests) ... ok
test_output_limit (test_audit.RuntimeTests) ... ok
test_timeout_includes_child_pipes (test_audit.RuntimeTests) ... ok
test_watchdog_survives_parent_exit (test_audit.RuntimeTests) ... ok
test_docker_inspection_caps (test_audit.WidgetTests) ... ok
test_docker_url_rejects_unsafe_values (test_audit.WidgetTests) ... ok
test_firewall_cache_structure (test_audit.WidgetTests) ... ok
test_firewall_memory_batch_limit (test_audit.WidgetTests) ... ok
test_firewall_persistence_noise_and_expiry (test_audit.WidgetTests) ... ok
test_network_handles_truncated_routes_and_rates (test_audit.WidgetTests) ... ok
test_process_query_bounds (test_audit.WidgetTests) ... ok
test_process_startup_path_is_shell_quoted (test_audit.WidgetTests) ... ok
test_sensor_known_and_unknown_descriptions (test_audit.WidgetTests) ... ok
test_sensor_missing_readings_are_not_exported (test_audit.WidgetTests) ... ok
test_storage_rejects_recursive_or_wrong_mounts (test_audit.WidgetTests) ... ok
test_update_unknown_action_and_shared_confirmation (test_audit.WidgetTests) ... ok
test_weather_malformed_values (test_audit.WidgetTests) ... ok
test_import_does_not_collect_sleep_spawn_or_print (test_collector_entrypoints.CollectorEntrypoints) ... ok
test_network_rate_and_details_prefix (test_collector_entrypoints.CollectorEntrypoints) ... ok
test_security_summary_skips_dns (test_collector_entrypoints.CollectorEntrypoints) ... ok
test_temperatures_fallback_and_details (test_collector_entrypoints.CollectorEntrypoints) ... ok
test_worker_style_exec_still_runs_cpu_entrypoint (test_collector_entrypoints.CollectorEntrypoints) ... ok
test_busy_device_does_not_power_off (test_eject.EjectTests) ... ok
test_stale_identity_does_not_unmount (test_eject.EjectTests) ... ok
test_unmount_all_verify_then_power_off (test_eject.EjectTests) ... ok
test_physical_devices_separate_and_partitions_aggregated (test_external_devices.ExternalDevicesTests) ... ok
test_document_get_keeps_token_boundary (test_frontend_modules.YouTubeBoundaryTests) ... ok
test_invalid_requests_and_comment_cache (test_frontend_modules.YouTubeBoundaryTests) ... ok
test_local_key_permissions_and_validation (test_frontend_modules.YouTubeBoundaryTests) ... ok
test_loopback_origin_and_token_required_before_api (test_frontend_modules.YouTubeBoundaryTests) ... ok
test_search_and_missing_key_contract (test_frontend_modules.YouTubeBoundaryTests) ... ok
test_gateway_and_bounded_probe (test_network_quality.QualityTests) ... ok
test_parsing (test_network_quality.QualityTests) ... ok
test_invalid_calendar_and_unsafe_urls_preserve_error_contract (test_planner_backend.CalendarTests) ... ok
test_shared_normalization_identity_recurrence_and_alarms (test_planner_backend.CalendarTests) ... ok
test_atomic_failure_preserves_original_and_cleans_temporary (test_planner_backend.PersistenceTests) ... ok
test_atomic_permissions_and_durability_order (test_planner_backend.PersistenceTests) ... ok
test_cli_concurrent_edits_are_serialized (test_planner_backend.PersistenceTests) ... ok
test_drafts_and_external_accounts_remain_independent (test_planner_backend.PersistenceTests) ... ok
test_store_backups_restore_and_retention (test_planner_backend.PersistenceTests) ... ok
test_task_timesheet_contract_and_midnight_timer (test_planner_backend.PersistenceTests) ... ok
test_duplicate_samples_are_rejected (test_pressure.PressureTests) ... ok
test_rejects_invalid_and_nonfinite (test_pressure.PressureTests) ... ok
test_thresholds_multiple_resources_and_missing (test_pressure.PressureTests) ... ok
test_caps_details_and_read_only (test_services.ServicesTests) ... ok
test_empty_and_permission_failure (test_services.ServicesTests) ... ok
test_malformed_list_is_not_healthy (test_services.ServicesTests) ... ok
test_missing_details_are_reported_as_partial (test_services.ServicesTests) ... ok
test_rejects_option_names_and_nonfailed_units (test_services.ServicesTests) ... ok
test_children_created_by_worker_threads_are_found (test_stop_collectors.StopCollectorsTests) ... ok
test_detached_child_is_stopped_with_parent (test_stop_collectors.StopCollectorsTests) ... ok
test_rejects_system_pids (test_stop_collectors.StopCollectorsTests) ... ok
test_wrong_identity_does_not_kill (test_stop_collectors.StopCollectorsTests) ... ok
test_deduplicates_bind_mounts (test_storage.StorageTests) ... ok
test_external_content_is_bounded_and_siblings_not_inherited (test_storage.StorageTests) ... ok
test_failure_not_healthy (test_storage.StorageTests) ... ok
test_selection_filters_by_device_and_rejects_stale_identity (test_storage.StorageTests) ... ok
test_smart_unavailable_and_alert (test_storage.StorageTests) ... ok
test_unmounted_partition_without_usage (test_storage.StorageTests) ... ok
test_unmounted_usb_is_only_in_external_view (test_storage.StorageTests) ... ok

----------------------------------------------------------------------
Ran 62 tests in 2.507s

OK
```
