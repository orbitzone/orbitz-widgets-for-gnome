# Registro de decisões e restrições

Registro inicial em 17/10/2026. As entradas documentam instruções explícitas ou escolhas já presentes no código; não atribuem ao usuário decisões técnicas sem evidência. Alternativas futuras seguem como propostas no [backlog](backlog.md).

| ID | Natureza / estado | Decisão ou escolha existente | Evidência e consequência |
|---|---|---|---|
| D-01 | Instrução explícita · confirmado | Usar `/home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome` como repositório canônico desta missão. | Pedido recebido; checkout inspecionado em `2a24e0d`. Cadastro confirmado pelo usuário e pelo ambiente do projeto; pendência encerrada. |
| D-02 | Instrução explícita · confirmado | Primeira missão limitada à auditoria e aos três documentos; preservar alterações anteriores. | Pedido e contrato `docs/agents/project-owner.md`. Sem mudança funcional, commit, push, GNOME, instalação ativa, automação ou mensagens a outros chats. |
| D-03 | Contrato do papel · confirmado | Usuário decide objetivos, prioridades e escopo; agente propõe requisitos e prioridades com evidências. | `AGENTS.md` e contrato do papel. Responsabilidade persistente não significa execução contínua. |
| D-04 | Escolha existente · observada | Separar UI do Shell em GJS, aplicativos GTK/coletores em Python e preferências GTK 4. | `extension/extension.js`, `prefs.js`, `settings/`, `extension/planner/`, `widgets/`, `sticky-notes/`. Processos separados não isolam falhas da própria extensão no Shell. |
| D-05 | Escolha existente e contrato de preservação | Tarefas/timesheets são locais e independentes dos calendários externos; importação é explícita e sem escrita no provedor. | `store.py`, `timesheet.py`, `external_ui.py`, README e AGENTS. Desconectar fonte não deve apagar histórico local. |
| D-06 | Escolha existente e contrato de preservação | Credencial iCloud no Secret Service; metadados/cache em JSON. | `external_store.py`, classe `Vault`. Backup da agenda não inclui cofre; migração requer reconexão ou procedimento próprio. |
| D-07 | Escolha existente e contrato de preservação | Agenda usa lock e gravação atômica com fsync, backups de até 60 snapshots; notas usam SQLite WAL e backups próprios. | `store.py`, `sticky-notes/storage.py`. SQLite retém 14 backups diários no código. Estratégias distintas precisam de validação de recuperação separada. |
| D-08 | Escolha existente · observada | Sincronização externa depende da agenda aberta; alertas do Shell usam cache e têm ciclo próprio. | README, `external_ui.py`, `calendar.js`, `reminders.js`; `extension.js` chama `Calendar.enable`/`disable`. Fechar widgets não equivale a desativar lembretes; não existe serviço externo independente comprovado. |
| D-09 | Escolha herdada · observada | Preservados UUID/schema azclock e manifesto de GNOME 42/43/44. | `metadata.json` e schemas. Não há decisão nesta missão de mudar identidade nem evidência de validação completa dessas versões. |
| D-10 | Restrição operacional · confirmada | Não mover/apagar caminhos históricos sem mapear comandos e preservar auxiliares/dados. | Pedido, AGENTS, README e stack. O repositório reúne fontes, mas não substitui automaticamente a instalação ativa. Migração permanece proposta B-03. |
| D-11 | Restrição de evidência · confirmada | Resultados da publicação são históricos, não execução desta missão. | README e contrato: 44 Python, 12/15 JS, três falhas conhecidas; ausência de teste gráfico completo nessa publicação. Não declarar suíte integralmente aprovada. |
| D-12 | Contrato de preservação · confirmado | Manter créditos/licenças, inclusive bibliotecas vendorizadas e termos próprios de ferramentas. | AGENTS, arquivos LICENSE, `extension/planner/vendor/`, `extension/speedtest.md`. Empacotamento exige revisão específica; nenhuma dependência foi modificada. |

## Decisões ainda necessárias

