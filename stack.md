# Stack dos widgets Orbitz

Inventário inicial em **17/10/2026**, atualizado em **21/10/2026** para refletir o conversor unificado e a revisão da sprint.

## Estado atual das fontes e instalação

A instalação local já usa os módulos refatorados e os coletores em `~/.local/share/orbitz-widgets/collectors`; o atualizador confirmou zero arquivos/comandos pendentes na conferência de 18/10/2026. Os mapas de pastas históricas abaixo descrevem a origem anterior, preservada para referência e rollback; não são mais os caminhos configurados dos dez comandos migrados. Instalação em máquina limpa ainda não foi validada. Verificação histórica desse marco: 71 testes Python, 17 arquivos Node.js e GJS/PangoCairo aprovados; clique RAM e validação visual/interativa permanecem pendentes conforme README/backlog.

## Visão geral

O conjunto combina uma extensão do GNOME Shell, aplicativos nativos GTK e coletores Python. A configuração visual fica no GSettings; os dados da agenda ficam em JSON e os Sticky Notes usam SQLite.

| Componente | Stack e responsabilidade |
|---|---|
| Widgets da área de trabalho | JavaScript/GJS, GNOME Shell, St e Clutter; relógio, métricas, atalhos, controlador e cartões de alerta. |
| Configurações dos widgets | JavaScript/GJS, GTK 4 e libadwaita; edição de elementos, aparência, posições e grupos. |
| Calendário, tarefas e timesheets | Python 3, PyGObject e GTK 3; interface nativa, tabelas, histórico, rascunhos e backups. |
| Sticky Notes | Mini app independente, distribuído no repositório `orbitz-sticky-notes`; não faz parte dos atalhos ou preferências dos widgets. |
| Coletores do sistema | Python 3, `/proc`, `/sys` e ferramentas Linux; CPU, RAM, processos, rede, sensores, serviços, atualizações, firewall e Docker. `widgets/clima-widget.py` consulta a Open-Meteo para resumo atual e previsão de sete dias, com cache por local/unidade; a modal pesquisa cidades via Open-Meteo Geocoding, mostra até dez matches Cidade · Região · País com dados GeoNames e atribuição. Preferências privadas de local/unidade ficam no XDG, com gravação atômica e CAS. O conversor unificado usa `widgets/fx_rates.py` e `currency-widget.py`: modo Fiat consulta Frankfurter v2 (referência diária em dias úteis) e modo Crypto consulta tickers CoinPaprika, preservando precisão suficiente para valores cripto pequenos. Ambos usam atualização automática a cada quatro horas; a modal oferece atualização manual, inversão persistida e calculadora. Atribuição CoinPaprika aparece na modal; uso comercial dos dados requer licença compatível. WX-01 passou testes sintéticos locais; consulta online e inspeção visual/instalação GNOME ainda não foram verificadas. |
| Calendários externos | Python, HTTPS, CalDAV e iCalendar; consulta ao iCloud e assinaturas ICS, com conversão explícita de eventos em tarefas. |
| YouTube | Mini app independente, distribuído no repositório `orbitz-youtube-wrapper`; busca e preferências são próprias do aplicativo. |
| Lançadores | Atalhos para Gemini e btop; Sticky Notes e YouTube são iniciados pelo menu de aplicativos do ambiente. |
| Caffeine Indicator | Aplicativo externo, configurado para iniciar automaticamente com a sessão. |

### Comunicação entre componentes

- **GObject/signals:** eventos das interfaces e dos widgets.
- **Gio.Subprocess + JSON:** execução dos coletores e operações da agenda.
- **D-Bus:** instância única dos aplicativos, encerramento dos Sticky Notes, mídia/MPRIS e cofre de senhas.
- **Monitoramento de arquivos:** atualização dos alertas ao mudar tarefas ou caches de eventos.
- **HTTPS:** clima, calendários, assinaturas e serviços do YouTube.

## Dependências

### Plataforma e bibliotecas nativas

