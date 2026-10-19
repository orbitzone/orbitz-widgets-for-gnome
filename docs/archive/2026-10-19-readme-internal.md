# README anterior — referência histórica de manutenção

Arquivado em 19/10/2026 ao separar a apresentação pública do contexto interno. O conteúdo abaixo registra estados de datas diferentes; não é guia atual de instalação nem evidência de aplicação de todas as fontes. Para manutenção atual, consulte [o índice técnico](../maintenance.md).

---

# Orbitz — Widgets for GNOME

Documentação da instalação local revisada em **17/10/2026**, a partir do código em uso e do [inventário da stack](../../stack.md).

**Orbitz Widgets for GNOME** é o projeto de **Felipe Santiago / orbitzone**, desenvolvido em [github.com/orbitzone/orbitz-widgets-for-gnome](https://github.com/orbitzone/orbitz-widgets-for-gnome). Reúne widgets de desktop, monitoramento do sistema, calendário, tarefas, timesheets e Sticky Notes. A origem do código e as atribuições dos componentes estão em [Créditos e licenças](../../docs/credits.md).

## Estado atual — 19/10/2026

CAL-01 acrescenta Google Calendar e Calendly em consulta. [Auditoria focada](../../docs/audits/2026-10-19-calendar-audit.md) concluída; plano de atualização atual:10arquivos/0comandos. Contas e GTK reais pendentes. About Orbitz fonte/instalado conferidos1.0; captura mostra conteúdo da instalação legada preservada.

As fontes incluem Orbitz Workspace (WSP-01), com cinco áreas, contexto de timesheets, faturamento e backup completo do aplicativo. Auditoria integrada: **169/169 testes Python aprovados**, cenário temporário de restauração e PDF PT/EN conferidos; veja o [parecer](../../docs/audits/2026-10-19-workspace-audit.md). Plano histórico WSP-01: 21 arquivos e zero comandos a migrar. Aplicação local e teste GTK real permanecem pendentes; registros de zero arquivos abaixo são históricos.

Refatoração modular, contratos da equipe, atualização local reversível e restauro do padrão Hardware estão implementados. A nova identidade Orbitz foi preparada, ativada e conferida; a identidade legada está desativada e preservada para retorno. A marca e a página Sobre 1.0 também foram aplicadas: o atualizador confirma zero arquivos e comandos pendentes. O usuário confirmou CPU e SSD funcionando após a correção do roteamento CLI.

A última verificação completa anterior à mudança de identidade passou: **71 testes Python, 17 arquivos de teste Node.js e o teste GJS/PangoCairo**. ID-01 recebe verificações próprias e migração separada. Resultados de 62 Python/16 JS nos relatórios anteriores pertencem ao alvo auditado naquele momento. Persistem pendências explícitas: clique da RAM não abre no teste manual reportado (ainda sem confirmação após o restauro visual), comparação visual/interativa completa e diferenças históricas de dispositivos externos/alertas (BUG-02). Este estado pode ser versionado com limitações documentadas; não representa uma versão integralmente validada do desktop.

## Identidade Orbitz e migração

A identidade própria implementada nas fontes usa UUID `orbitz-widgets@orbitzone.github.io`, URL deste GitHub e schema `org.gnome.shell.extensions.orbitz-widgets`. O UUID identifica a extensão; o campo URL aponta ao repositório. A versão apresentada é **1.0**, com revisão numérica interna 1 no manifesto, sem representar certificação de compatibilidade ou resolução das pendências conhecidas. O domínio de tradução `azclock` e o schema XML legado permanecem apenas para compatibilidade de traduções/migração.

A instalação atual usa a identidade Orbitz. Preparação reversível, configuração copiada e ativação exclusiva foram confirmadas; a instalação antiga está preservada para rollback. Implementação e auditorias dirigidas concluídas; validação gráfica/funcional abrangente permanece distinta do teste superficial relatado pelo usuário. Trocar somente o nome da pasta ou o manifesto não migra configurações. A nova instalação deve receber configuração preservada, backup/rollback e um procedimento de ativação que evite executar ambas as identidades. Nenhuma migração de dados JSON, SQLite ou credenciais é necessária por essa troca; esses dados não devem ser movidos. Guia de preparo/ativação/retorno: [migração de identidade](../../docs/operations/identity-migration.md). Estado e aceite em `docs/requirements.md` (RC-13), `docs/backlog.md` (ID-01) e `docs/decisions.md` (D-22).

## Marca e página Sobre

A marca própria fica em `extension/media/orbitz-logo.svg`: vetor original Orbitz, com anel, órbita e satélite, sem o relógio da base. Preferências carrega o arquivo pelo caminho da extensão e apresenta Orbitz Widgets for GNOME, versão 1.0, Felipe Santiago/orbitzone e GitHub do projeto. Origem e licença ficam no grupo de créditos, com os avisos preservados.

Para evitar abrir a página da instalação legada preservada para rollback, fechar janelas de preferências antigas e abrir explicitamente:

```bash
gnome-extensions prefs orbitz-widgets@orbitzone.github.io
```

Se aparecer Desktop Clock7, confira o [diagnóstico das identidades](../../docs/operations/calendar-integrations.md#about-distinguir-a-instalação-preservada): a instalação legada preservada contém essa página; a fonte e o About Orbitz instalado foram conferidos com a marca1.0.

Mudanças na página Sobre exigem atualização dos arquivos e reabertura das preferências; não exigem reinício da sessão por si só. Validação visual real continua distinta da renderização isolada da logo/testes de componentes.

## Orbitz Workspace

O aplicativo reúne cinco áreas visíveis: **Hoje**, **Agenda**, **Tarefas**, **Horas** e **Invoices**, com o subtítulo “Agenda, tarefas, horas e faturamento”. Hoje resume compromissos da fonte selecionada em cache, tarefas pendentes/atrasadas e cronômetros ativos. A área inicial pode ser escolhida nas preferências; o contexto selecionado aparece no cabeçalho. A identidade da extensão Orbitz Widgets permanece a mesma.

Na área Horas, uma timesheet possui **nome identificador** e campos opcionais de **cliente/destinatário**, **contrato/projeto** e **departamento/centro de custo**. O contexto pode ser editado sem apagar registros, IDs ou rascunhos. Timesheets existentes continuam válidas sem recadastro. Esse contexto não substitui os dados fiscais do destinatário da invoice: o cliente só é sugerido quando o perfil ainda estiver vazio. Invoices novas apresentam as referências de contrato/departamento; documentos históricos permanecem intactos.

A emissão avisa sobre possível repetição de horários já incluídos em outras invoices e permite confirmar reemissão intencional. Dados legados sem vínculo completo e registros indisponíveis têm limites explícitos de comparação; o aviso não garante ausência de duplicidade. Pagamento é informado manualmente e pode ser revertido para “Não informado”; esse estado não comprova recebimento bancário, não valida assinatura e não altera o PDF emitido.

**Backup completo do Workspace** exporta tarefas/horas/contextos, perfis, invoices e versões, pagamentos manuais, estado UI e cópias locais de tarefas. Inclui um manifesto de integridade; é um arquivo privado com dados pessoais, sem criptografia de senha. Não inclui credenciais, calendários externos, Sticky Notes ou GSettings. Pare os cronômetros antes de exportar/restaurar. A restauração tem prévia, confirmação e cópia privada do estado anterior, recusa alterações concorrentes e tenta rollback verificado em falhas controladas. Depois da operação, o Workspace fecha para evitar regravar rascunhos antigos; reabra o aplicativo. Isso não é garantia de recuperação automática após queda de energia ou edição externa não cooperante.

## Invoice de serviços em PDF

Na área **Invoices** ficam **Gerar invoice / PDF** e o histórico. O menu superior reúne timesheets arquivadas, backups e preferências. Para exportar, escolha a timesheet, preencha emitente/cliente, valor por hora e idioma Português ou English, revise a prévia e escolha onde salvar. O período oferece três opções: **Período de 1 mês** (mês civil escolhido), **Todo o histórico** (padrão) e **Período específico**. Um único calendário permite escolher as duas datas do intervalo com cliques, inclusive em meses diferentes; o resumo mostra início/fim inclusivos, sem digitação de datas. Cronômetro em andamento e lixeira não entram no cálculo. O total usa minutos inteiros e aritmética decimal, arredondado somente ao final.

Os dados do emitente e o idioma são lembrados; cliente, taxa e moeda são separados por timesheet. Eles só são persistidos após salvar um PDF com sucesso, em `~/.local/share/orbitz-widgets/invoice-profiles.json`, com permissão privada. Cancelar não grava alterações. O PDF contém dados pessoais: escolha cuidadosamente onde armazená-lo e compartilhá-lo. Esse perfil é separado dos backups de tarefas e horas; faça cópia privada dele se necessário.

O menu **Histórico de invoices** reúne as novas emissões por empresa da timesheet, cliente e ano/mês de emissão. O período dos serviços continua nos detalhes. Cada registro mantém uma cópia privada independente do PDF exportado: consultar abre essa cópia; salvar uma cópia permite escolher outro destino; excluir pede confirmação e remove somente o registro do histórico, preservando os arquivos já exportados e as horas registradas. PDFs anteriores à funcionalidade não são importados automaticamente.

O acervo fica em `~/.local/share/orbitz-widgets/invoices`, separado dos perfis e do backup de tarefas/horas. PDFs contêm dados pessoais; preserve uma cópia privada do acervo se precisar de backup. Falha ao arquivar depois de exportar gera aviso de sucesso parcial: o PDF externo permanece salvo.

A assinatura gov.br usa um fluxo assistido no histórico: **Assinar com gov.br** salva uma cópia e abre o portal oficial; o usuário faz login, envia o documento, assina e baixa o resultado no navegador. **Adicionar versão assinada** vincula uma cópia desse PDF à invoice escolhida, preservando o original e as versões anteriores. Em **Original e versões…**, cada PDF pode ser consultado ou salvo separadamente, sem alterar seus bytes.

As versões importadas ficam com **validação pendente**. O Orbitz não verifica criptograficamente a assinatura nem a correspondência do documento importado com a invoice. **Verificar no VALIDAR** abre o portal oficial para envio e conferência manuais; abrir o site não muda o estado para validado. O aplicativo não guarda senha gov.br nem envia documentos automaticamente. Login e assinatura no portal exigem conta prata ou ouro. Nenhum desses passos transforma a fatura em NFS-e.

A exportação requer os pacotes `python3-reportlab` e `fonts-dejavu-core` no Python do sistema. Sua ausência não impede abrir a agenda. A moeda inicial é BRL e pode ser alterada, independentemente do idioma. O documento é uma fatura de serviços, sem integração de emissão fiscal eletrônica ou cálculo de impostos.

Após aplicar esta atualização pelo atualizador local, feche e reabra a agenda; não é necessário reiniciar a sessão GNOME. A implementação e a instalação real são verificações separadas.

## Desenvolvimento no Codex

O [fluxo econômico dos agentes](../../docs/agents/workflow.md) agrupa auditorias por sprint e risco; a [fila de revisão](../../docs/sprint-backlog.md) concentra pendências. UX é consultoria sob demanda; testes locais continuam com o desenvolvedor. Contratos e contexto atuais são curtos, com histórico arquivado para consulta dirigida.

As instruções do projeto ficam em [AGENTS.md](../../AGENTS.md). O papel do agente responsável por documentação, requisitos e coordenação está em [docs/agents/project-owner.md](../../docs/agents/project-owner.md). O cadastro da pasta como projeto é feito na interface do Codex; esses arquivos preservam as responsabilidades entre conversas.

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
| Orbitz Workspace | Hoje, Agenda, Tarefas, Horas e Invoices; fontes externas e gestão local do trabalho. |
| Timesheets | Contextos de cliente/contrato/departamento, registro manual ou cronômetro, histórico, totais e exportação. |
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

O Workspace organiza a navegação em Hoje, Agenda, Tarefas, Horas e Invoices; a área inicial é configurável. As timesheets ficam em Horas. O tamanho da janela está sujeito aos limites do ambiente gráfico.

Acima do calendário, o seletor escolhe uma fonte conectada. O menu de integração permite conectar Apple/iCloud, Google Calendar, Calendly ou uma assinatura ICS. O seletor abre abaixo do campo; a rolagem é usada quando o espaço disponível não comporta todas as opções.

### Fontes suportadas

- **Apple/iCloud:** leitura via CalDAV com senha específica de aplicativo, guardada no Secret Service/libsecret.
- **Google Calendar:** leitura com OAuth desktop no navegador, cliente JSON fornecido localmente e grant no Secret Service.
- **Calendly:** consulta dos agendamentos do próprio usuário com PAT pessoal no Secret Service; `users:read` e `scheduled_events:read`.
- **Assinaturas ICS:** endereços HTTPS ou webcal, incluindo fontes públicas sem autenticação de conta.
- **Brasil · Datas comemorativas (Google):** assinatura pública separada, sem login Google, incluindo feriados e datas comemorativas como Dia do Professor.

A fonte pública brasileira utilizada é:

```text
https://calendar.google.com/calendar/ical/pt.brazilian%23holiday%40group.v.calendar.google.com/public/basic.ics
```

Google Calendar e Calendly foram implementados nas fontes no lote CAL-01: consulta com OAuth desktop no Google e PAT pessoal no Calendly. Pré-requisitos e limites estão no [guia das integrações](../../docs/operations/calendar-integrations.md); auditoria focada concluída com35 testes aprovados e2skips ambientais de socket. Instalação, configuração e teste real permanecem pendentes neste marco. Zoho e outros provedores ainda podem usar uma assinatura ICS compatível. Calendários de feriados exibidos pelo iPhone nem sempre pertencem aos calendários pessoais retornados pelo iCloud.

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

## Timesheets por contexto de trabalho

Na área **Horas**, **+ Nova timesheet** cria um registro com nome e contexto opcional de cliente, contrato/projeto e departamento/centro de custo. É possível editar o contexto e reordenar as abas, preservando o histórico.

Cada registro possui três campos editáveis: **Descrição**, **Início** e **Fim**. A data vem do dia selecionado. A interface calcula duração e totais por dia, semana e mês. Oferece:

- Edição direta, Enter para salvar, Esc para cancelar e navegação com Tab.
- Sugestão do último horário de término e autocompletar descrições por timesheet.
- Cronômetro, com divisão dos registros ao atravessar a meia-noite.
- Aviso de sobreposição e revisão dos horários antes de registrar uma tarefa concluída.
- Rascunhos persistentes, inclusive após fechar e reabrir a agenda.
- Exportação CSV por período, com UTF-8 BOM, separador ponto e vírgula e proteção contra fórmulas em campos de texto.
- Arquivamento, consulta e exportação de arquivadas, restauração e exclusão definitiva somente após arquivar e confirmar.

Não é possível arquivar uma timesheet com cronômetro ativo. Timesheets arquivadas são consultadas sem edição até serem restauradas. O acesso às arquivadas e aos backups fica no menu de ações do Workspace. O backup legado de tarefas/horas permanece distinto do backup completo.

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

A lista detalhada, incluindo versões das bibliotecas Python, está em [stack.md](../../stack.md). Os coletores de sistema usam principalmente a biblioteca padrão; o projeto completo também precisa de bibliotecas nativas e das dependências de calendário.

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

## Organização das fontes após a refatoração RF-01

No checkout de desenvolvimento, a agenda separa normalização iCalendar em `extension/planner/calendar_events.py`, acesso ao cofre em `credential_vault.py` e substituição JSON durável em `atomic_json.py`. `apple_client.py` mantém os helpers públicos anteriores por reexportação; `external_store.py` mantém `Vault`. Locks, backups e retenção continuam nos respectivos chamadores. A análise pura UFW fica em `widgets/firewall_patterns.py`; journal, cache e CLI continuam em `firewall-widget.py`.

CPU/RAM, processos, rede, conexões e temperaturas têm entradas `main()` protegidas, preservando execução direta e pelo worker. Os módulos novos devem acompanhar seus chamadores em qualquer instalação futura. Este mapa descreve as fontes; o mapa da instalação histórica acima não é atualizado automaticamente.

O frontend compõe os painéis a partir de `extension/commandPanels.js` e dos oito módulos em `extension/panels/`, antes do registro GObject. O diálogo de fuso está em `extension/settings/TimeZoneDialog.js`; o fluxo tarefa→timesheet em `extension/planner/task_timesheet_ui.py`; o cartão das notas em `sticky-notes/card.py`. YouTube separa API/cache em `youtube_api.py` e HTTP em `youtube_server.py`, mantendo `youtube-widget.py` como ponto de entrada GTK/WebKit. Esses módulos também devem acompanhar os chamadores em distribuição futura.

Inventários e testes específicos: [backend](../../docs/audits/2026-10-18-backend-refactor.md) e [frontend](../../docs/audits/2026-10-18-frontend-refactor.md). Ambos declararam suas áreas estáveis; a [auditoria integrada](../../docs/audits/2026-10-18-integrated-audit.md) concluiu as verificações locais sem regressão impeditiva reproduzida no escopo revisado. Validação gráfica permanece pendente por bloqueio dos sockets Broadway no ambiente isolado; não há alegação de ganho de desempenho. Errata de 18/10/2026: o auditor reconciliou a baseline local — eram **11 de 14 arquivos JS aprovados**, com três falhas, e não 12/15. O número 12/15 abaixo preserva o relato recebido na publicação e está corrigido por esta errata; não é evidência de uma execução separada com 15 arquivos. Na suíte integrada RF-01, o auditor informou **62 testes Python e 16 arquivos de teste JS aprovados**; o relatório integrado confirma 102 verificações de sintaxe e mantém a validação visual/interativa pendente.

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

Projeto Orbitz: **Felipe Santiago / orbitzone**. Origem, contribuições anteriores, recursos e licenças estão em [docs/credits.md](../../docs/credits.md). Os arquivos `LICENSE` e `extension/LICENSE` e os avisos das dependências/recursos foram preservados.

-----

### Correção de roteamento após teste manual — hardware

Em 18/10/2026 o teste do usuário encontrou falhas CPU/SSD e abertura RAM. A migração para coletores do repositório expôs ausência preexistente dos desvios CLI `--hardware`, `--details` e `--eject` no snapshot, presentes no coletor histórico. O repositório corrigido restaura os protocolos esperados pelos painéis; a aplicação local dessa correção foi conferida e o usuário confirmou CPU e SSD funcionando. O sintoma específico de clique RAM ainda não foi reproduzido em ambiente gráfico. Registros e pendências: `docs/backlog.md`, BUG-01/BUG-02.

### Padrão mantido do resumo Hardware

Conforme confirmação do usuário e coletor histórico, o resumo CPU/RAM/SSD usa fonte monospace com `size="7680"` (7,5 pt em unidades Pango), `line_height="1.5"`, barras de oito células e linhas sem vazios intercalados. Padding/margens da configuração existente são preservados; não ajustar escala global nem outros widgets para compensar. Requisito RC-12 e parecer UX em `docs/design/2026-10-18-hardware-restoration.md`. O markup restaurado coincide com a instalação no último plano conferido; é necessário reiniciar os widgets pelo controlador para recriar o worker após uma atualização, sem necessidade de logout quando apenas o coletor mudou. O clique RAM continua pendente de validação na sessão real.