1. Ambiente obrigatório e matriz de compatibilidade da instalação reproduzível (B-02/B-06).
2. Destino de instalação dos coletores e estratégia reversível para comandos/configurações existentes (B-03).
3. Comportamento esperado da região de clique do armazenamento, caso a investigação B-01 confirme divergência de produto.
4. Distribuição, atualização e política de identidade/metadados (B-07).

Não há aprovação registrada dessas alternativas, responsáveis de implementação definidos ou prazos assumidos.

## D-13 — Equipe especializada (18/10/2026)

Usuário autorizou criação de três chats dedicados e comunicação entre supervisor, backend, frontend e auditor; backend/frontend podem alinhar interfaces entre si. Supervisor centraliza documentação e encaminha entregas ao auditor. Refatoração de todo código próprio autorizada, preservando contratos e sem alterações na instalação ativa. Divisão e critérios: `agents/team.md`.

## D-14 — Responsabilidade pelo conhecimento do projeto (18/10/2026)

Confirmado pelo usuário: analista centraliza contexto e pesquisa do projeto; especialistas recebem informação direcionada e reportam mudanças/lacunas. Implementado nos contratos e no índice `docs/project-context.md`. Critério: cada tarefa aponta arquivos, contratos, aceite e evidências; cada entrega atualiza referências afetadas. Leitura local necessária e auditoria independente não são dispensadas; conhecimento completo de cada linha não foi comprovado.

## D-15 — Design/UX e práticas da equipe (18/10/2026)

Usuário aprovou todas as recomendações de coordenação/qualidade e solicitou agente Design/UX com comunicação exclusiva ao frontend. Frontend responde ao UX por revisão visual e ao analista por requisitos/documentação; não elimina alinhamento técnico com backend. UX registra padrões e relatórios em `docs/design/`, sem editar código nem contatar outros agentes. A primeira revisão é diagnóstica; redesign não é misturado à refatoração que preserva aparência.

## D-16 — Autonomia e definição de conclusão (18/10/2026)

Usuário aprovou as recomendações de responsabilidades e processo ágil. Especialistas têm autonomia dentro do escopo e podem investigar o necessário sem aguardar o analista; registram conclusões para contexto/documentação. Auditor mantém independência e pode alinhar achados críticos diretamente com backend/frontend, mantendo supervisor informado. UX continua exclusivo ao frontend. Entregas pequenas exigem aceite, verificações pertinentes, documentação e tratamento dos achados impeditivos; melhorias opcionais ficam separadas. Validações funcional, visual e de segurança são registradas individualmente. Sem nova autorização de deploy, instalação ativa, publicação ou monitoramento contínuo.

## Errata de evidência — baseline JavaScript (18/10/2026)

Auditor reconciliou lista nominal e inventário: 14 arquivos JS originais, 11 aprovados e três falhas. Corrige o resumo 12/15 anteriormente fornecido e reproduzido nos registros, sem alterar a identidade das falhas nem afirmar nova execução histórica. A execução integrada RF-01 foi relatada com 16 arquivos JS e 62 testes Python aprovados, separada da baseline; aguarda relatório final de revisão.

## D-17 — Aceite parcial RF-01 após auditoria (18/10/2026)

Supervisor conferiu relatório independente `audits/2026-10-18-integrated-audit.md` e aceitou as verificações funcionais locais/estruturais e a revisão delimitada de segurança/integridade (62 Python, 16 arquivos JS, 102 sintaxes, sem impeditivo reproduzido). Validação visual/interativa permanece pendente por bloqueio Broadway, sem ampliação de permissões ou uso da sessão ativa. Não declarar RF-01 integralmente concluída, ganho de desempenho ou autorização de distribuição. Próxima evidência cabe a frontend/UX quando houver ambiente isolado permitido.

## D-18 — Atualização local e bloqueio do sandbox