| Dependência | Breve descrição |
|---|---|
| Linux com GNOME Shell | Ambiente em que a extensão e os widgets são executados. |
| GNOME Shell **42.9** | Versão encontrada na máquina; o manifesto da extensão declara suporte às versões 42, 43 e 44. |
| GJS **1.72.4** | Runtime JavaScript da extensão e das preferências. |
| Mutter / Meta | Integração com janelas, monitores, espaços de trabalho e sobreposição. |
| St, Clutter e Graphene | Componentes visuais, posicionamento, geometria e entrada dos widgets. |
| GLib, Gio e GObject | Laço de eventos, sinais, arquivos, processos e comunicação D-Bus. |
| Pango | Renderização, formatação e quebra de texto. |
| GSettings / dconf | Persistência das configurações dos widgets. |
| GTK 3 e GDK | Interface GTK da agenda. Os mini apps têm dependências próprias documentadas em seus repositórios. |
| GTK 4 e libadwaita | Interface de preferências da extensão. |
| Python **3.10.12** | Runtime encontrado para os aplicativos e coletores. |
| PyGObject (`gi`, pacote `python3-gi`) | Acesso do Python às bibliotecas GTK, Gio e demais APIs nativas. |
| GObject Introspection / typelibs | Descrições das APIs nativas usadas por Python e GJS. |
| WebKitGTK / WebKit2 **4.0** | Usado somente pela fonte legada do YouTube preservada em `extension/youtube-widget/`; não é requisito dos widgets ativos. |
| libsecret / Secret Service | Armazena e recupera a senha específica de aplicativo do iCloud. |
| GNOME Keyring ou cofre compatível | Implementação do serviço de senhas da sessão. |
| D-Bus de sessão e do sistema | Comunicação com aplicativos, mídia e serviços do desktop. |
| SQLite | Usado pelas fontes legadas de Sticky Notes preservadas neste repositório; o mini app independente mantém seu próprio banco e empacotamento. |
| libcanberra / `canberra-gtk-play` | Reprodução do som de alarme do sistema. |
| Tema de sons freedesktop | Disponibiliza o evento sonoro `alarm-clock-elapsed`. |
| X11 / XWayland | Backend explicitamente solicitado pelos aplicativos GTK lançados pela extensão. |
| tzdata do sistema | Catálogo local de nomes de cidades/regiões e identificadores IANA para seleção de fusos horários; não exige conexão ou GWeather. O clima exibido é consultado no Open-Meteo. |

Os typelibs correspondentes incluem `Gtk-3.0`, `Gtk-4.0`, `Adw-1`, `WebKit2-4.0` e `Secret-1`.

### Pacotes Python adicionais

| Pacote | Versão / origem | Breve descrição |
|---|---|---|
| `icalendar` | **7.3.0**, em `planner/vendor/` | Leitura de eventos ICS, fusos e alarmes VALARM. |
| `recurring-ical-events` | **3.8.2**, em `planner/vendor/` | Expansão de recorrências e suas exceções por período. |
| `python-dateutil` | **2.9.0.post0**, em `planner/vendor/` | Regras de recorrência e operações de datas. |
| `tzdata` | **2026.5**, em `planner/vendor/` | Base de fusos horários. |
| `x-wr-timezone` | **2.0.1**, em `planner/vendor/` | Compatibilidade com fusos definidos em arquivos iCalendar. |
| `six` | **1.17.0**, em `planner/vendor/` | Compatibilidade transitiva do `python-dateutil`. |
| `typing_extensions` | **4.16.0**, em `planner/vendor/` | Recursos de tipagem exigidos pelas bibliotecas de calendário. |
| `click` | **8.5.0**, em `planner/vendor/` | Dependência transitiva para ferramentas de linha de comando. |
| `defusedxml` | Biblioteca do sistema | Leitura protegida das respostas XML do CalDAV. |

As versões empacotadas estão registradas em `planner/apple-calendar-requirements.txt`. A conexão iCloud usa o cliente HTTP/XML próprio do projeto; não depende do pacote Python `caldav`. As senhas são acessadas por libsecret, sem depender do pacote Python `keyring`.

