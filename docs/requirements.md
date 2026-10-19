# Requisitos e critérios de aceite

Registro inicial em 17/10/2026, sobre o checkout `2a24e0d` e a documentação local já alterada. Fontes: pedido desta missão, `AGENTS.md`, `docs/agents/project-owner.md`, `README.md`, `stack.md` e inspeção estática dos componentes abaixo. Não substitui validação funcional.

## Classificação e evidências

- **Confirmado:** instrução explícita do usuário ou contrato do papel; não significa implementação validada.
- **Observado:** comportamento descrito na documentação e sustentado pela estrutura/código; implementação sem validação nesta missão.
- **Proposto:** critério ou evolução sugerida, pendente de decisão quando afetar escopo.
- **Validado:** reservado a evidência de execução identificada. Nenhum comportamento do desktop recebeu esse estado nesta auditoria.

## Requisitos confirmados desta missão

| ID | Requisito | Critério de aceite | Situação |
|---|---|---|---|
| RC-01 | Manter documentação, requisitos, backlog e decisões verificáveis. | Os três registros existem, distinguem origem, estado, evidência e pendências. | Confirmado; documentos entregues nesta missão. |
| RC-02 | Preservar alterações anteriores e limitar a entrega à documentação. | Diff desta missão acrescenta somente os três documentos; sem mudança funcional, commit, push, instalação ou recarga do GNOME. | Confirmado; conferência pelo diff e escopo dos comandos. |
| RC-03 | Preservar dados, backups, gravações atômicas, credenciais, independência das tarefas/timesheets e licenças. | Toda futura mudança apresenta evidência proporcional de preservação desses contratos; dados pessoais e segredos não entram no repositório. | Confirmado pelo contrato; aplicação funcional futura. |
| RC-04 | Tratar falhas JS, instalação reproduzível e caminhos históricos como propostas. | Backlog contém investigação e critérios verificáveis, sem correções nesta missão. | Confirmado; registrado. |

## Comportamentos observados e critérios propostos para regressão

Os critérios abaixo descrevem resultados a verificar em entregas futuras; não são novos pedidos aprovados pelo usuário nem testes executados agora.

| ID | Comportamento observado / fonte | Critério de aceite proposto |
|---|---|---|
| RO-01 | Extensão GJS com widgets, preferências e grupos (`extension/extension.js`, `settings/`, `dragging.js`, `grouping.js`). README descreve início pausado e controlador branco. | Ao ativar/login, widgets começam pausados; abrir/fechar pelo controlador funciona repetidamente e encerra atores, sinais, timers e coletores sem apagar dados. |
| RO-02 | Coletores Python separados (`widgets/`), runtime compartilhado e worker de métricas. | Métricas preservam unidades; indisponibilidade de ferramenta produz estado compreensível; timeout/cancelamento impedem processos órfãos e respostas antigas na UI. |
| RO-03 | Agenda GTK 3 e tarefas locais (`extension/planner/calendar-app.py`, `store.py`). | Agenda abre em Tarefas; criar, editar, concluir e reabrir preserva descrição, data, horário e lembrete; falha externa não remove tarefas. |
| RO-04 | Timesheets por empresa (`timesheet.py`, `timesheet_ui.py`). | Criar/reordenar/renomear, registrar horas e cronômetro preservam histórico; virada de dia divide registros; sobreposição exige revisão; arquivadas não editam; exclusão exige arquivo e confirmação. |
| RO-05 | Exportação CSV e vínculo tarefa/horas (`timesheet.py`, `store.py`). | CSV por período tem BOM UTF-8, separador ponto e vírgula e texto protegido contra fórmulas; mesma tarefa não duplica registro na mesma timesheet, permitindo outra empresa. |
| RO-06 | iCloud CalDAV e assinaturas ICS (`apple_client.py`, `ics_client.py`, `external_store.py`, `external_ui.py`). | Consultas preservam cache em falha; senha fica no Secret Service; desconectar fonte mantém tarefas/horas; importação de evento exige revisão e evita duplicidade; sem escrita no provedor. |
| RO-07 | Lembretes no Shell (`calendar.js`, `reminders.js`). README delimita cache e ciclo de vida. | Com agenda fechada e extensão ativa, tarefas e eventos em cache alertam sem anúncio duplicado; eventos de dia inteiro não alertam; bloqueio da tela impede anúncio; desativar extensão encerra serviço. |
| RO-08 | Agenda JSON com lock, replace atômico, fsync e retenção de 60 snapshots (`store.py`); estado UI separado (`ui_state.py`). | Gravações concorrentes não perdem histórico; restauração confere prévia e preserva estado anterior; retenção não invalida salvamento; rascunhos sobrevivem à reabertura. |
| RO-09 | Sticky Notes GTK/SQLite WAL (`sticky-notes/storage.py`, `postits.py`); backup diário com retenção de 14 cópias no código. | Notas e propriedades persistem; conflito de revisão não sobrescreve silenciosamente; backup é recuperável; controle das notas não altera dados da agenda. |
| RO-10 | YouTube GTK/WebKit e lançadores (`extension/youtube-widget/`, `notes-widget/`, `extension.js`). | Player local permanece restrito a loopback/token; consultas usam chave local; lançadores informam dependência ausente sem expor segredos. |
| RO-11 | Compatibilidade declarada GNOME 42/43/44 (`metadata.json`), APIs legadas e backend X11 nos lançadores GTK. | Matriz por versão e sessão registra ambiente e evidências antes de afirmar suporte validado; não ampliar suporte por simples alteração do manifesto. |

