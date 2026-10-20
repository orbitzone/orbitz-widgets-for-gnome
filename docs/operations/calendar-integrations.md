# Google Calendar e Calendly — configuração local

Escopo CAL-01/RC-22, 19/10/2026. Implementação e auditoria focada concluídas nas fontes; autorização real e interação GTK precisam de teste separado. [Parecer CAL-01](../audits/2026-10-19-calendar-audit.md):35 testes aprovados,2skips ambientais de sockets e teste Node de identidade aprovado. A integração consulta eventos e permite criar uma tarefa local por ação explícita. Não cria, altera, cancela ou exclui eventos remotos. Tarefas e horas não dependem da continuidade da conexão.

## Google Calendar — usuário

No Workspace, abra **Integrar calendário → Google Calendar**, ajuste o nome da conexão se desejar e clique em **Entrar com Google**. O navegador abre a escolha de conta e o consentimento de leitura. Depois, retorne ao Workspace e escolha o calendário no seletor. Não é necessário criar projeto no Google Cloud, importar JSON ou informar senha no aplicativo.

Se o Google informar que sua conta não está autorizada, o mantenedor precisa conferir público/usuários de teste, API habilitada e estado de verificação do projeto. Cancelar interrompe a tentativa; conexões e dados locais anteriores são preservados.

Se a consulta da lista retornar HTTP403, confira a ativação da [Google Calendar API no projeto Orbitz](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project=227612761270). **Ativar** indica que ainda falta habilitar; **Gerenciar** indica que já está habilitada. Essa configuração cabe ao responsável pelo projeto, não aos usuários comuns. A ajuda opcional do diálogo oferece esse mesmo link. Outros motivos403 exigem diagnóstico próprio; não concluir falta de escopo somente pelo status. O mantenedor confirmou login/sincronização inicial após ativar a API, sem certificar todos os casos ou contas.

## Google Calendar — mantenedor

O cliente público do Orbitz foi fornecido pelo responsável em19/10/2026 e será incluído no aplicativo. O Client ID é um identificador distribuível; não dá acesso administrativo à conta Cloud. Nenhum segredo administrativo/chave de conta de serviço/token pessoal acompanha o aplicativo. Tipo Desktop, API Calendar habilitada e configuração de consentimento pertencem ao projeto do mantenedor; só o identificador não comprova essas configurações.

O protocolo usa navegador, retorno loopback local, state e PKCE; tokens de usuário ficam no Secret Service. Embora a documentação Google descreva client_secret como opcional no fluxo geral, o cliente real do Orbitz retornou invalid_request/client_secret ausente em probe com código fictício. Ao fornecer a configuração Desktop completa indicada pelo mantenedor, esse erro desapareceu (invalid_grant esperado para o código fictício). Não foi obtido um token real nessa sonda. Não solicitar credenciais administrativas se o provedor recusar a configuração: diagnosticar o erro específico com o mantenedor. O fluxo anterior de JSON customizado permanece somente para compatibilidade técnica, fora da tela normal.