Usuário autorizou atualização reversível, sem reinício automático. Plano preparado em `tools/update-local.py`, com coletores em diretório estável e migração limitada a comandos conhecidos, backups privados fora do repositório e rollback por manifesto. Aplicação do agente bloqueada por filesystem somente leitura em `~/.local/share`, antes de alteração instalada/configuração. Não contornar restrição nem declarar instalação pronta; execução com acesso aos destinos e confirmação de hashes é necessária. Guia em `operations/local-update.md`; revisão independente do instalador corrigido ainda pendente neste marco.

## D-19 — Supervisor libera teste da versão instalada (18/10/2026)

Usuário atribuiu ao analista a responsabilidade de conferir prontidão de cada atualização e avisar quando reiniciar a sessão para teste. A liberação exige confirmar aplicação e componentes instalados, sem confundir checkout com instalação nem testes locais com validação gráfica. Orientação manual proporcional ao componente; não reiniciar automaticamente. DEP-01 continua sem confirmação de aplicação enquanto não houver resultado/verificação da execução no terminal do usuário.

## D-20 — Padrão histórico do resumo Hardware (18/10/2026)

Usuário solicitou recuperar tamanhos anteriores e mantê-los como padrão. Valores comprovados no coletor histórico: monospace, size7680 unidades Pango (7,5 pt), line_height1.5, barras de oito células e linhas sem vazios. Backup/configuração atual mantêm padding L/R20 e demais valores visuais; não alterar GSettings para compensar regressão no markup. Reparar apresentação sem mudanças de métricas/cache/dispositivos. Frontend encaminha ao UX registro e revisão do padrão.

## D-21 — Versionar estado atual com pendências explícitas

Usuário solicitou prosseguir com commit/push em 18/10/2026. Supervisor consolidou README/stack/backlog e executou verificação completa atual (71 Python,17 Node,GJS/Pango aprovados). Estado pode ser versionado como refatoração/correções com clique RAM e validação gráfica pendentes, sem declarar release integralmente aprovada. Operações Git da ferramenta impedidas: .git somente leitura para fetch e DNS do GitHub indisponível para ls-remote. Publicação ainda não realizada; sem force-push ou integração remota automática.

## D-22 — Identidade Orbitz e preservação da origem

Usuário pediu projeto próprio atribuído a si, com menor destaque ao template de origem e identificador ligado ao seu GitHub. Supervisor escolheu UUID orbitz-widgets@orbitzone.github.io e schema org.gnome.shell.extensions.orbitz-widgets, metadados/links Orbitz e version 1 como linha própria. Não representa domínio web publicado nem release totalmente validada. Créditos/licenças herdados ficam preservados, concentrados em docs/credits.md; retirar CTA/doações upstream da apresentação principal sem inventar dados financeiros do usuário. Compatibilidade de tradução e schema legado mantida para migração; dados/cofre independentes do UUID não serão movidos. Migração e ativação exigem procedimento explícito e rollback, sem execução automática na sessão ativa do agente.

### Complemento D-22 — namespace GObject e versões de licença exibidas

Reprodução com GObject confirmou que GTypes implícitos do legado permanecem registrados após desativação. Para permitir carregamento sequencial das identidades no mesmo processo, os 20 registros recebem GTypeName OrbitzWidgets explícitos; nomes JS/exports e controlador plain preservados. Registro representativo de 20 pares legado/Orbitz passou com GObject real, sem provar ativação completa no Shell. Corrigido também aviso UI herdado que apontava GPL2 enquanto LICENSE distribuído contém outro texto: a página passa a referenciar o arquivo LICENSE do projeto de forma neutra, preservando avisos/arquivos sem relicenciamento ou conclusão jurídica adicional.

### Aceite local D-22

Supervisor conferiu relatório frontend/backend/auditoria ID01. Identidade própria, preservação de créditos/licenças e ferramentas estão prontas para preparo humano, com limites documentados. Suíte global do alvo anterior aprovada83 testes Python/18 arquivos Node/2 testes GJS; após correção de remoção parcial, auditor verificou11 testes do migrador e proteções de subset/conflito. Sem impeditivo reproduzido remanescente no escopo; não confundir preparo com ativação ou aceitação visual. Nova etapa começa pelo --prepare no terminal, sem reinício imediato nem ativação automática.