### Biblioteca padrão do Python

Estes módulos já acompanham o Python; não exigem instalação por pip.

| Módulos | Breve descrição |
|---|---|
| `datetime`, `calendar`, `time`, `zoneinfo` | Datas, calendário, intervalos, contagem regressiva e fusos. |
| `json`, `csv`, `sqlite3` | Persistência, comunicação e exportação de dados. |
| `pathlib`, `os`, `sys`, `shutil`, `tempfile`, `stat` | Arquivos, diretórios, permissões e gravações temporárias. |
| `fcntl`, `contextlib` | Bloqueio de arquivos e limpeza controlada de recursos. |
| `subprocess`, `signal`, `selectors`, `shlex`, `runpy` | Execução, supervisão e encerramento de processos. |
| `threading`, `concurrent.futures` | Operações em segundo plano e consultas paralelas limitadas. |
| `urllib.request`, `urllib.parse`, `urllib.error`, `http.server` | Clientes HTTP/HTTPS dos recursos do Orbitz e servidor local da fonte legada do YouTube. |
| `socket`, `ipaddress` | Resolução de nomes, endereços e validação de destinos. |
| `hashlib`, `uuid`, `secrets`, `base64` | Identificadores, hashes, tokens locais e autenticação HTTP. |
| `gzip`, `io`, `html`, `re` | Conteúdo comprimido, buffers, textos e validações. |
| `math`, `itertools`, `heapq`, `ctypes` | Cálculos, classificação e acesso pontual a recursos nativos. |

### Ferramentas e aplicativos por recurso

| Dependência | Breve descrição |
|---|---|
| `/proc` e `/sys` | Métricas e informações de processos, hardware e rede fornecidas pelo kernel. |
| `setsid` e `timeout` | Isolamento e limite de execução dos coletores. |
| `lsblk` e `lscpu` | Inventário de discos e processador. |
| `udisksctl` / UDisks | Desmontagem e ejeção de dispositivos externos. |
| `dmidecode`, opcional | Leitura dos módulos e limites de RAM informados pelo firmware. |
| `sensors` / lm-sensors | Leitura adicional das temperaturas de hardware. |
| `nvidia-smi`, opcional | Temperatura de GPU NVIDIA quando disponível. |
| `ip`, `ss` e `ping` | Interfaces, conexões, latência, perda e qualidade de rede. |
| `getent` | Resolução de nomes e informações do sistema. |
| `systemctl` e `journalctl` | Estado dos serviços e consulta aos registros do sistema. |
| APT | Consulta e ações de atualização dos pacotes Ubuntu/Debian. |
| Snap e Flatpak, opcionais | Consulta e atualização desses formatos quando instalados. |
| Docker CLI e daemon, opcionais | Inventário e ações do widget de contêineres. |
| Bash e Tilix | Execução das ações explicitamente acionadas pelo usuário; Tilix é o terminal gráfico usado por essas ações. |
| `sudo` | Elevação em ações específicas, como firmware e manutenção. |
| Tilix | Dependência para abrir ações interativas no terminal; todas as ações do Orbitz usam este terminal. |
| btop, opcional | Monitor de sistema usado pelo lançador quando instalado. |
| Google Chrome | Lançador do Gemini em janela de aplicativo. |
| Player compatível com MPRIS | Controles de mídia para players reconhecidos, incluindo Spotify e Chrome/Chromium. |
| Caffeine Indicator | Indicador externo mantido na inicialização automática. |
| Speedtest CLI da Ookla, opcional | Binário incluído na extensão para o teste de velocidade. |

### Serviços externos

| Serviço / protocolo | Breve descrição |
|---|---|
| Open-Meteo | Previsão e condições meteorológicas do widget de clima. |
| Apple iCloud / CalDAV | Consulta dos calendários da conta com senha específica de aplicativo. |
| ICS / iCalendar por HTTPS | Assinaturas públicas ou privadas por link, sem modificar os eventos de origem. |
| Calendário público brasileiro do Google | Fonte separada de feriados e datas comemorativas; dispensa conta Google. |
| Gemini na web | Serviço aberto pelo lançador no Chrome. |
| WHOIS / RDAP na web | Consulta externa de endereços a partir dos detalhes de conexões. |