Preparação exclusiva do mantenedor: habilitar [Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com), configurar [Branding](https://console.cloud.google.com/auth/branding), [Audience/usuários de teste](https://console.cloud.google.com/auth/audience), [Data Access](https://console.cloud.google.com/auth/scopes) e cliente [Desktop em Clients](https://console.cloud.google.com/auth/clients). Escopos: `https://www.googleapis.com/auth/calendar.calendarlist.readonly` e `https://www.googleapis.com/auth/calendar.events.readonly`. Para contas pessoais, público externo; testes limitados às contas permitidas enquanto o projeto estiver nesse estado. Distribuição pública depende das exigências de verificação do Google. [Guia oficial](https://developers.google.com/identity/protocols/oauth2/native-app).

Este marco substitui a importação manual solicitada ao usuário em CAL-01/02. Implementação, revisão local e autenticação real são estados distintos; [parecer CAL-03](../audits/2026-10-19-google-login-audit.md):30 testes aprovados/2skips de socket; autorização real ainda pendente.

### Se a página local disser “Autorização recebida”

A mensagem indica somente que o retorno chegou ao aplicativo; a conclusão ocorre no Orbitz. Volte à janela do Workspace sem iniciar outro login. A conexão mostra a etapa atual: aguardando o Google, concluindo autorização, consultando calendários ou salvando no cofre. A conta só está conectada depois de o diálogo fechar com sucesso e a fonte aparecer no seletor. Em caso de falha, registre a mensagem do próprio Orbitz, sem códigos/tokens/arquivos privados.

CAL-04 corrige a perda de retorno válido quando ocorre falha ao enviar a página ao navegador; diagnóstico de erros de token usa apenas mensagens fixas/códigos conhecidos. Isso não comprova que toda falha real tenha a mesma causa. O aviso Google de aplicativo em teste é uma etapa distinta: usuários de teste precisam estar permitidos no projeto e autorizar os escopos.

### Preparação privada desta instalação

O mantenedor baixa o JSON do cliente Desktop próprio e executa a ferramenta do repositório:

```bash
/usr/bin/python3 tools/configure-google-client.py --from-json "/caminho/fora-do-repositorio/cliente-desktop.json"
/usr/bin/python3 tools/configure-google-client.py --check
```

A ferramenta aceita apenas o Client ID do Orbitz e guarda a configuração em `$XDG_CONFIG_HOME/orbitz-widgets/google-client.json` (padrão `~/.config/orbitz-widgets/google-client.json`), arquivo0600/diretório0700. Não colocar o JSON em Git/chat, logs ou dados de teste. Se existir configuração diferente, só substitui com `--replace` explícito. Não altera grants existentes nem faz login. O carregamento padrão passa a usar esse arquivo; formato/permissões/ID inválidos geram erro, sem fallback silencioso.

Essa preparação é do mantenedor desta instalação, não uma etapa do login normal de cada usuário. Não equivale a disponibilizar a configuração de uma versão pública para todos; empacotamento e verificação pública permanecem pendentes. Tokens pessoais continuam no Secret Service e não entram nesse arquivo nem no backup do Workspace.

## Calendly

Para esta instalação pessoal, gerar um Personal Access Token na conta Calendly com os escopos de leitura **users:read** e **scheduled_events:read**. No Workspace, abra **Integrar calendário → Calendly**, dê um nome à conexão e informe o token somente nesse formulário local. Não enviar tokens pelo chat nem versionar arquivos com credenciais. O conector consulta os eventos do próprio usuário; não oferece administração de organização, webhooks nem criação/cancelamento remoto de agendamentos.

PAT é apropriado ao uso privado/interno. Uma distribuição pública com autorização de clientes por OAuth próprio exigirá configuração e escopo futuros; não compartilhar um token do desenvolvedor com outras instalações.

## Brasil · Datas comemorativas — fonte padrão

Fonte pública ICS independente do login Google. A linha permanece em **Gerenciar conexões**, com **Ativar/Desativar**. Desativar preserva cadastro e cache, mas tira a fonte do seletor, sincronização, marcações e conteúdo da Agenda. A escolha persiste ao fechar/reabrir. Reativar permite selecionar e atualizar novamente; tarefas e horas não são removidas.

Ao atualizar uma instalação que excluiu esse cadastro, o aplicativo o recupera ativo ao abrir. Uma assinatura legada da mesma URL é reconhecida sem duplicação; a restauração não modifica contas pessoais. As demais fontes continuam com Desconectar normal. Uma desativação explícita após essa mudança não é revertida automaticamente.

## Dados e verificação

Caches são cópias locais e podem ficar desatualizados quando o acesso falha; consultar o indicador de atualização e usar a sincronização manual. Desconectar remove o acesso local e cache pertinente, preservando tarefas e timesheets. Revogação de consentimento/token na conta do provedor é uma operação distinta. Segredos não fazem parte do backup do Workspace.

Teste de aceite manual após instalação: conectar cada serviço, escolher a fonte, consultar um mês/dia com eventos, sincronizar, cancelar uma tentativa de conexão e desconectar. Conferir que uma tarefa criada explicitamente continua disponível depois de desconectar. Casos de erro/autorização expirada não devem apagar o cache anterior nem expor tokens.

## Referências oficiais

- [OAuth Google para desktop](https://developers.google.com/identity/protocols/oauth2/native-app).
- [Escopos da API Calendar](https://developers.google.com/workspace/calendar/api/auth).
- [Personal Access Tokens Calendly](https://developer.calendly.com/docs/authentication/how-to-authenticate-with-personal-access-tokens).
- [Escopos Calendly](https://developer.calendly.com/docs/authentication/scopes).
- [Consulta de eventos Calendly](https://developer.calendly.com/api-docs/calendly-api/scheduled-events/list-scheduled-events).

## About: distinguir a instalação preservada

A leitura dos artefatos em19/10/2026 confirmou: o About do UUID Orbitz instalado é idêntico à fonte e contém Orbitz1.0/SVG próprio; o About da instalação legada preservada contém Desktop Clock7/GitLab/PayPal, como na captura. O cadastro de extensões habilitadas aponta somente Orbitz. Isso identifica o conteúdo legado, mas não prova qual janela, cache ou lançador produziu a captura. Não sobrescrever a pasta legada nem repetir migração sem necessidade.

Fechar todas as janelas de preferências e abrir explicitamente a identidade atual:

```bash
gnome-extensions prefs orbitz-widgets@orbitzone.github.io
```

Se continuar exibindo Desktop Clock7, registrar o resultado junto de `gnome-extensions info orbitz-widgets@orbitzone.github.io`; não declarar a regressão resolvida sem essa confirmação visual.