## Limites e dúvidas abertas

- O README/stack descrevem a instalação local histórica; a inspeção do repositório não reconfirma o estado atual de GSettings, cofre, aplicativos ou sessão gráfica.
- Qual ambiente será alvo obrigatório da primeira instalação reproduzível? Ubuntu 22.04/GNOME 42.9 é contexto registrado, não uma nova matriz de suporte aprovada.
- Qual política de distribuição, atualização e rollback será adotada? Qual destino único dos coletores? Pendentes de decisão após proposta técnica.
- O inventário de testes da agenda em diretórios externos precisa ser consolidado antes de alegar cobertura completa.
- Requisitos de experiência, desempenho e acessibilidade ainda não possuem metas aprovadas. Os critérios acima são uma base de regressão, não especificação exaustiva de todos os painéis.

## Baseline de testes

Evidência histórica fornecida pelo contrato e README para a publicação de `2a24e0d`: **44 testes Python aprovados; 12/15 testes JavaScript aprovados**, com falhas em `test_storage_ui.js`, `test_stats_storage_click.js` e `test_widget_controller.js`. Não houve reexecução da suíte nem teste gráfico nesta missão. Ver próximos trabalhos em [backlog](backlog.md).

## RC-05 — Equipe e refatoração (18/10/2026)

Confirmado pelo usuário: supervisor de requisitos/documentação; agentes backend, frontend e auditor; desenvolvimento simultâneo com propriedade de arquivos e coordenação conforme `agents/team.md`. Toda entrega é reportada ao supervisor, documentada e auditada. Primeira tarefa RF-01: revisão estrutural de todo código próprio, preservando comportamento, com critérios no contrato da equipe.

## RC-06 — Contexto persistente e pesquisa centralizados (18/10/2026)

Confirmado pelo usuário: analista centraliza contexto e pesquisa do projeto; especialistas recebem informação direcionada e reportam mudanças/lacunas. Implementado nos contratos e no índice `docs/project-context.md`. Critério: cada tarefa aponta arquivos, contratos, aceite e evidências; cada entrega atualiza referências afetadas. Leitura local necessária e auditoria independente não são dispensadas; conhecimento completo de cada linha não foi comprovado.

## RC-07 — Design/UX e qualidade das entregas (18/10/2026)

Confirmado pelo usuário: Design/UX atua somente com frontend, que se reporta diretamente a ele para consistência visual e usabilidade e mantém o analista informado sobre código. Cobertura: alinhamento, margin/padding, cores, tipografia, foco/sobreposição, dimensões, estados e transições. Critérios: padrões existentes inventariados, achados com cenário/evidência e aceite, limitações visuais explícitas, alterações implementadas por frontend e reportadas ao analista. Recomendações de entregas pequenas, contratos claros, responsável por arquivo, evidências de conclusão e desempenho medido passam a práticas confirmadas em `agents/team.md`.

## RC-08 — Autonomia e colaboração ágil (18/10/2026)

Confirmado pelo usuário: adotar todas as recomendações sobre responsabilidades, independência necessária, colaboração e redução de gargalos. Aceite do processo: tarefa com área/contratos definidos; decisões técnicas locais sem aprovação rotineira; investigação pertinente permitida com relato ao analista; achados críticos encaminhados imediatamente aos responsáveis; entrega com relatório curto e validações funcional, visual e de segurança separadas. Política operacional em `agents/team.md`; UX preserva parceria exclusiva com frontend. Registro documental não comprova execução bem-sucedida do processo nem conclusão da RF-01.

## Errata da baseline e evidências RF-01 (18/10/2026)

