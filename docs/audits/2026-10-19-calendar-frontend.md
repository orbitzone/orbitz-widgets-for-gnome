# CAL-01 — frontend — 19/10/2026

**Frontend estável com testes específicos; autenticação real/GTK e integração final pendentes.** Sem instalação, migração, publicação, sobreposição do legado, segredo real, navegador ou cofre acessado pelo frontend.

## Google Calendar e Calendly

Novo `provider_connection_ui.py` e integração em `external_ui.py`:

- Menu adiciona Google Calendar e Calendly; iCloud/ICS preservados. Google exige arquivo OAuth **desktop fornecido pelo usuário**, escolhido localmente; autorização no navegador com retorno local controlado pelo backend. Sem client ID inventado, senha no formulário ou segredo solicitado no chat.
- Calendly usa Entry mascarada para PAT, limpa ao iniciar/fechar; instrução mostra users:read e scheduled_events:read, conforme contrato/pesquisa atual do backend. Credenciais/configuração ficam sob responsabilidade do cofre do backend, nunca JSON de calendários, logs ou repositório.
- Trabalho em executor mantém diálogo responsivo; cancelar/fechar sinaliza cancel_event. Um handshake de aceite da UI após retorno do backend evita deixar conta recém-conectada se a janela fecha antes do callback. Worker aguarda aceite limitado; cancel/timeout solicita disconnect/limpeza. Aceite tardio depois do rollback é recusado. Não se declara garantia contra encerramento abrupto do processo ou falhas do storage/cofre; atomicidade/erros pertencem ao backend.
- Google launch callback aceita somente HTTPS em accounts.google.com, sem userinfo/porta arbitrária, via Gio. Nenhuma automação de login ou upload.
- Sync usa calendar_accounts.events para novos provedores, com cancelamento e cache escrito somente após resposta completa e não cancelada. Botão Cancelar sincronização, status de interrupção/sem operação e erro com último cache disponível. API de cache revalida conta existente. Desconectar cancela trabalhos da conta e usa wrapper cofre-aware apenas para novos providers; callbacks iCloud/ICS mantidos. Tarefas/horas locais não são removidas.

APIs alinhadas diretamente: connect_google(config_path,label,cancel_event,open_browser), connect_calendly(token,label,cancel_event), events(account,calendar,month,cancel_event), disconnect(account). Campos/events mantêm contrato Apple normalizado. Novo módulo é obrigatório no pacote de fontes. Sem UX extra automático ou alteração do renderer/PDF.

## About — leitura instalada e diagnóstico

UUID novo instalado `orbitz-widgets@orbitzone.github.io`: metadata Orbitz Widgets for GNOME, version1/version-name1.0/schema próprio. About SHA256 **99c2d42af230ad64400fd2cd7cdf4ad7dbce3a48371575f9c96b0c3284b6bc53**, idêntico ao repositório; contém SVG própria, sem título Desktop Clock ou PayPal.

UUID legado instalado `azclock@azclock.gitlab.com`: metadata Desktop Clock7/schema antigo. About SHA256 **de5c009b532d59dc335becd8a1a780c13f70089fa3f802f5f00ed3abf1d8f360**, com conteúdo da captura (logo/título antigo, GitLab/PayPal). Isso identifica o **conteúdo legado**, não comprova qual acionamento/cache/janela aberta o produziu.

GSettings enabled-extensions lista somente o UUID novo entre os dois IDs relevantes; isso é configuração lida, não prova de estado runtime de janelas. No namespace /proc disponível não foi identificado processo prefs por argumentos exatos conhecidos; não se conclui que todas as janelas estejam fechadas. Uma primeira busca ampla por substring encontrou a própria execução de diagnóstico e foi descartada, sem atribuir identidade a processo de prefs.

Lançador oculto local orbitz-notes.desktop aponta notes-widget legado, **não abre preferências**, portanto não explica o About e não foi alterado. Fonte da ação de preferências usa ExtensionUtils.openPrefs contextual da extensão corrente. Por orientação do supervisor, preservada a API correta; nenhum hardcode/correção especulativa aplicado a fontes/instalação. Marca SVG, créditos e licenças intactos.

Orientação operacional sob coordenação do supervisor: fechar preferências antigas e abrir explicitamente `gnome-extensions prefs orbitz-widgets@orbitzone.github.io`. Esse comando **não foi executado** pelo frontend; não exige sobrescrever a pasta legada. Se persistir, é necessária evidência da janela/processo que efetivamente abriu; causa exata de launcher/cache continua não comprovada.

## Evidências e limites

- `python3 -m unittest discover -s tests -p test_calendar_frontend.py -v`: **8/8**. Contratos Google/Calendly, cancel antes/depois do commit/ACK descartado, worker real aguardando aceite com cancelamento, destino de browser restrito, rotas Google/Calendly/iCloud/ICS, cache preservado em falha/cancel e disconnect correto. Serviços HTTP/cofre/browser são mocks, dados sintéticos.
- `node tests/test_identity.js`: aprovado; About/metadata/logo/GioFileIcon/versão/licença corretos na fonte.
- AST/whitespace dos três arquivos frontend/teste e diff-check de external_ui aprovados. Alterações finais no texto de cancelamento não exigiram repetir suíte global.
- Leitura de metadata/About instalados, hashes e configuração de IDs realizada somente para diagnóstico. Nenhum dump de preferências pessoais, tokens/config cliente ou credenciais foi registrado.

Sem autenticação externa real, callback OAuth real, PAT válido, API externa, Secret Service, GTK/foco/AT ou nova tentativa gráfica bloqueada. Backend mantém pesquisa oficial/scopes e testes de protocolo. Supervisor centraliza guia `docs/operations/calendar-integrations.md`, documentação, integração/auditoria e RC-17/comando de atualização quando autorizado. Frontend não declara aplicação instalada ou conexão efetiva de contas.
