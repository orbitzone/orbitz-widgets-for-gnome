# Orbitz — Widgets for GNOME

Documentação da instalação local revisada em **17/10/2026**, a partir do código em uso e do [inventário da stack](stack.md).

Orbitz reúne widgets de desktop, monitoramento do sistema, calendário, tarefas, timesheets e Sticky Notes. A base é uma personalização do **Desktop Clock / azclock v7**, de Andrew Zaech, mantendo o identificador `azclock@azclock.gitlab.com`. Não é uma versão oficial do upstream.

## Estado do projeto e compatibilidade

- Ambiente local: Ubuntu 22.04, GNOME Shell **42.9**, GJS **1.72.4** e Python **3.10.12**.
- O manifesto declara GNOME 42, 43 e 44; isso não equivale a validação completa dessas versões. A implementação usa APIs legadas e não declara suporte a GNOME 45 ou posterior.
- A extensão está instalada em `~/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/`.
- O repositório reúne o código em `extension/`, `widgets/` e `sticky-notes/`. A instalação local ainda está distribuída entre a extensão, o aplicativo Sticky Notes e coletores em pastas anteriores do Codex. O mapa abaixo mostra os caminhos usados. Não existe, neste inventário, um pacote único atualizado e validado para reinstalar todos esses componentes.
- Pacotes e instaladores históricos não devem ser tratados como uma distribuição completa do estado descrito aqui. Instalar o azclock original também não instala estas personalizações.

## Widgets e aplicativos

| Componente | Recursos atuais |
|---|---|
| Relógio | Hora, data, aparência configurável e ponto de referência dos alertas da agenda. |
| Clima | Condições e previsão via Open-Meteo; preserva o último resultado válido em falhas. Localização configurada no script. |
| CPU, RAM e armazenamento | Uso de recursos, detalhes de CPU/RAM, informações de armazenamento e dispositivos externos com ação de ejeção. |
| Processos | Consumo de CPU e memória, pressão de recursos e atalhos disponíveis para processos, inicialização e perfis de energia. |
| Rede | Tráfego, interface ativa e qualidade da conexão; usa rota IPv6 como alternativa quando necessário. |
| Segurança/conexões | Conexões TCP estabelecidas fora de loopback e portas locais em escuta; detalhes, consultas manuais de DNS/RDAP e teste de velocidade opcional. “Externa” aqui não significa necessariamente internet: pode incluir a rede local. |
| Firewall | Análise de registros UFW, agrupamento de padrões, evidências e inspeção de endereços/portas. Depende de logs e permissão de leitura. |
| Serviços | Estado e informações dos serviços do sistema. |
| Temperaturas | Sensores agrupados em quatro colunas, ajuda por sensor e destaque vermelho acima de 80 °C; leituras indisponíveis são omitidas. |
| Atualizações | Consulta APT, Snap e Flatpak, indicação de resultados parciais e ações manuais em terminal. |
| Docker | Contêineres em execução e portas publicadas; links para interfaces web quando reconhecidas. Não inicia ou encerra contêineres. |
| Mídia | Integração MPRIS com players reconhecidos, incluindo Spotify, Chrome/Chromium e YouTube Widget; sem dependência de `playerctl`. |
| Calendário e tarefas | Agenda local, fontes externas e conversão de evento em tarefa. |
| Timesheets | Múltiplas empresas, registro manual ou por cronômetro, histórico, totais e exportação. |
| Sticky Notes | Notas independentes em GTK, com persistência SQLite e backups. |
| YouTube | Janela GTK/WebKit com player incorporado; pesquisa, sugestões e comentários usam chave da YouTube Data API. |
| Lançadores | Abertura dos Sticky Notes, YouTube, Gemini no Chrome e btop no Tilix. |
| Caffeine Indicator | Aplicativo externo com inicialização automática própria. |

## Controlador e interação