Auditor reconciliou o inventário: a execução inicial tinha **14 arquivos JS, 11 aprovados e três falhas**; o resumo 12/15 reproduzido acima era incorreto. Esse texto histórico não comprova execução adicional. Auditor informou suíte integrada com **62 testes Python e 16 arquivos JS aprovados**; relatório final de revisão ainda pendente neste registro. UX confirmou equivalência estática dos corpos extraídos, sem aprovação visual.

## Aceite RF-01 por dimensão (18/10/2026)

Evidência independente: `audits/2026-10-18-integrated-audit.md`. Funcional local/estrutural aprovado no escopo dos 62 testes Python, 16 arquivos JS, 102 sintaxes, importações e comparações documentadas. Segurança/integridade: nenhuma regressão impeditiva reproduzida nas fronteiras revisadas, sem certificação integral. Visual/interação: pendente por ambiente isolado Broadway bloqueado; não há execução completa GNOME/GTK/WebKit. Desempenho: não medido. Supervisor aceita essas evidências delimitadas e mantém RF-01 sem conclusão integral até a validação visual requerida.

## RC-09 — Atualização local reversível (18/10/2026)

Confirmado pelo usuário: aplicar versão refatorada localmente, avisando quando pronta para reinício/teste manual; não reiniciar ou recarregar GNOME automaticamente. Aceite: backup de código/configuração e rollback, módulos completos com hashes conferidos, comandos dos coletores apontando fontes novas, preservação de dados/cofre/histórico, resultado explícito da aplicação. Bloqueio atual: destinos `~/.local/share` somente leitura pelo sandbox; plano preparado não equivale a instalação aplicada.

## RC-10 — Prontidão e aviso de reinício para teste (18/10/2026)

Confirmado pelo usuário: supervisor verifica testabilidade ao término de cada atualização e informa quando reiniciar a sessão para conferir funcionamento. Aceite: aplicação/versão instalada confirmadas, verificações e impedimentos explícitos, indicação de reinício/reabertura necessária e roteiro curto dos fluxos afetados. Estado final distingue pronta, instalada sem necessidade de reinício de sessão e não pronta. Não equivale a garantir ausência de bugs; resultado manual é registrado após execução. Sem reinício automático.

## RC-11 — Preservar contratos da instalação histórica na atualização

Requisito decorrente do escopo de preservação e confirmado pelo fluxo documentado de CPU/RAM/SSD. Teste manual do usuário revelou BUG-01: comparação somente com HEAD não cobre divergências entre fontes e scripts históricos efetivamente configurados. Critérios de correção: comandos CPU/RAM/armazenamento devem produzir protocolos esperados pelo frontend e clique RAM abrir painel; comparar contratos históricos relevantes antes de nova migração, sem copiar indiscriminadamente diferenças ou dados pessoais.

## RC-12 — Restaurar e manter padrão visual histórico do resumo Hardware

Confirmado pelo usuário em 18/10/2026 a partir da captura `codex-clipboard-70ecc3a9-9222-46a2-a3f5-181d2bc981d2.png`: restaurar tamanhos/espacamentos anteriores, sem redesign. Evidência primária: coletor histórico `2026-10-08/quan/outputs/cpu-ram-widget.py` e GSettings pré-atualização confrontados com os atuais.

| Item | Padrão confirmado / aceite |
|---|---|
| Fonte do resumo CPU/RAM/SSD | Monospace via markup, size=7680 unidades Pango (7,5 pt); não confundir com pixels físicos ou mudar escala global. |
| Barras | Oito células totais; preenchimento arredondado percent×8/100, limitado entre 0 e 8. |
| Entrelinha | line_height=1.5 no span; sem linhas vazias/intercaladas nem newline inicial/final dentro do resumo. |
| Colunas | Rótulo com largura fixa de quatro caracteres, alinhamento do prefixo e espaços históricos; percentual com largura três e %. |
| Padding e margens | Preservar configuração existente: esquerda/direita 20; topo/baixo 0; margens 0. Configuração antes/agora já igual. |
| Alinhamento/configuração | Text_Size=8, fonte custom desativada, X Start/Y Center/Line Center preservados; markup define tamanho efetivo do resumo. |

Não alterar algoritmos de métricas, cálculo/cache SSD, agregação de dispositivos ou layout dos demais widgets neste reparo visual. Padrões de cores/alertas e dispositivos divergentes permanecem registrados separadamente; não introduzir nova paleta. Critérios automatizados de markup/barra/linhas/colunas e revisão UX complementam, sem substituir, comparação visual após atualização. Falha de clique RAM permanece aberta e não é presumida corrigida por alteração estética.

## RC-13 — Identidade própria Orbitz (18/10/2026)