## D-23 — Identidade visual própria e versão exibida

Pedido explícito de logo nova e versão 1.0. Implementação em vetor SVG nativo para escala/integrar GNOME, com origem gráfica própria do Orbitz; não reutilizar o relógio da base como marca. Version-name1.0 para apresentação com version inteiro 1 preservado. Preferências serão abertas pelo UUID Orbitz para evitar confusão com janela/página da instalação legada ainda preservada para rollback. Atribuições e licença não serão apagadas; ficam na seção própria discreta.

## D-24 — Invoice local e critérios monetários

Pedido do usuário confirmado para PDF de serviços a partir das horas da timesheet, com partes/CPF-CNPJ/endereço cliente e PT/EN. Decisões técnicas: minutos inteiros e Decimal, arredondamento final centesimal, perfil emitente global e cliente/taxa/moeda por sheet, persistência privada separada. Todo histórico explícito inicialmente e período opcional, BRL padrão editável independente do idioma. Não incluir cronômetro em andamento/lixeira nem marcar automaticamente registros como faturados. O PDF será identificado como fatura/invoice de serviços, sem integração fiscal eletrônica ou cálculo tributário. ReportLab disponível nativamente é usado para paginação/PDF; supervisor aplica skillPDF para QA visual das amostras sintéticas.

## D-25 — Mês civil e intervalo inclusivo no calendário da invoice

19/10/2026. Pedido de três modos e calendário único. Decisão técnica: “1 mês” significa mês civil escolhido, não últimos 30 dias; “histórico” preserva default anterior. Modo específico usa dois cliques para início/fim inclusivos, ordenados se necessário, e permite navegar entre meses/anos sem selecionar automaticamente. Resumo e destaque evitam ambiguidade; incompleto impede revisão. Contrato existente start/end ISO alimenta domínio sem migração ou alteração monetária. Componente da agenda preservado, pois sua navegação atual também emite seleção de dia.

## D-26 — Arquivo local imutável de invoices e limites de exclusão

19/10/2026. Histórico mantém cópia exata dos PDFs gerados a partir da atualização, mais snapshot dos dados de emissão. Empresa significa timesheet e a competência de organização usa mês/ano de emissão, com período dos serviços separado e explícito. IDs internos distinguem registros e clientes homônimos, sem nomes/documentos em caminhos. Download exporta cópia; excluir atua exclusivamente no acervo gerenciado após confirmação, preservando exportações externas e dados de trabalho. Erro após salvar PDF externo gera aviso parcial e não equivale a falha retroativa da exportação. Sem importação/varrimento de arquivos antigos por inferência.

## D-27 — Portais externos e honestidade do estado de assinatura

19/10/2026. Usuário aprovou integração assistida após consulta oficial: API GOV.BR não disponível para este aplicativo privado. Abrir URLs oficiais fixas após ações explícitas; usuário controla login, upload e download. Importação guarda nova versão privada vinculada sem substituir original; hash associa bytes e registro, não autentica assinatura/conteúdo. Estado permanece pendente, mesmo após abrir VALIDAR ou confirmação manual. Sem bibliotecas novas de assinatura, validação criptográfica, tokens ou automação de navegador nesta etapa. Não alterar/regerar PDF assinado.

D-27 — apresentação de versões: decisão técnica do supervisor aceita o diálogo separado “Original e versões…” acessível pela invoice no histórico, em vez de expandir cada versão na árvore principal. O pedido aprovado não exige árvore inline; essa escolha evita ler versões de todo o acervo ao recarregar a listagem. A linha principal identifica a invoice, e “Original” identifica o PDF dentro da tela de versões. Não se afirma equivalência visual por testes de lógica.

## D-28 — Revisão por lote e risco, UX sob demanda