### Ferramentas de desenvolvimento e verificação

| Ferramenta | Breve descrição |
|---|---|
| Node.js | Verificação de sintaxe e testes da lógica JavaScript fora do GNOME Shell. |
| `unittest`, `unittest.mock`, `ast` e `py_compile` | Testes e validação dos módulos Python. |
| Broadway / `broadwayd` | Backend GTK utilizado nos testes locais de interface. |
| `dbus-run-session` | Sessão D-Bus isolada para os testes gráficos. |
| Pycairo | Captura das interfaces GTK para inspeção visual nos testes. |
| Xephyr e GNOME Shell isolado | Ferramentas utilizadas em verificações anteriores da extensão. |
| pip | Preparação das dependências vendorizadas de calendário. |

## Mapa simples de pastas e arquivos

Os caminhos abaixo são relativos à pasta pessoal do usuário (`~`). As descrições agrupam arquivos auxiliares e imagens para manter o mapa compacto.

```text
~/.local/share/
├── gnome-shell/extensions/azclock@azclock.gitlab.com/
│   ├── metadata.json                  # Identificação e compatibilidade GNOME
│   ├── extension.js                   # Widgets, controlador, métricas e mídia
│   ├── prefs.js                       # Entrada das preferências
│   ├── utils.js                       # Utilitários de configuração
│   ├── dragging.js                    # Arraste e limites por monitor
│   ├── grouping.js                    # Agrupamento dos widgets
│   ├── stop-collectors.py             # Encerramento dos processos coletores
│   ├── schemas/                       # Schema GSettings e versão compilada
│   ├── settings/                      # Páginas das preferências
│   ├── media/                         # Ícones, controles e peças dos relógios
│   ├── planner/
│   │   ├── calendar-app.py            # Janela principal da agenda
│   │   ├── month_calendar.py          # Dias, destaques e indicadores de feriado
│   │   ├── calendar_selector.py       # Dropdown de fontes de calendário
│   │   ├── timesheet.py               # Regras, cálculos e exportação
│   │   ├── timesheet_ui.py            # Interface das timesheets
│   │   ├── store.py                   # Tarefas, histórico e backups
│   │   ├── ui_state.py                # Preferências e rascunhos persistentes
│   │   ├── planner_tools.py           # Consulta das arquivadas e recuperação
│   │   ├── external_ui.py             # Conexões e conversão de evento em tarefa
│   │   ├── external_store.py          # Contas, caches e acesso ao cofre
│   │   ├── apple_client.py            # Cliente CalDAV e leitura de eventos
│   │   ├── ics_client.py              # Cliente de assinaturas por link
│   │   ├── calendar.js                # Cartões de alerta no GNOME Shell
│   │   ├── reminders.js               # Agendamento e contagem regressiva
│   │   ├── planner.js / editor.py     # Componentes legados preservados
│   │   ├── apple-calendar-requirements.txt
│   │   └── vendor/                    # Bibliotecas Python empacotadas
│   ├── notes-widget/                  # Ícone legado; não há mais atalho ativo
│   ├── youtube-widget/                # Fonte legada preservada; mini app fica em repositório próprio
│   ├── gemini-widget/                 # Ícone do lançador Gemini
│   └── speedtest                      # Executável do teste de velocidade
├── orbitz-postits/
│   ├── app/postits.py                 # Interface e ciclo de vida das notas
│   ├── app/storage.py                 # Persistência SQLite e backups
│   ├── app/postits.svg                # Ícone
│   ├── notes.sqlite3                 # Banco das notas
│   └── backups/                       # Cópias das notas
└── orbitz-widgets/
    ├── notes.json                     # Tarefas, timesheets e dados legados
    ├── planner-ui.json                # Rascunhos e preferências da agenda
    ├── external-calendars.json         # Conexões e eventos em cache
    ├── reminder-state.json            # Alertas anunciados e dispensados
    └── planner-backups/               # Histórico de cópias da agenda

~/.config/
├── autostart/
│   ├── caffeine-indicator.desktop     # Inicialização do indicador Caffeine
│   └── orbitz-postits.desktop         # Inicialização automática desativada
└── orbitz-widgets/
    ├── youtube.json                   # Chave histórica; o mini app usa configuração isolada
    └── update-actions.json            # Ações adicionais, quando configuradas

~/.cache/orbitz-widgets/                # Caches dos coletores e da fonte legada do YouTube
~/.local/share/applications/            # Atalhos .desktop dos aplicativos
```