Confirmado pelo usuário: apresentar Orbitz como projeto próprio atribuído a Felipe Santiago/orbitzone e apontar identificador/links ao seu GitHub, preservando referências anteriores com menor destaque. Escolhas técnicas do supervisor: nome Orbitz Widgets for GNOME, UUID orbitz-widgets@orbitzone.github.io, URL https://github.com/orbitzone/orbitz-widgets-for-gnome, schema org.gnome.shell.extensions.orbitz-widgets e caminho /org/gnome/shell/extensions/orbitz-widgets/. Versão própria inicia1; não representa novo aceite funcional.

Aceite: metadados/UI principal Orbitz/autor/GitHub; referências upstream concentradas em créditos e origem; nenhuma conta de doação herdada apresentada como conta Orbitz; licenças/atribuições preservadas. Novo schema com os mesmos tipos/valores e migração reversível sem perda de aparência/comandos/dados; legado permanece preservado para rollback; não ativar duas identidades simultaneamente. Gettext-domain azclock mantido por compatibilidade de catálogo, sem renomeação gratuita de classes internas. Código e ferramentas novos testados/auditados antes de recomendar aplicação. Alteração instalada/ativação só confirmadas por evidência, sem recarga/reinício automático pelo agente. BUG RAM/EXT/validação visual não resolvidos por rebranding.

RC-13 — critério adicional de compatibilidade: GTypes da nova identidade não podem colidir com tipos persistentes do legado no mesmo processo. Vinte nomes explícitos OrbitzWidgets e teste GJS representativo de coexistência implementados; não equivale a executar ambos conjuntos de widgets. Preparação continua separada da ativação e somente uma extensão deve ficar ativa.

RC-13 — evidências locais: metadados/UI/schema equivalentes em chaves/defaults,20 GTypes únicos e migração tipada/preparo/rollback testados e auditados. Suíte integrada83 testes Python/18 arquivos Node/2 testes GJS/110 verificações de sintaxe; ajuste posterior rollback reverificado11/11 sem novo resultado global. Aceite local do supervisor; migrador apto no escopo auditado, sem afirmar implantação ou ativação real. Permanecem critérios operacionais: conferir preparo/hashes, descoberta/ativação manual exclusiva, preservação percebida de configuração e aparência na sessão real.

## RC-14 — Logo própria e versão de apresentação 1.0

Confirmado pelo usuário em 18/10/2026: substituir a logo de origem por identidade visual própria Orbitz e apresentar versão 1.0 na página Sobre, com nome/descrição/autor/GitHub próprios. A captura fornecida mostra Desktop Clock7/GitLab/PayPal; supervisor confrontou instalações e confirmou que About do UUID Orbitz coincide com a fonte já própria, enquanto a captura corresponde à página legada. Não concluir que a nova extensão ativa foi revertida; fechar janelas antigas e abrir preferências explicitamente pelo UUID novo faz parte da validação.

Aceite: logo SVG original do projeto em `extension/media/orbitz-logo.svg`, sem relógio/logo azclock, renderizável e identificável em tema claro/escuro; carregamento por arquivo no caminho da identidade nova, sem depender de nome de ícone legado/cache; espaço100px/margem5 preservados. Metadata version permanece inteiro 1; version-name=1.0 e About exibindo1.0 mesmo com cache de metadata inteiro 1. Nome/descrição/GitHub/autor próprios, atribuições/licença preservadas em grupo discreto. Atualizador deve copiar/validar/rollback logo e metadata sem incluir JSON pessoal nem aceitar UUID/schema incompatíveis. Testes/auditoria e nova conferência instalada antes de orientar teste. Apenas reabrir preferências deve bastar; sessão GNOME não deve ser reiniciada sem necessidade demonstrada.

RC-14 — evidências: integração estática SVG/FileIcon/versão 1.0/fallback, preservação atribuições/LICENSE e whitelist/backup/rollback passaram na revisão dirigida BRAND-01. ParserSVG rejeita conteúdo ativo/externo no asset atual. Validação visual do asset100px favorável por UX, com renderização librsvg; janela GTK completa e aplicação real pendentes. Não chamar preview de instalação ou certificação de acessibilidade.

## RC-15 — Menu da agenda e invoice PDF bilíngue

Confirmado pelo usuário: mover Timesheets arquivadas e Restaurar backup do rodapé para menu dropdown no topo direito, na mesma linha da data, e incluir geração de invoice. O usuário escolhe timesheet e valor/hora; documento calcula horas registradas × taxa e pode ser salvo em PDF. Campos editáveis persistentes: emitente (nome completo/empresa e CPF/CNPJ), cliente (nome, CPF/CNPJ e endereço fiscal), idioma Português/Inglês.