19/10/2026. Usuário apontou custo excessivo do fluxo e pouco retorno de Design/UX. Supervisor substitui revisão independente por incremento por fila de sprint para risco médio, mantendo testes locais e revisão antecipada para operações de alto risco. IH-A01/IH-A02 foram defeitos reais encontrados nas auditorias de histórico; isso fundamenta preservar o gate de dados/exclusão, sem transformar rótulos/ajustes visuais em auditorias. UX passa a consultoria focada, frontend aplica padrões básicos. Contratos/contexto ativos compactados, versões anteriores preservadas em `docs/archive/2026-10-19-agent-workflow/`. Sem calendário automático, novos agentes ou alteração de modelos. Referência única: `docs/agents/workflow.md`.

## D-29 — Espaço de trabalho e referências da timesheet

19/10/2026, todas recomendações aceitas pelo usuário. O aplicativo da agenda passa a Orbitz Workspace (sem mudar UUID/schema da extensão). Cliente/contratante, contrato/projeto e departamento/centro de custo são referências opcionais de trabalho, separadas do nome identificador e do destinatário fiscal da invoice. Compatibilidade sem descarte/migração destrutiva. Nova navegação e Hoje reutilizam componentes; duplicidade é aviso, pagamento é informação manual e assinatura continua pendente até verificação externa real. Backup/restauração cobrem somente os dados listados de Workspace, preservando cofre/externos/outros aplicativos. Lote WSP-01 recebe uma auditoria final porque contém dados/backup, sem acionar UX por hábito.

## D-30 — Integrações de calendário com acesso de consulta (19/10/2026)

RC-22/CAL-01: Google usa OAuth de aplicativo desktop com navegador, state e PKCE; requer cliente OAuth real com API Calendar habilitada. Calendly inicia com PAT pessoal adequado à instalação privada, não com um token compartilhado embutido; uma oferta pública com OAuth próprio é escopo futuro. Consulta periódica/manual em vez de webhooks/servidor público. Persistir segredos exclusivamente no Secret Service, sem modificar calendários remotos nem vincular a existência das tarefas/horas à conexão. Implementação e mocks não provam autorização real.

Referências oficiais consultadas: [Google OAuth desktop](https://developers.google.com/identity/protocols/oauth2/native-app), [escopos Calendar](https://developers.google.com/workspace/calendar/api/auth), [PAT Calendly](https://developer.calendly.com/docs/authentication/how-to-authenticate-with-personal-access-tokens), [escopos Calendly](https://developer.calendly.com/docs/authentication/scopes).

## D-31 — Identidade OAuth pública do Orbitz e login direto (19/10/2026)

RC-25/CAL-03 substitui o preparo Cloud/JSON exigido ao usuário em CAL-01/02. O mantenedor forneceu um Client ID público do próprio aplicativo; a configuração padrão contém apenas esse identificador. A interface oferece Entrar com Google com autorização no navegador, sem projetar a configuração do desenvolvedor sobre o usuário final. JSON customizado permanece compatível internamente, assim como grants anteriores. Não inventar client_secret nem distribuir chaves administrativas/tokens. Documentação oficial declara esse parâmetro opcional no fluxo desktop com PKCE; isso não substitui teste real do cliente e consentimento. Operação normal não requer backend público: navegador e retorno loopback já existentes. Escopos somente leitura e cofre permanecem.

## D-32 — Configuração Desktop completa fora da interface pública (19/10/2026)

RC-27/CAL-05: apesar de client_secret constar como opcional na documentação geral desktop, o cliente real recusou a troca sem esse parâmetro. Sonda oficial com código fictício confirmou ausência; configuração Desktop completa fornecida pelo mantenedor removeu esse erro (invalid_grant esperado para código fictício). Manter valores reais fora do repositório/chat e carregar configuração privada validada nesta instalação. Setup de mantenedor não volta à UI normal, que permanece Entrar com Google. Não anunciar distribuição pública configurada por causa desse setup local, nem solicitar senha Google/chave administrativa. Preservar tokens/grants existentes no cofre.
