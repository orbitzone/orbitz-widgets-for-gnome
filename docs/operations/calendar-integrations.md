# Google Calendar e Calendly — configuração local

Escopo CAL-01/RC-22, 19/10/2026. Implementação e auditoria focada concluídas nas fontes; autorização real e interação GTK precisam de teste separado. [Parecer CAL-01](../audits/2026-10-19-calendar-audit.md):35 testes aprovados,2skips ambientais de sockets e teste Node de identidade aprovado. A integração consulta eventos e permite criar uma tarefa local por ação explícita. Não cria, altera, cancela ou exclui eventos remotos. Tarefas e horas não dependem da continuidade da conexão.

## Google Calendar

Pré-requisitos externos: projeto no Google Cloud, Google Calendar API habilitada, tela de consentimento configurada e cliente OAuth do tipo **Desktop app**. Se o projeto estiver em teste, a conta precisa estar permitida como usuário de teste conforme a configuração do Google. Regras de verificação, expiração e acesso são controladas pelo provedor; não há promessa de login público sem configuração.

No Workspace, abra **Integrar calendário → Google Calendar**, dê um nome à conexão e escolha o JSON baixado do cliente OAuth desktop. Clique em Conectar. A conexão abre o navegador do sistema e recebe a resposta em endereço loopback local; state e PKCE vinculam o retorno à solicitação. A configuração do cliente deve ser fornecida localmente; não existe cliente OAuth fictício ou senha Google embutida. Credenciais de acesso e renovação pertencem ao Secret Service, fora do cache e dos backups do Workspace.

## Calendly

Para esta instalação pessoal, gerar um Personal Access Token na conta Calendly com os escopos de leitura **users:read** e **scheduled_events:read**. No Workspace, abra **Integrar calendário → Calendly**, dê um nome à conexão e informe o token somente nesse formulário local. Não enviar tokens pelo chat nem versionar arquivos com credenciais. O conector consulta os eventos do próprio usuário; não oferece administração de organização, webhooks nem criação/cancelamento remoto de agendamentos.

PAT é apropriado ao uso privado/interno. Uma distribuição pública com autorização de clientes por OAuth próprio exigirá configuração e escopo futuros; não compartilhar um token do desenvolvedor com outras instalações.

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