O controlador permanece **branco** tanto com os widgets abertos quanto fechados. A cada login ou ativação da extensão, os widgets começam pausados: clique no controle para abrir o conjunto, incluindo Sticky Notes; clique novamente para fechar os widgets e as notas. O controle fica indisponível enquanto o encerramento termina.

O encerramento remove atores, diálogos, temporizadores e assinaturas dos widgets e cancela seus coletores. Os dados salvos permanecem. Ações já iniciadas em terminais e serviços do sistema têm ciclo de vida próprio. O **Caffeine Indicator continua independente**, iniciando com a sessão; os Sticky Notes não possuem inicialização automática ativa.

A posição do controlador considera o monitor com mais posições salvas, com alternativa no monitor principal. A detecção de interação considera janelas à frente para evitar acionar widgets encobertos. Aparência, posição, dimensões, comandos e agrupamentos ficam nas preferências da extensão. Relógio e clima têm largura padrão de 440 px; os demais usam largura natural, com opção de largura individual.

O controle manual reduz a exposição a problemas ao iniciar os coletores, mas não isola falhas no próprio GNOME Shell. Os comandos personalizados executam com as permissões da conta do usuário.

## Calendário, tarefas e fontes externas

A janela abre por padrão na aba **Tarefas**, inclusive ao reativar a aplicação. O tamanho inicial é 1040 × 1300 px, sujeito aos limites do ambiente gráfico. As abas seguintes incluem **Eventos** e as timesheets.

Acima do calendário, o seletor escolhe uma fonte conectada. O menu de integração permite conectar Apple/iCloud ou uma assinatura ICS. O seletor abre abaixo do campo; a rolagem é usada quando o espaço disponível não comporta todas as opções.

### Fontes suportadas

- **Apple/iCloud:** leitura via CalDAV com senha específica de aplicativo, guardada no Secret Service/libsecret.
- **Assinaturas ICS:** endereços HTTPS ou webcal, incluindo fontes públicas sem autenticação de conta.
- **Brasil · Datas comemorativas (Google):** assinatura pública separada, sem login Google, incluindo feriados e datas comemorativas como Dia do Professor.

A fonte pública brasileira utilizada é:

```text
https://calendar.google.com/calendar/ical/pt.brazilian%23holiday%40group.v.calendar.google.com/public/basic.ics
```

Google com autenticação de conta, Zoho e outros provedores não possuem conectores próprios implementados nesta versão. Um link ICS compatível pode ser usado como assinatura. Calendários de feriados exibidos pelo iPhone nem sempre pertencem aos calendários pessoais retornados pelo iCloud.

A agenda sincroniza as fontes conectadas enquanto está aberta, com atualização periódica de cinco minutos e botão manual. Consultas rodam em segundo plano e preservam o cache anterior quando falham. Selecionar ou desconectar uma fonte não altera as tarefas e timesheets locais.

### Marcação dos dias

Dias com conteúdo recebem números brancos em negrito; os demais ficam cinza. A marcação considera tarefas locais pendentes, registros de timesheets não arquivadas e eventos da fonte selecionada. Feriados identificados em qualquer calendário conectado recebem sublinhado dourado e informação ao passar o ponteiro. Datas comemorativas e eventos de dia inteiro não são automaticamente classificados como feriados.

### Tarefas e eventos

Tarefas possuem descrição, data, horário opcional e antecedência do lembrete. Eventos externos só viram tarefas por uma ação explícita, com revisão antes de salvar e proteção contra importação duplicada. Não há sincronização de escrita com o calendário externo.

Ao concluir uma tarefa, **Registrar horas** permite escolher uma timesheet ativa. A descrição e a data são preenchidas, com sugestão de horários para revisão. O vínculo permite consultar o registro e evita registrar a mesma tarefa duas vezes na mesma timesheet; outra timesheet pode receber seu próprio registro.

### Alertas