Critérios de aceite: menu conserva callbacks/confirmações e não perde status do rodapé; seleção de sheets ativas e arquivadas sem modificar histórico; horas em minutos inteiros dos registros concluídos, sem lixeira/cronômetro ativo; preview exibe período, horas, taxa, moeda e total antes da gravação. Escopo assumido explicitamente na UI: todo histórico por padrão, datas opcionais para restringir; moeda BRL inicial editável independente de idioma. Cálculo Decimal com arredondamento monetário só no total, evitando float e arredondar horas antes de multiplicar. Taxas inválidas/não finitas/negativas rejeitadas.

Persistência: dados emitente globais; cliente/taxa/moeda por ID da timesheet; idioma lembrado. Valores pessoais apenas no perfil privado local separado `invoice-profiles.json`, lock/gravação atômica e modo 0600, nunca logs/repo/fixtures reais. Campos voltam preenchidos até alteração explícita; cancelar não altera dados silenciosamente. Arquivo danificado deve ser preservado e erro comunicado.

PDF PT/EN apresenta referência/data/período, ambas partes e identificações, endereço fiscal cliente, descrição/quantidade de serviços, taxa/moeda e total; textos longos/acentos/paginação legíveis. Revisão/salvar como/confirmar sobrescrita; arquivo privado e gravação segura. Documento é Fatura/Service Invoice de serviços, não emissão eletrônica oficial integrada. Nenhuma taxa/imposto/integração fiscal foi solicitada ou implementada por inferência.

Verificações proporcionais com dados sintéticos: Decimal/limites/período/timer ativo/timesheets arquivadas, persistência isolada, cancelamento/formulário/menu, textos PDF PT/EN/markup/endereço longo/paginação, renderização e inspeção visual; auditoria independente antes de aplicar. ReportLab 3.6.8 disponível em Python do sistema, dependência runtime a documentar; versão instalada/abertura da agenda devem ser conferidas antes de informar prontidão de teste.

Identificações aceitam CPF numérico e CNPJ numérico ou alfanumérico, com ou sem pontuação completa, sem consulta cadastral. Formato alfanumérico: primeiras 12 posições A–Z/0–9, duas últimas numéricas; fonte: [Receita Federal — CNPJ alfanumérico](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cnpj-alfanumerico), consultada em 18/10/2026.

RC-15 — evidências locais: 11 testes backend e seis frontend (17 novos), mais oito regressões planner aprovados por auditoria dirigida. Sessão→PDF real e round-trip privado PT/EN testados; supervisor inspecionou quatro páginas renderizadas sem corte/sobreposição nas amostras. UX revisou estrutura e correções de largura/atalhos/foco/prévia sem impedimento estático remanescente. Não equivale a execução GTK/AT/chooser nativo real ou aplicação local. Atualização exige seis arquivos Python e nenhuma migração de comando neste alvo; fechar/reabrir agenda após aplicar, sem reiniciar sessão GNOME.

## RC-16 — Seleção visual do período da invoice (19/10/2026)

Confirmado pelo usuário: substituir a opção única de histórico e os dois campos digitados por três opções: Período de 1 mês, Todo o histórico e Período específico. Um único calendário permite escolher o intervalo sem digitar início e fim.

Critérios: mês civil escolhido inclui primeiro ao último dia, respeitando anos bissextos; histórico continua sem restrição; intervalo específico inclusivo selecionado por dois cliques, início e fim, com navegação entre meses/anos. Mostrar resumo legível das datas, destaque do trecho visível e instrução do próximo clique; permitir limpar/recomeçar. Navegar não conta como selecionar extremo. Seleção incompleta impede prévia/exportação; mudanças efetivas do período invalidam a prévia anterior. Navegação e foco preservam a prévia quando modo/extremos/mês escolhido não mudam. Mesma data nos dois cliques representa um dia; ordem invertida é normalizada e mostrada claramente. Default histórico preserva o comportamento anterior; mês inicial corresponde ao dia selecionado na agenda. Sem mudança no cálculo Decimal, registros ou perfis.

Estado: implementação frontend/UX em andamento; auditoria e teste GTK real são etapas distintas. Nenhuma atualização instalada por inferência.

INV-02 — resultado consolidado em 19/10/2026: auditoria dirigida aprovou 27 testes (10 de período e 17 regressões invoice), três sintaxes e diff-check, sem impeditivo reproduzido. Supervisor conferiu os três hashes do alvo. Relatório `docs/audits/2026-10-19-invoice-period-audit.md`; revisão UX em `docs/design/2026-10-19-invoice-period-review.md`, achado de invalidação tratado. Funcional local validado; visual/teclado/AT GTK real pendentes. Plano de dois arquivos/zero comandos, aplicação ainda necessária; encerrar/reabrir agenda, sem logout GNOME.