### Coletores referenciados pela configuração atual

Parte dos scripts ainda é executada diretamente de diretórios de trabalho anteriores:

```text
~/Documents/Codex/
├── 2026-10-08/quan/outputs/
│   ├── clima-widget.py
│   ├── cpu-ram-widget.py
│   ├── processos-widget.py
│   ├── rede-widget.py
│   ├── seguranca-widget.py
│   ├── servicos-widget.py
│   ├── temperaturas-widget.py
│   ├── metrics-worker.py              # Coleta persistente compartilhada
│   ├── widget_runtime.py              # Timeouts, subprocessos e caches
│   ├── pressure_metrics.py            # Pressão de recursos do kernel
│   ├── network_quality.py             # Qualidade da conexão
│   ├── external_storage.py            # Dispositivos externos
│   ├── hardware-details.py            # Detalhes de CPU e RAM
│   ├── conexoes-inspect.py            # Inspeção de conexões
│   ├── armazenamento-widget.py        # Auxiliar de armazenamento
│   └── limpeza-linux.py               # Ações de limpeza
├── 2026-10-09/pngrub-ae-in-f14-1e100-net/outputs/
│   ├── firewall-widget.py
│   └── auxiliares Python              # Runtime e consultas relacionadas
└── 2026-10-11/https-rdap-org-ip-2a06-3a98c1/outputs/
    ├── atualizacoes-widget.py
    ├── docker-widget.py
    └── auxiliares Python              # Runtime e consultas relacionadas
```

Esses caminhos fazem parte da instalação atual: mover ou remover as pastas exige atualizar os comandos salvos no GSettings. Os arquivos `*.backup-*`, caches e `__pycache__/` foram omitidos do mapa.

## Persistência e execução

- A agenda usa JSON com bloqueio de arquivo, gravação atômica e retenção das 60 cópias mais recentes do histórico.
- Os Sticky Notes usam SQLite em modo WAL, com transações e backups próprios.
- Credenciais iCloud ficam no Secret Service; o arquivo de conexões guarda metadados e caches, sem a senha.
- Eventos externos só viram tarefas mediante confirmação; tarefas e timesheets permanecem locais e independentes das conexões.
- Os alertas do relógio usam tarefas e eventos já sincronizados em cache; a sincronização externa é executada pela agenda aberta.
- A interface dos widgets roda no GNOME Shell; os aplicativos e coletores rodam em processos separados.
- Os aplicativos GTK são iniciados com `GDK_BACKEND=x11`, inclusive em sessões Wayland com XWayland.
- As ferramentas opcionais são necessárias apenas para seus respectivos recursos; o manifesto GNOME não garante compatibilidade com versões posteriores à 44.

## Modularização das fontes — RF-01 (18/10/2026)

O backend do checkout passou a separar `extension/planner/calendar_events.py` (iCalendar/recorrências/VALARM), `credential_vault.py` (acesso tardio a libsecret) e `atomic_json.py` (substituição JSON durável). Apple/ICS reutilizam a normalização; store, external_store e ui_state reutilizam a escrita mantendo locks e políticas próprias. `widgets/firewall_patterns.py` contém análise pura UFW, separada de journal/cache/CLI. Cinco coletores têm `main()`/guarda de execução, mantendo o contrato do worker. Não foram acrescentadas dependências externas.