No período de notificação, o GNOME Shell mostra um cartão próximo ao relógio com título, origem e tempo restante, além de ações para abrir a agenda ou dispensar. Também emite uma notificação do sistema e tenta reproduzir `alarm-clock-elapsed` pelo `canberra-gtk-play`, conforme as condições de áudio da sessão.

Tarefas usam a antecedência configurada. Eventos usam seus alarmes VALARM ou dez minutos quando não há alarme compatível. Eventos de dia inteiro não disparam esse alerta. O histórico persistente evita repetir o anúncio a cada atualização; a contagem regressiva continua no cartão. Há proteção contra duplicidade entre evento e tarefa importada e contra anúncios durante o bloqueio da tela.

Os alertas funcionam com a janela da agenda fechada, desde que a extensão esteja ativa, mas usam **eventos já sincronizados em cache**. Não existe sincronização externa independente com a agenda fechada. Sem relógio visível, o cartão usa uma posição alternativa no monitor. Parar os widgets pelo controlador não desativa o serviço de lembretes da extensão; desativar a extensão o encerra.

## Timesheets por empresa

O botão **+** à direita das abas cria quantas timesheets forem necessárias. O nome informado aparece como `TS - Nome`, por exemplo `TS - Viewdeck`. É possível renomear e reordenar as abas.

Cada registro possui três campos editáveis: **Descrição**, **Início** e **Fim**. A data vem do dia selecionado. A interface calcula duração e totais por dia, semana e mês. Oferece:

- Edição direta, Enter para salvar, Esc para cancelar e navegação com Tab.
- Sugestão do último horário de término e autocompletar descrições por empresa.
- Cronômetro, com divisão dos registros ao atravessar a meia-noite.
- Aviso de sobreposição e revisão dos horários antes de registrar uma tarefa concluída.
- Rascunhos persistentes, inclusive após fechar e reabrir a agenda.
- Exportação CSV por período, com UTF-8 BOM, separador ponto e vírgula e proteção contra fórmulas em campos de texto.
- Arquivamento, consulta e exportação de arquivadas, restauração e exclusão definitiva somente após arquivar e confirmar.

Não é possível arquivar uma timesheet com cronômetro ativo. Timesheets arquivadas são consultadas sem edição até serem restauradas. O acesso às arquivadas e à restauração de backup fica em ícones próximos de “Tarefas e horas salvas neste computador”.

## Persistência e recuperação

| Local | Conteúdo |
|---|---|
| GSettings/dconf da extensão | Elementos, comandos, posições, aparência e grupos. |
| `~/.local/share/orbitz-widgets/notes.json` | Tarefas, timesheets, vínculos e dados legados. |
| `~/.local/share/orbitz-widgets/planner-ui.json` | Preferências e rascunhos da agenda. |
| `~/.local/share/orbitz-widgets/external-calendars.json` | Metadados das conexões e eventos em cache; não contém a senha iCloud. |
| `~/.local/share/orbitz-widgets/reminder-state.json` | Alertas anunciados e dispensados. |
| `~/.local/share/orbitz-widgets/planner-backups/` | Até 60 cópias do histórico da agenda. |
| `~/.local/share/orbitz-postits/notes.sqlite3` | Banco dos Sticky Notes, em modo WAL. |
| `~/.local/share/orbitz-postits/backups/` | Backups próprios das notas. |
| Secret Service da sessão | Credencial específica de aplicativo do iCloud. |
| `~/.cache/orbitz-widgets/` | Caches de execução; alguns coletores também mantêm caminhos de cache legados. |

A agenda usa bloqueio de arquivo, gravação atômica e sincronização em disco. A restauração mostra uma prévia, exige confirmação e preserva uma cópia do estado anterior. As credenciais no cofre e o banco dos Sticky Notes **não fazem parte do backup JSON da agenda**. Para migrar a instalação completa, preserve esses componentes separadamente e reconecte as contas quando necessário.

## Stack e dependências

