# Stack dos widgets Orbitz

Inventário inicial em **17/10/2026**, atualizado em **18/10/2026** após RF-01 e atualização local.

## Estado atual das fontes e instalação

A instalação local já usa os módulos refatorados e os coletores em `~/.local/share/orbitz-widgets/collectors`; o atualizador confirmou zero arquivos/comandos pendentes na conferência de 18/10/2026. Os mapas de pastas históricas abaixo descrevem a origem anterior, preservada para referência e rollback; não são mais os caminhos configurados dos dez comandos migrados. Instalação em máquina limpa ainda não foi validada. Suíte completa atual: 71 testes Python, 17 arquivos Node.js e GJS/PangoCairo aprovados; clique RAM e validação visual/interativa permanecem pendentes conforme README/backlog.

## Visão geral

O conjunto combina uma extensão do GNOME Shell, aplicativos nativos GTK e coletores Python. A configuração visual fica no GSettings; os dados da agenda ficam em JSON e os Sticky Notes usam SQLite.

| Componente | Stack e responsabilidade |
|---|---|
| Widgets da área de trabalho | JavaScript/GJS, GNOME Shell, St e Clutter; relógio, métricas, atalhos, controlador e cartões de alerta. |
| Configurações dos widgets | JavaScript/GJS, GTK 4 e libadwaita; edição de elementos, aparência, posições e grupos. |
| Calendário, tarefas e timesheets | Python 3, PyGObject e GTK 3; interface nativa, tabelas, histórico, rascunhos e backups. |
| Sticky Notes | Python 3, GTK 3 e SQLite; notas independentes da extensão, com salvamento e recuperação. |
| Coletores do sistema | Python 3, `/proc`, `/sys` e ferramentas Linux; CPU, RAM, processos, rede, sensores, serviços, atualizações, firewall e Docker. |
| Calendários externos | Python, HTTPS, CalDAV e iCalendar; consulta ao iCloud e assinaturas ICS, com conversão explícita de eventos em tarefas. |
| YouTube | Python, GTK 3, WebKitGTK e HTML/CSS/JavaScript; janela com player incorporado e servidor HTTP local. |
| Lançadores | Atalhos para Sticky Notes, YouTube, Gemini e btop; abertura dos respectivos aplicativos. |
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
| GTK 3 e GDK | Interface da agenda, Sticky Notes e YouTube. |
| GTK 4 e libadwaita | Interface de preferências da extensão. |
| Python **3.10.12** | Runtime encontrado para os aplicativos e coletores. |
| PyGObject (`gi`, pacote `python3-gi`) | Acesso do Python às bibliotecas GTK, Gio e demais APIs nativas. |
| GObject Introspection / typelibs | Descrições das APIs nativas usadas por Python e GJS. |
| WebKitGTK / WebKit2 **4.0** | Motor web da janela do YouTube. |
| libsecret / Secret Service | Armazena e recupera a senha específica de aplicativo do iCloud. |
| GNOME Keyring ou cofre compatível | Implementação do serviço de senhas da sessão. |
| D-Bus de sessão e do sistema | Comunicação com aplicativos, mídia e serviços do desktop. |
| SQLite | Banco local dos Sticky Notes, acessado pela biblioteca padrão do Python. |
| libcanberra / `canberra-gtk-play` | Reprodução do som de alarme do sistema. |
| Tema de sons freedesktop | Disponibiliza o evento sonoro `alarm-clock-elapsed`. |
| X11 / XWayland | Backend explicitamente solicitado pelos aplicativos GTK lançados pela extensão. |
| GWeather **4.0**, opcional | Seletor de localização herdado nas preferências; o clima exibido é consultado no Open-Meteo. |

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
| `urllib.request`, `urllib.parse`, `urllib.error`, `http.server` | Clientes HTTP/HTTPS e servidor local do YouTube. |
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
| Bash e terminal gráfico | Execução das ações explicitamente acionadas pelo usuário. |
| `sudo` | Elevação em ações específicas, como firmware e manutenção. |
| Tilix e btop | Terminal e monitor de sistema usados pelo lançador configurado. |
| Google Chrome | Lançador do Gemini em janela de aplicativo. |
| Player compatível com MPRIS | Controles de mídia para os players reconhecidos, incluindo Spotify, Chrome/Chromium e YouTube Widget. |
| Caffeine Indicator | Indicador externo mantido na inicialização automática. |
| Speedtest CLI da Ookla, opcional | Binário incluído na extensão para o teste de velocidade. |

### Serviços externos

| Serviço / protocolo | Breve descrição |
|---|---|
| Open-Meteo | Previsão e condições meteorológicas do widget de clima. |
| Apple iCloud / CalDAV | Consulta dos calendários da conta com senha específica de aplicativo. |
| ICS / iCalendar por HTTPS | Assinaturas públicas ou privadas por link, sem modificar os eventos de origem. |
| Calendário público brasileiro do Google | Fonte separada de feriados e datas comemorativas; dispensa conta Google. |
| YouTube Data API v3 | Pesquisa, sugestões e comentários; essas consultas exigem chave configurada localmente. |
| YouTube IFrame Player API | Reprodução incorporada dos vídeos. |
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
│   ├── notes-widget/                  # Lançador e ícone dos Sticky Notes
│   ├── youtube-widget/                # Aplicativo Python, HTML e ícone
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
    ├── youtube.json                   # Chave da API do YouTube
    └── update-actions.json            # Ações adicionais, quando configuradas

~/.cache/orbitz-widgets/                # Caches dos coletores e do YouTube
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