## RC-17 — Conclusão explícita com comando de atualização

19/10/2026, confirmado pelo usuário: adicionar como responsabilidade do supervisor informar a conclusão das tarefas e fornecer o comando completo de atualização. Aceite: resposta final contém resultado, verificações/limites, instalação confirmada ou pendente, comando copiável quando aplicável, resultado esperado e orientação de reabertura/reinício/teste. Documentação apenas: declarar que não exige aplicação nem reinício. Registrado nos contratos project-owner/team e no contexto persistente.

## RC-18 — Histórico local de invoices (19/10/2026)

Confirmado pelo usuário: adicionar Histórico de invoices ao menu de ações, permitindo consultar, baixar e excluir PDFs organizados por empresa/cliente e mês/ano. Decisões operacionais: empresa corresponde à timesheet; agrupamento mensal usa a data de emissão, identificada na interface, e detalhes preservam o período dos serviços. Clientes homônimos devem permanecer distintos pela identidade registrada.

Aceite: cada nova exportação bem-sucedida guarda cópia exata privada do PDF e metadados da emissão, sem depender de mudanças futuras em perfis/timesheets ou da existência do arquivo externo. Múltiplas invoices por cliente/mês não se sobrescrevem. Armazenamento separado em `~/.local/share/orbitz-widgets/invoices` (respeitando XDG), diretórios privados e arquivos 0600, IDs internos seguros, sem nomes/CPF em caminhos. Nenhum varrimento ou importação automática de PDFs antigos.

Histórico mostra agrupamentos e itens consultáveis com referência, emissão, período, horas, valor/moeda e idioma. Abrir consulta usa arquivo local; baixar significa salvar uma cópia em destino escolhido, com confirmação para substituir. Excluir exige confirmação clara e remove somente registro/cópia gerenciada, nunca arquivo exportado externo, horas, perfis, tarefas ou credenciais. Cancelamentos não alteram dados; ações de folha desabilitadas sem invoice selecionada.

Falhas de arquivamento após exportação são apresentadas como sucesso parcial (PDF externo salvo, histórico não registrado), sem sucesso falso ou perda do original. Atomicidade, concorrência, integridade/corrupção, symlinks/traversal e falhas de escrita/exclusão recebem verificações proporcionais sintéticas. Erros de um registro não devem apagar os demais. Validação funcional/estrutural e revisão de segurança são distintas de GTK real. Sem alteração de renderer, cálculo, impostos ou licença.

RC-18 — fronteira adicional de integridade: destinos da nova emissão e de downloads não podem apontar para dentro do acervo gerenciado, inclusive via caminho vinculado. Rejeitar antes do writer, preservando PDF/metadados anteriores. Critério derivado da preservação de emissões; caso adverso IH-A02 reproduzido com fixtures temporárias, em correção antes do aceite.

INV-03 — conclusão local em 19/10/2026: auditoria independente aprovou 47 testes de invoices (incluindo 11 histórico backend e nove histórico frontend), seis sintaxes e diff-check. IH-A01/IH-A02 resolvidos e reverificados; nenhum impeditivo remanescente no escopo. Supervisor conferiu os seis hashes finais. Relatório `docs/audits/2026-10-19-invoice-history-audit.md`; revisão UX estática separada. Funcional local e integridade aprovados; GTK/AT/chooser/confirmações reais pendentes. Listagem metadata/stat e hash nas ações, sem benchmark. Plano de quatro arquivos/zero comandos, ainda precisa aplicação local. Após ATUALIZACAO_OK, encerrar/reabrir agenda, sem logout; testar gerar uma invoice sintética, consultar/salvar cópia/cancelar exclusão e excluir somente registro de teste. PDFs antigos não importados automaticamente. Nenhuma instalação, commit ou push executado nesta etapa.

## RC-19 — Assinatura assistida gov.br e versões importadas (19/10/2026)