A lista detalhada, incluindo versões das bibliotecas Python, está em [stack.md](stack.md). Os coletores de sistema usam principalmente a biblioteca padrão; o projeto completo também precisa de bibliotecas nativas e das dependências de calendário.

| Dependência | Finalidade |
|---|---|
| GNOME Shell, GJS, St, Clutter, Meta e Graphene | Extensão, widgets, janelas, monitores e entrada. |
| GLib, Gio, GObject e Pango | Eventos, processos, arquivos, D-Bus e texto. |
| GSettings/dconf | Configuração persistente da extensão. |
| Python 3 e PyGObject (`python3-gi`) | Aplicativos GTK e coletores. |
| GTK 3/GDK | Agenda, Sticky Notes e YouTube. |
| GTK 4/libadwaita | Preferências da extensão. |
| WebKit2 4.0 | Player incorporado do YouTube. |
| libsecret/Secret Service e cofre compatível | Credenciais do iCloud. |
| `icalendar`, `recurring-ical-events`, `python-dateutil`, `tzdata`, `x-wr-timezone` | Leitura, recorrência e fusos de calendários; incluídos em `planner/vendor/`. |
| `click`, `six`, `typing_extensions` | Dependências transitivas empacotadas. |
| `defusedxml` | Leitura protegida de XML do CalDAV, fornecida pelo sistema. |
| SQLite, JSON e CSV do Python | Notas, histórico e exportação. |
| X11/XWayland | Backend solicitado pelos aplicativos GTK lançados pela extensão. |
| `canberra-gtk-play` e tema de sons | Alarme dos lembretes. |
| `/proc`, `/sys`, `setsid`, `timeout` e utilitários Linux | Métricas e execução limitada dos coletores. |
| `ip`, `ss`, `ping`, `getent` | Rede e resolução de nomes. |
| `lsblk`, `lscpu`, UDisks/`udisksctl` | Hardware, volumes e ejeção. |
| `sensors`, `nvidia-smi`, `dmidecode` | Informações adicionais de sensores e firmware, conforme disponibilidade. |
| `systemctl`, `journalctl`, UFW | Serviços e evidências do firewall. |
| APT, Snap, Flatpak e Docker | Respectivos widgets; opcionais conforme o recurso. |
| Terminal gráfico, Bash e `sudo` | Ações manuais e operações que exigem elevação. |
| GNOME System Monitor, Startup Applications e `powerprofilesctl` | Atalhos opcionais do painel de processos. |
| `libpsl.so.5` | Simplificação de domínios quando disponível. |
| Tilix/btop, Chrome e Caffeine Indicator | Aplicativos dos lançadores e indicador independente. |
| Ookla Speedtest CLI | Teste de velocidade opcional; há um executável na instalação local, com licença própria. |
| GWeather 4 | Auxiliar opcional de localização das preferências herdadas. |

A integração iCloud usa cliente HTTP/XML próprio e libsecret; os pacotes Python `caldav` e `keyring` não são requisitos dessa implementação. MPRIS dispensa `playerctl`. Não é necessário instalar Node.js para usar os widgets; ele é uma ferramenta de verificação de desenvolvimento.

## Mapa de arquivos

