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

## D-36 — Pesquisa inicial de fontes para FX-01 (20/10/2026)

Parecer técnico, não decisão de provedor nem autorização de gasto: Frankfurter v2 oferece cotações diárias de 223 moedas oriundas de 104 bancos centrais/fontes oficiais, sem chave; atualiza em dias úteis e é informativa, não cotação transacional. Adequado como candidato para o widget fiduciário, com data da taxa exibida e conversão calculada localmente. Fontes: [documentação Frankfurter](https://frankfurter.dev/v1/) e [metodologia/atualização ECB](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html).

Implementação inicial (20/10/2026): adotada como fonte técnica do protótipo fiat, não como garantia de cotação em tempo real. `widgets/fx_rates.py` usa v2 e valida moeda/par/valor/data; `currency-widget.py` e o preset Settings apresentam conversão diária, seletor pesquisável e inversão. A data é validada internamente, mas não aparece no estado normal do widget. Essa escolha não inclui cripto nem serviço pago; teste GTK real pendente.

Para cripto, CoinPaprika declara o plano sem chave como uso pessoal e exige Enterprise para redistribuir dados a clientes; CoinGecko Demo gratuito não concede direitos comerciais de exibição; CoinMarketCap tem API keyless com subconjunto e limites compartilhados por IP, mas sua documentação recomenda chave Basic gratuita para produção. Em 21/10/2026 a implementação do widget unificado selecionou provisoriamente o endpoint CoinPaprika sem chave para uso pessoal, sem que isso configure liberação para distribuição comercial. Antes de anunciar ou oferecer o feed como parte de produto comercial, escolher provedor/licença compatível ou integração com chave própria do usuário; não embutir segredo compartilhado. Fontes primárias: [CoinPaprika API](https://coinpaprika.com/api), [termos/licença CoinPaprika](https://coinpaprika.com/terms-api), [planos CoinPaprika](https://coinpaprika.com/api/pricing), [termos/licença CoinGecko](https://www.coingecko.com/en/api_terms) e [API Keyless/planos CoinMarketCap](https://coinmarketcap.com/api/documentation/pro-api-reference/keyless-public-api/).

Decisão de escopo em 21/10/2026, confirmada pelo usuário: não manter widgets de conversão fiat e Bitcoin separados; oferecer seleção Fiat/Crypto no mesmo **Conversor de moedas**. Esta decisão de interface não altera nem aprova os termos de uso do feed.

## D-37 — Cadência e fonte de conversão fiat (20/10/2026)

Requisito confirmado pelo usuário: consultar somente o endpoint da cotação mais recente, sem previsão, busca de datas históricas ou fallback de cache antigo; atualização automática a cada quatro horas e ação manual na modal do widget. A taxa Frankfurter é diária em dias úteis, portanto o polling de quatro horas apenas verifica se a publicação diária mudou e pode retornar o mesmo valor. Fins de semana/feriados podem ter data anterior sem constituir busca histórica; não impor um limite que rejeite essa publicação normal. Apenas par e valor aparecem no widget. Frontend implementou na fonte polling de 14.400.000 ms, modal acionável no widget, atualização manual e inversão persistida no comando; verificação visual/instalação ainda pendente. Esta decisão atualiza a proposta inicial D-36 de exibir data junto à taxa.

## D-38 — Precisão visível do conversor fiduciário (20/10/2026; esclarecida em 21/10)

Pedido explícito para Fiat: remover dígitos excessivos e mostrar duas casas. Em 21/10, o usuário esclareceu que a regra deve preservar centavos e arredondar metade para cima (`0.19829 → 0,20`), substituindo o truncamento anterior (`0.19`). Valores Fiat abaixo de `0.005` aparecem `0,00`; o valor original segue intacto na consulta. Cripto tem regra própria: USD→ativo preserva os dígitos recebidos para não zerar frações pequenas; ativo→USD usa centavos. Ver RC-40 e FX-01/03.

## D-39 — Idioma da interface configurável PT-BR / EN-US (21/10/2026)

Pedido confirmado: adicionar seletor em Settings, alinhado ao Add Widget, para Português (Brasil) e English (United States), cobrindo a interface Orbitz. Decisão de implementação: idioma persistido em GSettings, PT-BR como padrão/fallback, catálogo JSON comum com IDs semânticos e valores em ambos os idiomas. A seleção atualiza as janelas abertas sem reiniciar a sessão. Não traduzir conteúdo escrito pelo usuário, nomes/dados de serviços externos, IDs/protocolos/comandos ou documentos cujo idioma seja controlado por configuração própria (como invoice PDF); não alterar dados armazenados. Implementação de fonte concluída em 22/10/2026; testes funcionais de código passaram, mas instalação e validação visual ainda não comprovadas.

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

## D-40 — Previsão do tempo interativa (22/10/2026)

Pedido confirmado: resumo do clima traduzido, modal ao clicar com sete dias em sete colunas, unidade °C/°F e localização selecionável por país → região → cidade. Open-Meteo permanece como fonte de previsão; a atribuição deve ser apresentada e o uso grátis segue os termos não comerciais publicados pelo provedor. A Geocoding API busca localidades por nome e código do país, mas não fornece catálogos completos de países/regiões/cidades. Para os dropdowns, backend adotou snapshot versionado v5.0.0-export.1 do [Countries States Cities Database](https://github.com/dr5hn/countries-states-cities-database/releases/tag/v5.0.0-export.1), sob ODbL 1.0; suas notices de distribuição devem acompanhar a cópia e a atribuição deve ficar visível. A cascata representa a cobertura publicada desse catálogo, não toda povoação mundial. Preferências de local/unidade persistem; resumo legado segue compatível. Implementação em andamento, sem teste visual/instalação ou decisão de atualização futura do catálogo.

Referências: [Open-Meteo Forecast API](https://open-meteo.com/en/docs), [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api), [Open-Meteo Terms](https://open-meteo.com/en/terms), [CSC release e licença](https://github.com/dr5hn/countries-states-cities-database/releases/tag/v5.0.0-export.1).

## D-41 — Busca única de localidade e atualização imediata do resumo (22/10/2026)

O usuário substituiu a cascata de três seletores por um único campo de busca, botão Pesquisar e resultados selecionáveis no formato Cidade · Região · País. A interface usa `--geocode` da Open-Meteo/GeoNames, limitada a dez correspondências por consulta; não apresenta o conjunto como catálogo completo. Seleção persiste coordenadas, fuso e rótulos por CAS; preferências e unidades preexistentes permanecem compatíveis. O usuário também reportou que selecionar °F só alterava a previsão da modal. Depois do ACK da persistência, o CommandLabel cancela uma execução antiga e solicita atualização imediata do resumo do desktop, mantendo o intervalo regular. Isso supersede D-40 na interação de localização, mas preserva sua fonte de previsão, modal, unidades e atribuição. Implementação na fonte e testes locais concluídos; busca externa real, instalação e conferência visual permanecem pendentes.

Referência: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api), com dados de localização baseados em GeoNames.

## D-42 — Colunas do forecast e ícones diários (22/10/2026)

Para evitar que a modal de sete dias force uma barra horizontal, cada coluna divide igualmente a largura interna disponível e seus rótulos podem quebrar linha. A UI mantém sete dias visíveis; a rolagem vertical da própria modal continua disponível para conteúdo fora da altura da tela. Cada dia recebe ícone da condição WMO predominante. A API Forecast fornece velocidade máxima diária do vento de 10 m (`wind_speed_10m_max`); o collector solicita km/h, valida os sete valores e a unidade, e invalida o namespace anterior de cache. A apresentação usa ícone de vento a partir de 40 km/h; trovoadas WMO 95/96/99 conservam precedência. O limiar é convenção visual do produto, não alerta meteorológico. Testes dirigidos de contrato, ícones e geometria sintética passaram; sem sessão GNOME não houve verificação visual real.

Referência: [Open-Meteo Forecast API — variáveis diárias](https://open-meteo.com/en/docs#daily).

## D-43 — Emoji e exclusão direta de Sticky Notes (22/10/2026)

O seletor de emoji deve ser uma janela GTK espaçosa e transitória da nota, com ponto de inserção salvo e foco restaurado. O menu não apresenta mais ações de arquivar/restaurar; notas legadas com `archived=1` são mostradas como notas comuns para não ocultá-las nem migrá-las destrutivamente. “Delete note” e a soltura sobre a lixeira removem a linha ativa da tabela SQLite com comparação de revisão; conflito ou erro mantém a nota. A ação no menu e o drop são diretos, conforme o pedido de notas descartáveis. A pedido do usuário, a operação purga a mesma nota, por ID, de todos os snapshots diários retidos antes de concluir a exclusão no banco ativo; se qualquer purga falhar, falha fechada, preserva a linha ativa e permite retry. A reauditoria independente aprovou esse delta sem residual nos casos testados. Limite: processos maliciosos sob o mesmo UID não são isolados entre a verificação final e o commit; a substituição de vários snapshots também não forma uma transação filesystem única, mas falha parcial preserva a nota ativa. A lixeira flutuante usa coordenadas raiz disponíveis no X11/XWayland, que é o backend escolhido pelos launchers Orbitz; sessão GTK nativa Wayland recebe indicação para usar “Delete note” no menu, pois não há coordenada global confiável para hit-test. Inspeção GTK real pendente.

## D-44 — Limpeza do modal e ciclo de vida de Sticky Notes (22/10/2026)

O backdrop do modal deve tornar-se não reativo antes de ocultar e cada limpeza de processo/timer deve ser independente, para que uma exceção não deixe a extensão interceptando a tela. O token de grab é descartado após chamar `popModal`, mesmo quando há exceção, porque o Shell pode já ter alterado estado interno; o sinal `destroy` também sincroniza o token quando o ator é descartado automaticamente. Na inicialização, iniciar Sticky Notes após validar configurações e antes de construir widgets; rollback de widgets não deve encerrar esse processo independente. Isso é uma mitigação revisada para teste local, não comprovação de que o travamento de input reportado foi resolvido: ainda requer smoke GNOME e captura de log se voltar a ocorrer.

## D-45 — Controles do cabeçalho e gesto para a lixeira (22/10/2026)

O cabeçalho das Sticky Notes não inicia movimento customizado: o botão dropdown substitui o indicador de arraste e compartilha o menu do clique direito; tooltips da nota são suprimidos enquanto o menu está aberto. Para manter a lixeira sem a área de drag and drop no topo, Design/UX recomendou Shift+arraste pela margem inferior vazia, sem sobreposição com edição, links, botões ou resize. A UI exibe a dica e mantém “Delete note” no menu. X11/XWayland oferece as coordenadas do alvo da lixeira; no Wayland GTK nativo o menu é a alternativa acessível. Código e testes sintéticos passam; validação visual/gestual real ainda pendente.

## D-46 — Escopo de segurança para Secret Notes (22/10/2026)

O usuário escolheu proteger a visualização somente pela interface; a primeira entrega não criptografa texto no SQLite nem nos backups. A UI deve tratar isso como bloqueio visual local e documentação/README devem explicar claramente que acesso direto aos arquivos continua revelando o conteúdo. PIN numérico de quatro dígitos é global às notas; sua troca exige o PIN atual. Para impedir bypass trivial pela própria UI, excluir ou remover o estado secreto também exige autenticação. Notas secretas iniciam bloqueadas, e o contador de 15 segundos começa no evento de saída do ponteiro, cancela quando retorna e bloqueia/oculta corpo e título ao terminar. Não persistir estado desbloqueado nem o PIN em texto claro; auditoria independente focada é requisito antes de aplicar a instalação.

## D-47 — Distribuição independente das Sticky Notes (27/10/2026)

Usuário confirmou distribuições Linux e criação de repositório GitHub. Adotado Flatpak em `orbitzone/orbitz-sticky-notes`, sem retirar as fontes/integração atuais nem mover dados históricos. Inicialmente x86_64 com X11/XWayland para conservar posicionamento/lixeira; compatibilidade com outras arquiteturas e desktops requer evidência própria. Traduções e schema passam a pertencer ao aplicativo independente. Dados do Flatpak são isolados e não recebem migração automática. Publicar fontes após revisão focada do instalador e disponibilizar bundle somente após build/smoke de CI. Não há publicação no Flathub nem ativação do novo aplicativo nesta entrega.

## D-48 — Distribuição independente do YouTube Desktop (27/10/2026)

Pedido confirmado: mini app independente chamado **Orbitz YouTube Desktop**, inicialmente com repositório GitHub `orbitz-youtube-desktop`, renomeado depois para `orbitz-youtube-wrapper` por decisão D-51. Primeiro alvo x86_64, runtime GNOME 49, X11/XWayland; sem afirmar compatibilidade universal, Windows/macOS, Flathub ou Wayland sem XWayland. Não importar API key/cache/preferências da instalação Orbitz integrada; guardar chave e cache em diretório próprio. API key serve à busca/comentários, não fornece fluxo de mídia nem remove anúncios; o player oficial incorporado pode exibi-los. Publicação de bundle fica condicionada a CI/build. Revisão de segurança restringe o bridge externo a hosts/caminhos exatos, com risco residual de abrir um desses destinos sem clique por conteúdo da WebView.

## D-49 — Atalhos para os mini apps independentes (28/10/2026)

O primeiro passo de RC-59 fez os atalhos Notes/YouTube da extensão chamarem os Flatpaks independentes, preservando dados antigos e sem migrar credenciais/notas. Em RC-57, a decisão final passou a remover esses atalhos do widget; a extensão não deve iniciar nem encerrar os mini apps. RC-62 remove também a implementação YouTube integrada e seus testes/catálogos. A chave antiga permanece no perfil local sem migração.

## D-50 — Token e allowlist nos bridges nativos do YouTube (28/10/2026)

Handlers WebKit são interfaces nativas acessíveis aos frames da WebView, portanto nenhum payload pode ser aceito apenas por ter vindo do `index.html`: cada ação valida o token aleatório da janela e rejeita mensagens acima de 4096 caracteres. O handler de abertura externa aceita somente URLs HTTPS dos destinos fixos da interface e IDs válidos de vídeo; popups solicitados diretamente pelo player seguem bloqueados. A troca de aba invalida operações pendentes de busca/recomendações. A auditoria focada encontrou e guiou a correção desses riscos; a reauditoria passou, sem bloqueios. Permanece risco baixo de carga por volume alto de mensagens inválidas curtas.

## D-51 — Slug do repositório YouTube Wrapper (28/10/2026)

Por pedido do usuário, `orbitzone/orbitz-youtube-desktop` passa a se chamar `orbitzone/orbitz-youtube-wrapper`. O slug também nomeia o executável, diretório de instalação/configuração/cache e artefatos gerados pelo CI. O ID Flatpak/GSettings `io.orbitz.YouTubeDesktop` permanece estável para não criar uma segunda identidade de app nem ocultar preferências salvas. A leitura da chave mantém fallback somente de leitura no caminho de configuração legado; novas gravações usam o diretório com o nome atual. O bundle da release v0.1.0 mantém seu nome de arquivo publicado.

## D-49 — Identidade, idioma e filtros dos mini apps (28/10/2026)

Os nomes públicos e de janela passam a ser **Sticky Notes - By Orbitz** e **YouTube Wrapper - By Orbitz**. Cada repositório mantém seu próprio catálogo PT/EN e sua preferência persistida via GSettings, sem depender da extensão. A extensão deixa de renderizar atalhos para Sticky Notes e YouTube; elementos salvos antigos permanecem como rótulos de texto e Gemini/btop continuam como atalhos. O filtro Podcasts envia uma busca de relevância com o prefixo `podcast`, pois a YouTube Data API não oferece um filtro categórico de podcasts; a interface explicita que pode retornar outros vídeos. Fontes atualizadas nesta tarefa; instalar/reiniciar e publicar são etapas separadas.


## D-52 — Remoção reversível do YouTube integrado (28/10/2026)

YouTube é mantido somente como mini app independente em `orbitz-youtube-wrapper`. O checkout de widgets não conserva a WebView/servidor antigo nem apresenta um launcher para o mini app; a descoberta MPRIS reconhece o novo app ID. O atualizador local usa caminhos exatos para os seis arquivos e regex restrita aos bytecodes Python correspondentes, criando backup privado e entrada de rollback por arquivo. Nenhuma configuração/chave/cache de dados do usuário é migrada ou apagada.