Este registro descreve fontes refatoradas, não a instalação ativa. Os quatro módulos novos devem acompanhar os chamadores ao preparar distribuição futura. Evidências específicas: `docs/audits/2026-10-18-backend-refactor.md`; auditoria integrada concluída, com limites no relatório.

O frontend do checkout separa composição (`extension/commandPanels.js`) e oito módulos de painéis em `extension/panels/`: common, updates, temperatures, storage, resources, network, docker e firewall. A composição ocorre antes de `GObject.registerClass`. `settings/TimeZoneDialog.js`, `planner/task_timesheet_ui.py`, `sticky-notes/card.py` e `youtube-widget/{youtube_api,youtube_server}.py` isolam responsabilidades antes nos pontos de entrada. Esses 14 módulos frontend também são necessários na distribuição futura, sem novas dependências externas declaradas. Relatório: `docs/audits/2026-10-18-frontend-refactor.md`. Validações específicas não comprovam execução gráfica; captura Broadway foi bloqueada por permissões do ambiente.

Auditoria integrada RF-01 concluída: `docs/audits/2026-10-18-integrated-audit.md`; verificações locais/importações aprovadas, sem regressão impeditiva reproduzida no escopo revisado. A validação gráfica/interativa permanece pendente e nenhum ganho de desempenho foi medido.

## Identidade própria — ID-01 (fontes e migração implementadas)

As fontes passam a identificar Orbitz Widgets for GNOME, de Felipe Santiago/orbitzone, com URL GitHub do projeto, UUID `orbitz-widgets@orbitzone.github.io` e schema `org.gnome.shell.extensions.orbitz-widgets` (`/org/gnome/shell/extensions/orbitz-widgets/`). O domínio gettext azclock e XML schema legado são preservados para compatibilidade/migração; classes internas antigas não representam identidade pública nem requerem renomeação. Não há alteração de runtime/dependências ou da licença por essa mudança.

A instalação local já foi migrada e ativada com o UUID Orbitz; a instalação antiga permanece desativada para retorno. Migrador auditado separa cópia/configuração reversíveis da ativação manual; não mover dados da agenda/notas nem credenciais, e nunca ativar duas extensões. O histórico de paths acima permanece evidência do estado anterior; não trocar UUID apenas renomeando pasta.

ID-01: confira `docs/operations/identity-migration.md` e `docs/audits/2026-10-18-identity-audit.md`. Suíte integrada83 testes Python/18 arquivos Node/2 testes GJS/110 verificações de sintaxe e rechecagem final11 testes do migrador após ajuste de rollback; preparo/ativação foram executados pelo usuário e conferidos pelo supervisor; não houve troca automática pelo agente.

## Invoice PDF — INV-01

`planner_menu.py` compõe o menu ao lado da data; `invoice_ui.py` mantém formulário e prévia separados. `invoice.py` calcula minutos/Decimal e valida o snapshot; `invoice_profiles.py` persiste perfis privados com lock e escrita atômica; `invoice_pdf.py` renderiza PDFs PT/EN com ReportLab e fontes DejaVu Sans incorporadas. Dependências da exportação: `python3-reportlab` e `fonts-dejavu-core`; imports da biblioteca PDF são tardios.

Perfil local: `~/.local/share/orbitz-widgets/invoice-profiles.json`, modo 0600, separado de `notes.json`, credenciais e backups da agenda. Emitente/idioma globais; cliente/taxa/moeda por ID da timesheet. PDF salvo privadamente em destino escolhido, com confirmação para substituir. Nenhum serviço externo é consultado e os registros de horas permanecem intactos. Reabrir a agenda após instalação carrega os módulos novos; logout não é necessário.

INV-02 (19/10/2026): seletor visual isolado para mês civil/histórico/intervalo inclusivo com um calendário. Navegação e seleção são eventos distintos; o formulário passa start/end ISO ao domínio existente. Sem novas dependências, migração de perfis ou alterações nos registros. Aplicação e validação GTK real permanecem separadas da verificação local.