```text
~/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/
├── extension.js                 # Widgets, controlador, painéis e mídia
├── metadata.json / schemas/     # Compatibilidade e configuração
├── prefs.js / settings/         # Preferências GTK 4
├── dragging.js / grouping.js    # Posição e grupos
├── utils.js / stop-collectors.py # Utilitários e encerramento dos coletores
├── media/                      # Ícones e peças dos relógios
├── planner/
│   ├── calendar-app.py          # Agenda GTK 3
│   ├── month_calendar.py / calendar_selector.py
│   ├── store.py / ui_state.py / planner_tools.py
│   ├── timesheet.py / timesheet_ui.py
│   ├── external_ui.py / external_store.py
│   ├── apple_client.py / ics_client.py
│   ├── calendar.js / reminders.js
│   ├── planner.js / editor.py   # Componentes legados preservados
│   └── vendor/ / apple-calendar-requirements.txt
├── notes-widget/               # Lançador dos Sticky Notes
├── youtube-widget/             # Python, HTML e ícone
├── gemini-widget/               # Ícone do lançador
└── speedtest                   # CLI local da Ookla

~/.local/share/orbitz-postits/app/
├── postits.py
├── storage.py
└── postits.svg

~/Documents/Codex/
├── 2026-10-08/quan/outputs/
│   ├── clima-widget.py / cpu-ram-widget.py / processos-widget.py
│   ├── rede-widget.py / seguranca-widget.py / servicos-widget.py
│   ├── temperaturas-widget.py
│   └── metrics-worker.py / widget_runtime.py / auxiliares de métricas e detalhes
├── 2026-10-09/pngrub-ae-in-f14-1e100-net/outputs/
│   └── firewall-widget.py / auxiliares
└── 2026-10-11/https-rdap-org-ip-2a06-3a98c1/outputs/
    └── atualizacoes-widget.py / docker-widget.py / auxiliares
```

Os caminhos acima fazem parte da configuração atual. **Mover ou apagar essas pastas exige atualizar os comandos no GSettings e preservar os módulos auxiliares.** Cópias em outras pastas não são necessariamente as executadas pela extensão.

## Configuração e operação

Abra as preferências pelo aplicativo Extensões do GNOME ou execute:

```bash
gnome-extensions prefs azclock@azclock.gitlab.com
```

Os intervalos dos comandos são expressos em milissegundos. CPU, processos e tráfego compartilham um coletor persistente, com amostragem própria; o intervalo visual não equivale à janela de amostragem. O clima é limitado a consultas a cada cinco minutos. Painéis de detalhes possuem atualização manual, conforme o componente.

- **Clima:** edite os parâmetros de latitude, longitude e fuso no `clima-widget.py` efetivamente configurado, incluindo o texto da localização e o cache quando necessário.
- **YouTube:** configuração da chave em `~/.config/orbitz-widgets/youtube.json`; não publique esse arquivo. O player usa um servidor HTTP local restrito a loopback com token.
- **Atualizações:** `~/.config/orbitz-widgets/update-actions.json` aceita ações adicionais com nome e comando. O usuário aciona os botões e confirma no terminal; nenhuma atualização é executada automaticamente pelo widget.
- **Docker:** `~/.config/orbitz-widgets/docker-urls.json` permite substituir links por contêiner ou contêiner/porta. URLs precisam ser HTTP/HTTPS com porta explícita; contextos remotos não recebem links automáticos para localhost.
- **Firewall:** exige registros UFW existentes e acesso ao journal. Registros podem ser limitados ou ausentes; os padrões apresentados são heurísticas de revisão, não prova de ataque.
- **Speedtest:** requer o executável compatível chamado `speedtest` na raiz da extensão. Só executa sob solicitação e usa as condições próprias da Ookla; não é o pacote Python `speedtest-cli`.

Os coletores usam limites de tempo e saída, cancelamento e proteção contra respostas antigas. Operações privilegiadas não alteram permissões automaticamente. Ações de manutenção e atualização mostram o comando em terminal antes de executar. Importação de configurações valida o conteúdo e apresenta comandos para revisão.

## Solução de problemas