Usuário aprovou o fluxo explicado: disponibilizar cópia da invoice, abrir portal oficial para login/upload/assinatura/download manuais, adicionar PDF retornado ao histórico e oferecer acesso ao VALIDAR. É fluxo assistido; não integrar API restrita a órgãos públicos nem coletar credenciais, automatizar login ou enviar documentos em segundo plano. Fontes verificadas na consulta anterior: [regras de integração GOV.BR](https://www.gov.br/governodigital/pt-br/identidade/identidade-digital-para-gestores-publicos/duvidas-frequentes-do-ecossistema-da-identidade-digital-gov-br/) e [serviço de assinatura](https://www.gov.br/pt-br/servicos/assinatura-eletronica).

Aceite: ação Assinar com gov.br salva cópia em destino escolhido e, somente após sucesso, abre URL fixa https://assinador.iti.br/ no navegador por ação explícita. Cancelar não exporta nem abre portal. Instruções indicam conta prata/ouro e etapas manuais. Falha ao abrir navegador após cópia salva deve distinguir os dois resultados. Nenhuma senha/token/cookie guardado pelo aplicativo.

Adicionar versão assinada exige selecionar PDF e confirmar vínculo à invoice identificada; guardar bytes exatos em armazenamento privado, com ID de versão, data de importação, tamanho/hash e referência à invoice/hash original. Preservar original e outras versões, permitir múltiplas versões, consulta/download por versão sem regenerar o PDF. Compatibilidade com registros existentes; erro de uma versão isolado sem esconder o original. Arquivo gerenciado não pode ser usado como destino de exportação/cópia, nem importado como se fosse documento externo.

Estado obrigatório: versão importada, validação pendente. Extensão, nome do arquivo, confirmação do usuário, hash ou abertura de portal não comprovam presença/validade da assinatura nem correspondência criptográfica com conteúdo da invoice. Não há motor de validação criptográfica nesta etapa. Ação Verificar no VALIDAR abre somente URL fixa https://validar.iti.gov.br/; upload/verificação são feitos pelo usuário no portal, sem alterar automaticamente o estado para validado.

Excluir invoice deve confirmar alcance original+versões gerenciadas e preservar arquivos externos/horas/perfis. Se houver exclusão de versão individual, confirmar claramente e preservar original/demais versões. Guardas de caminhos/links, privacidade 0700/0600, atomicidade, concorrência, corrupção isolada e cancelamentos recebem testes sintéticos temporários; não abrir URLs reais, alterar instalação ou testar com documentos pessoais. Cálculo/renderer/perfis preservados; assinatura não representa emissão NFS-e.

INV-04 — conclusão local em 19/10/2026: auditoria independente aprovou 62 testes de invoices (15 novos), seis sintaxes e diff-check, sem impeditivo reproduzido. Supervisor conferiu seis hashes finais; relatório `docs/audits/2026-10-19-invoice-signatures-audit.md`. Original v1 e versões privadas preservados, cancelamentos/URLs fixas/vínculos e estado pendente verificados com dados temporários. Não houve assinatura, validação criptográfica, acesso real a portais/contas ou dados pessoais. GTK/AT/browser real e ações manuais nos serviços permanecem pendentes. Plano quatro arquivos/zero comandos; aplicação ainda necessária, seguida de fechar/reabrir agenda, sem logout. Teste manual: histórico→selecionar invoice→Assinar com gov.br→salvar cópia/portal; depois importar PDF escolhido com confirmação e consultar Original e versões/VALIDAR. Estado importado permanece pendente. Nenhuma instalação, commit ou push executado nesta entrega.

## RC-20 — Redução de consumo no fluxo dos agentes (19/10/2026)

Pedido confirmado: reduzir consumo de tokens, agrupar auditoria por sprint e reduzir recursos de Design/UX. Política operacional em `docs/agents/workflow.md`; fila em `docs/sprint-backlog.md`. Testes afetados continuam com o desenvolvedor, auditoria média é consolidada no fechamento, alto risco recebe revisão focada antes da operação e UX deixa de ser gate automático. Briefs/relatórios curtos, evidência reutilizada, contexto atual compacto e histórico sob demanda. Não representa mudança de modelo/plano ou promessa de economia medida. Alteração apenas documental; sem instalação/reinício ou acionamento de especialistas para revisá-la.

## RC-21 — Orbitz Workspace e contexto de faturamento (19/10/2026)

Confirmado: usuário aprovou as recomendações de nome/navegação/Hoje/contexto/duplicidade/backup e estados independentes, acrescentando que timesheet não pode ser identificada apenas por “Empresa”. Nome escolhido pela proposta aceita: Orbitz Workspace, subtítulo Agenda, tarefas, horas e faturamento. Áreas: Hoje, Agenda, Tarefas, Horas e Invoices; menu concentra ações administrativas.

Timesheet tem nome identificador obrigatório e contexto opcional separado: cliente/contratante, contrato/projeto, departamento/centro de custo. Criar/editar sem perder horas, timer, IDs, rascunhos ou arquivos antigos. Timesheets legadas sem novos campos continuam válidas. Destinatário fiscal (nome/CPF-CNPJ/endereço) continua no perfil da invoice; contrato/departamento não substituem pessoa/empresa destinatária. Cliente do contexto pode pré-preencher somente perfil ainda vazio; nunca sobrescrever dados fiscais guardados. Referências de contexto aparecem na prévia e PDF PT/EN, com compatibilidade dos documentos históricos imutáveis.

Hoje reúne compromissos do dia, tarefas pendentes/atrasadas e cronômetro ativo, sem escrever em calendários externos. Contexto e período selecionados ficam explícitos. Possível faturamento duplicado gera aviso e confirmação de reemissão intencional, sem bloquear correções ou marcar horas automaticamente. Estado manual de pagamento fica separado de original/versão importada/validação pendente e não altera bytes emitidos.

Backup completo deste aplicativo inclui tarefas/horas, perfis, invoices/versões e estado UI pertinente; não significa backup do sistema, cofre/credenciais, calendários externos ou Sticky Notes SQLite. Exportação privada, manifesto/verificação de integridade, limites de tamanho/tipos/caminhos e restauração confirmada com cópia de segurança e rollback. Falhas preservam dados existentes e não tocam arquivos fora da lista permitida; nenhuma restauração real em desenvolvimento.

Testes proporcionais com fixtures temporárias, PDF QA sintético e auditoria única do lote estável antes de aplicar operações de alto risco. Prioridades/lotes em docs/sprint-backlog.md. Implementação não equivale a instalação, GUI ou restauração real validadas.

Evidência RC-21: implementação nas fontes e auditoria integrada concluídas, 169/169 testes Python aprovados, restauração em dados temporários e PDF PT/EN conferidos. Parecer: [WSP-01](audits/2026-10-19-workspace-audit.md). Instalação e interação GTK real pendentes; não houve aplicação em dados pessoais.

## RC-22 — Google Calendar, Calendly e identidade About (19/10/2026)

Confirmado: incluir as duas integrações e investigar a janela About que mostra Desktop Clock7/logo original. Escopo técnico inicial: consultar calendários/eventos e converter evento em tarefa somente por ação explícita; não criar/editar/excluir eventos remotos. Preservar iCloud/ICS, cache anterior em falhas, tarefas/horas e backups independentes.

Google: OAuth desktop pelo navegador, callback loopback local, state e PKCE, escopos somente leitura, configuração de cliente OAuth fornecida pelo usuário. Calendly: API oficial com token pessoal para esta instalação privada; eventos agendados e cancelamentos, paginação limitada e fuso explícito. Tokens/refresh apenas no Secret Service, nunca no repositório, logs, cache ou backup. Cancelar/desconectar deve limpar a conexão/segredos pertinentes sem apagar tarefas. Autenticação real depende das credenciais e consentimento do usuário, não equivale a validação por mocks.

About deve apresentar logo Orbitz existente, título Orbitz Widgets for GNOME, versão1.0 e GitHub próprio, mantendo créditos/licenças. Fonte atual já contém a marca correta: captura confirma execução antiga, mas não identifica sozinha a causa. Investigar UUID, instalação/launcher/cache sem alterar a instalação legada preservada nem a sessão por inferência. Revisão focada de credenciais no alvo estável antes da aplicação; GUI e contas reais separados.

Evidência RC-22: clientes/UI implementados e [revisão focada CAL-01](audits/2026-10-19-calendar-audit.md) concluída sem impeditivos locais.35 testes direcionados aprovados,2skips ambientais; identidade fonte e integração temporária aprovadas. Segredos excluídos do backup, tarefas/horas preservadas na desconexão. Instalação, loopback real, cofre e contas reais/GTK continuam pendentes. About legado identificado por artefato, gatilho exato não provado; abrir UUIDOrbitz explicitamente, sem alterar legado.

## RC-23 — README público orientado ao usuário (19/10/2026)

Confirmado pelo usuário: README exclusivo para apresentar o sistema com linguagem fluida e comercial, sem referências ao Codex, coordenação interna, contagens de testes ou caminhos pessoais. Preservar funcionalidades relevantes, compatibilidade, requisitos de adoção, limites conhecidos, privacidade/backup e créditos. Contexto técnico necessário vai para documento separado. Implementado em README.md; índice em docs/maintenance.md e snapshot histórico em docs/archive/2026-10-19-readme-internal.md. Aceite documental: ausência do termo e de seções internas no README, links locais válidos e nenhuma promessa de instalador/contas reais validados. Sem alteração funcional/instalação.

Responsabilidade RC-23 confirmada pelo usuário: a instrução foi encaminhada acidentalmente ao auditor; o analista de requisitos/supervisor assume permanentemente a manutenção editorial do README. Revisão desta entrega preservou a apresentação pública já produzida e registrou a regra em AGENTS e contratos da equipe. Auditor reporta achados; supervisor atualiza documentação de produto.