## Histórico de invoices — INV-03 (19/10/2026)

`invoice_history.py` mantém PDFs e metadados privados separados dos dados vivos; `invoice_history_ui.py` apresenta consulta/cópia/exclusão e grupos por timesheet/cliente/mês de emissão. O menu e a sessão de exportação integram o acervo. Armazenamento em `~/.local/share/orbitz-widgets/invoices` (XDG), diretórios privados/arquivos0600 e IDs internos; nenhuma nova dependência externa. Exportar cópia ou excluir acervo não modifica o PDF externo original nem horas/perfis. Novas emissões apenas; não há varrimento de arquivos antigos.

## Versões importadas e gov.br assistido — INV-04 (19/10/2026)

Armazenamento separado de versões privadas vinculadas à invoice original; bytes/hashes preservados, sem substituir arquivos emitidos nem regenerar PDFs. Interface do histórico oferece cópia+portal, importação confirmada de versão e acesso ao VALIDAR. URLs oficiais fixas abertas via navegador, nenhuma chamada automática de upload/autenticação, nenhum segredo novo. Estado pendente sem motor criptográfico; nenhuma dependência de assinatura acrescentada. Compatibilidade, isolamento de corrupção e limites de exclusão continuam exigidos; reabrir agenda após aplicação, sem logout GNOME.

INV-04 módulos: `invoice_signatures.py` isola importação/lista/cópia/exclusão de versões; `invoice_signatures_ui.py` isola assistente e diálogo. `invoice_history.py` mantém compatibilidade e exportação de bytes compartilhada; `invoice_history_ui.py` integra ações. Auditoria62 testes e seis hashes conferidos; instalação ainda pendente neste marco.

## Orbitz Workspace — WSP-01

`workspace_ui.py` compõe as áreas e resumo Hoje; `timesheet_context_ui.py` edita nome/referências; `workspace_backup_ui.py` conduz backup e restauração com parada segura da UI. Backend: `sheet_context.py` valida referências, `invoice_duplicates.py` compara horários/proveniência e `invoice_payments.py` guarda informação manual separada dos PDFs. `workspace_backup.py` aplica whitelist/manifesto/limites/locks estáveis/CAS e recuperação de falhas controladas; exclui credenciais/externos/Sticky Notes/GSettings. Contexto opcional em snapshots/PDF mantém leitura dos históricos antigos. Novos módulos Python acompanham o app pelo atualizador; nenhuma dependência externa nova.

## Google Calendar e Calendly — CAL-01

`calendar_http.py` limita HTTPS a hosts oficiais, recusa redirecionamentos e impõe limites/tempos; `google_oauth.py` recebe OAuth desktop em loopback com state/PKCE; `google_client.py` e `calendly_client.py` consultam calendários/eventos com paginação. `calendar_api_events.py` normaliza datas/recorrências/cancelamentos no contrato do cache existente. `calendar_accounts.py` coordena ciclo de conexão, renovação e remoção com locks; `credential_vault.ProviderVault` separa grants/PAT no Secret Service. `provider_connection_ui.py` mantém formulários e cancelamento com aceite da interface; `external_ui.py` integra as rotas. Sem nova dependência Python externa; libsecret/gi e vendor de calendários já existentes.

Configuração real Google/PAT Calendly é externa ao repositório: [guia](docs/operations/calendar-integrations.md). Não há credencial compartilhada embutida, escrita remota de eventos ou servidor de webhooks. Teste de callback real pode exigir ambiente fora do sandbox; mocks e revisão não provam autorização com conta real.

CAL-06: day_activity.py centraliza projeções somente leitura de tarefas/horas, eventos da fonte selecionada e feriados conhecidos de outras fontes. Calendar-app/external_ui/month_calendar compartilham critérios para marcações e conteúdo diário; nenhuma alteração de persistência ou autenticação. Link de ativação da API fica na ajuda opcional do diálogo Google, com responsabilidade explícita do mantenedor.