| Sintoma | Verificação |
|---|---|
| Widgets não aparecem ao entrar na sessão | O início pausado é intencional: clique no controlador branco. Confira também se a extensão está ativa. |
| Widget apresenta erro | Execute o comando configurado em terminal e confira caminho, módulos auxiliares e ferramentas disponíveis. |
| Calendário iCloud parece ausente | Confira o seletor e a lista de conexões; uma falha de interface não significa perda dos dados. Verifique o cofre de senhas e use a atualização manual. |
| Evento externo não aparece | Confira fonte e dia selecionados, conexão e cache; datas comemorativas do iPhone podem vir de uma assinatura separada. |
| Lembrete externo não dispara | Abra a agenda para sincronizar, confira horário, antecedência e extensão ativa; eventos de dia inteiro não geram esse alarme. |
| Cartão aparece sem som | Confira volume, silenciamento, `canberra-gtk-play` e disponibilidade do som `alarm-clock-elapsed`. |
| Sensores ou firmware indisponíveis | Confira suporte do hardware e ferramentas opcionais; algumas consultas de firmware exigem autorização em terminal. |
| Docker ou firewall sem dados | Confira daemon, contexto, permissões e disponibilidade dos logs; não altere permissões apenas para ocultar o erro. |

## Desenvolvimento e validação

Alterações devem preservar as unidades das métricas, a persistência, os vínculos entre tarefas e horas e o encerramento dos coletores. O projeto possui verificações locais de sintaxe e lógica Python/JavaScript e testes de interface GTK em sessões isoladas. Ferramentas usadas incluem `unittest`, Node.js, Broadway, Pycairo, D-Bus isolado e Xephyr.

O repositório inclui testes em `tests/`; verificações mais recentes da agenda e relatórios também estão distribuídos entre diretórios de desenvolvimento. Execute `python3 -m unittest discover -s tests -v` e os testes JavaScript com Node.js ao alterar os componentes correspondentes. Não há validação integral de reinstalação em máquina limpa, de todas as versões GNOME declaradas ou de todas as combinações de hardware. A revisão deste README verifica documentação e caminhos, sem substituir os testes funcionais do desktop.

### Resultado da preparação para publicação (17/10/2026)

Foram aprovados 44 testes Python e 12 dos 15 testes JavaScript. Permanecem falhas em `test_storage_ui.js` (mock sem `_updatesNote`), `test_stats_storage_click.js` (expectativa de região de clique divergente) e `test_widget_controller.js` (mock sem `Calendar`). Essas falhas precisam ser investigadas antes de considerar a suíte integralmente aprovada. A sintaxe dos módulos Python próprios foi conferida. Não foi executado teste funcional completo da sessão gráfica nesta publicação.

## Créditos e licenças

Desktop Clock / azclock: **Andrew Zaech**. Personalizações e widgets Orbitz: **orbitzone / Orbitz**. A extensão inclui o texto da licença GNU GPL v3 em seu arquivo `LICENSE`; bibliotecas, ferramentas e recursos visuais mantêm suas próprias licenças. A CLI da Ookla possui termos separados.

Os créditos originais dos recursos do Desktop Clock são preservados abaixo.

**@[AndrewZaech](https://gitlab.com/AndrewZaech) - Project Maintainer and Developer**

#### Desktop Clock Logo

**@[AndyC](https://gitlab.com/LinxGem33)** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

#### Clock Faces and Hands

**@[stefan-oskamp](https://gitlab.com/stefan-oskamp) #34 - Style 9**

*Modifications were made to the following files to better suit this extensions needs*

**@[macrovector on Freepik](https://www.freepik.com/free-vector/clock-watch-collection-set-dial-with-seconds-arrow_13031502.htm) - Styles 1, 2, 5, 7, 8**

**@[Jahoe](https://commons.wikimedia.org/wiki/User:Jahoe) - Style 4** [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

**@[wikipedia](https://commons.wikimedia.org/wiki/File:Swiss_railway_clock_1.svg) - Style 3** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

#### Other contributions via MR:

**@[Sergey Korablin](https://gitlab.com/skorablin) - !7**

#### Translators:
**@[Etamuk](https://gitlab.com/Etamuk) - German** | **@[Ser82-png](https://gitlab.com/Ser82-png) - Russian** | **@[Vistaus](https://gitlab.com/Vistaus) - Dutch**

-----
