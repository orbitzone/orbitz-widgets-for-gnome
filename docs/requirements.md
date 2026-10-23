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

## WX-01 — Modal de previsão do tempo (22/10/2026)

Pedido confirmado pelo usuário. A correção deve traduzir o rótulo de umidade para o idioma ativo (PT-BR/EN-US) no resumo atual. Ao clicar no widget de clima, abrir uma modal com a previsão para sete dias em sete colunas e escolha Celsius/Fahrenheit. Em 22/10, o usuário substituiu a seleção em cascata por um único campo de pesquisa, botão Pesquisar e resultados selecionáveis identificados como Cidade · Região · País; ex.: “Brasília, Distrito Federal, Brazil”. Alterar local atualiza o resumo e os detalhes; unidade e local selecionados persistem entre aberturas/reinicializações.

Critérios verificáveis: manter compatibilidade do resumo atual; tradução de “Umidade” cobre os dois idiomas; modal abre pela ativação do widget; apresenta exatamente sete datas consecutivas em sete colunas de mesma largura, ajustadas à área interna sem barra de rolagem horizontal; cada dia tem ícone distinto para condição predominante (céu limpo, nuvens, nevoeiro, garoa, chuva, neve, tempestade e vento forte); vento forte usa velocidade máxima diária ≥40 km/h e não substitui o ícone de tempestade; alternar °C/°F atualiza previsão e resumo imediatamente e persiste; consulta de 2 a 100 caracteres retorna até dez matches ordenados pelo serviço, com cidade/região/país, sem afirmar completude; selecionar um resultado grava local/CAS e atualiza a modal e o resumo; pesquisa vazia/curta, sem resultados e falha de rede têm feedback; respostas antigas e botões de resultados obsoletos não substituem seleção mais recente; previsão usa cache e não consulta continuamente; atribuição Open-Meteo e GeoNames permanece visível. A adoção da API de geocodificação substitui o catálogo CSC no fluxo da interface; a API é uma busca limitada, não um diretório completo.

Estado: implementação de fonte atualizada em 22/10. Busca única substituiu a cascata; após confirmação da gravação C/F, o resumo do desktop é atualizado sem esperar pelo próximo polling. A modal exibe sete colunas sem rolagem horizontal, ícones por código WMO e ícone de vento a partir de 40 km/h; o backend valida e guarda a velocidade diária em km/h e usa namespace de cache novo. Testes dirigidos WX: 24 Python, painel Node com viewports 740/1034 px e 36 scripts Node passaram. A consulta online real, instalação e validação visual GNOME seguem pendentes. Suíte Python consolidada após as correções: 428 passaram, 4 skips ambientais, sem falhas.

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

Não alterar algoritmos de métricas, cálculo/cache SSD, agregação de dispositivos ou layout dos demais widgets neste reparo visual. Padrões de cores/alertas e dispositivos divergentes permanecem registrados separadamente; não introduzir nova paleta. Critérios automatizados de markup/barra/linhas/colunas e revisão UX complementam, sem substituir, comparação visual após atualização. Na data desta decisão, a falha de clique RAM permanecia aberta; consulte a atualização de estado abaixo.

Estado atualizado em 20/10/2026: o usuário informou que o clique da RAM não é mais um problema. BUG-01 fica encerrado por confirmação manual; isso não amplia a validação para outros hardwares ou versões.

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

## RC-24 — Conexão Google guiada e estados claros (19/10/2026)

Usuário reportou que o diálogo não explica o necessário para concluir a conexão. Substituir instrução genérica por passos acionáveis: preparo do projeto Google/Calendar API/consentimento/cliente Desktop, links oficiais e download do JSON; seleção identificada por texto claro em vez de “None”; nome sugerido editável; validação local do arquivo com retorno imediato e botão de autorização condicionado aos dados válidos. Explicar que o navegador abre após essa etapa e que a configuração própria ainda é necessária nesta versão. Sem mudar endpoints/scopes, cofre, credenciais ou protocolos já auditados. Não expor conteúdo do JSON nos erros. Cancelamento/ACK e Calendly devem manter comportamento. Verificação proporcional de UI e validação; auditoria média agrupada no fechamento, sem nova rodada automática de segurança/UX. GTK real e autorização continuam separados.

Evidência RC-24: diálogo guiado implementado, nove testes frontend aprovados; preparo/seleção JSON, validação local, mensagens e botão condicionado aos dados. Aparência GTK e contas reais não foram validadas nesta mudança. Plano:1arquivo/0comandos; aplicação pendente.

## RC-25 — Entrar com Google usando o cliente público do Orbitz (19/10/2026)

Usuário rejeitou configuração de desenvolvedor na interface e forneceu o Client ID público próprio. Fluxo normal: Entrar com Google → navegador/seleção da conta → consentimento de leitura → seleção do calendário. Remover seleção de JSON e instruções Cloud do diálogo normal; preparo/consentimento/verificação pública são responsabilidade do mantenedor, documentados fora da UI. Configuração pública embarcada não inclui tokens, chaves administrativas ou segredo inventado. Manter state/PKCE/loopback/hosts/scopes/cofre/cancelamento e conexões existentes. Cliente legado customizado pode continuar compatível internamente. Substitui a exigência pública de importação de RC-22/24; evidências históricas não equivalem ao novo fluxo. Autenticação real/consentimento/cliente Desktop precisam teste humano.

Evidência RC-25: fluxo padrão semJSON implementado com ClientID público fornecido; [auditoria focada](audits/2026-10-19-google-login-audit.md) concluída,30 testes aprovados/2skips ambientais e4hashes conferidos. Instalação e autorização real pendentes; somente ID não comprova configuração/aceitação pelo Google.

## RC-26 — Conclusão e diagnóstico da conexão Google (19/10/2026)

Usuário reportou callback recebido no navegador e Orbitz ainda aguardando/botão inativo, sem erro. Retorno local não pode ser perdido por falha ao escrever a página de resposta: registrar código/negação somente após validação state/Host/path e antes de escrever, preservando recusa de callback inválido. Mostrar etapas fixas da conexão (aguardando, troca de autorização, consulta de calendários, cofre) sem segredos/dados da resposta; callbacks antigos não alteram tentativa nova. Erro/recusa deve reabilitar tentativa, cancelamento/ACK preservados. Erros do endpoint token podem identificar apenas códigos em allowlist com mensagens fixas, nunca error_description/corpo/URL/credenciais. Causa da tentativa real permanece não comprovada; testar cenário adverso com fixtures, revisão focada antes de aplicar alteração do callback.

Evidência RC-26: correção de callback reproduzida e revista;36 testes aprovados/2skips e8 casos adversos. [Parecer](audits/2026-10-19-google-callback-audit.md);6hashes finais conferidos. Progresso e erros seguros permitem investigar etapas; não declarar login real resolvido antes do reteste do usuário.

## RC-27 — Completar configuração do cliente Google do mantenedor (19/10/2026)

Observação real: instalação CAL-04 conferida atualizada/zero arquivos pendentes; erro genérico persistiu. Probe diagnóstico autorizado ao tokenendpoint oficial usou ClientID público+código fictício, sem autorização/token/conta real:HTTP400 invalid_request e motivo exato client_secret ausente. Identificador sozinho foi insuficiente para este cliente, apesar da descrição opcional da documentação. Não atribuir expiração ou reinstalação como solução comprovada.

Completar configuração local pelo mantenedor a partir do JSON Desktop fornecido pelo próprio Google, fora do chat/repositório, com leitura limitada/validada, permissões privadas e gravação atômica. ClientID deve corresponder ao Orbitz; não aceitar endpoint/token_uri arbitrário. Usuário final continua com Entrar com Google, sem importação na UI; setup local não equivale a distribuição pública pronta. Preservar grants/cofre/clientes legados; erros diagnósticos fixos sem valores/descrição remota. Uma revisão focada antes da configuração sensível/aplicação. JSON real/download/caminho e novo login dependem do mantenedor; não copiar segredo para documentação ou fixtures.

Evidência RC-27: [revisão focada](audits/2026-10-19-google-client-config-audit.md) sem impeditivo reproduzido,35 testes aprovados/2skips e6 adversos;6hashes conferidos. Supervisor validou o JSON Desktop indicado pelo mantenedor sem exibir valores, sondas sem grant real confirmaram remoção do erro de parâmetro ausente. Após permissão explícita de escrita fora do workspace, configuração privada preparada/check OK, arquivo0600/diretório0700/proprietário corretos. Nenhum token/grant alterado e nenhum segredo levado ao repositório/chat. Plano de instalação:2fontes/0comandos ainda pendentes; login real posterior continua pendente.

## RC-28 — Marcações explicadas na Agenda e ajuda da API (19/10/2026)

Usuário confirmou conexão Google funcionando após ativar a API no projeto. Validação manual inicial de login, não certificação de todos os casos/contas; Calendly não confirmado. Pede link da ativação e explicação dos dias marcados sem itens na Agenda.

Observado no código: marcação inclui feriados de todas as fontes e tarefas/horas locais; render de eventos lista apenas fonte selecionada. Data selecionada (laranja) não significa evento. Agenda deve mostrar motivos pertinentes ao dia: eventos da fonte, feriados conhecidos de outras fontes com nome/origem e resumo/rotas de tarefas pendentes/horas locais que produzem marcas. Evitar duplicidade para feriado já exibido na fonte ativa, distinguir feriado de compromisso pessoal e usar cache existente sem consulta ou importação implícita. Legenda/tooltip/acessibilidade coerentes; dia só selecionado sem atividade continua explicado como seleção.

Google mantém Entrar com Google; link fixo opcional para ativar Calendar API no projeto Orbitz com responsabilidade explícita do mantenedor, sem exigir Cloud/JSON de usuários comuns nem mudar autenticação. Testes proporcionais com fixtures e revisão média agrupada no fechamento; sem auditor/UX automáticos, instalação ou redes reais por inferência.

Evidência RC-28/CAL-06: projeções somente leitura em day_activity.py compartilhadas por calendário/Agenda; feriados externos com título/origem, resumos/rotas de tarefas/horas locais, seleção explicitada, legenda limitada à largura e link opcional de ativação adicionados.18 testes direcionados aprovados (7atividade/integração+11frontend), AST/diff check. Sem nova autenticação, leitura de acervo real ou mutação de dados. No fechamento da implementação, GUI/aplicação estavam pendentes; revisão média na fila de fechamento.

Validação manual registrada em 20/10/2026: usuário confirmou que Google Calendar funcionou na instalação atual. Confirmação restrita à conta/fluxo usados; Calendly e cobertura ampla de contas permanecem pendentes.

## RC-29 — Datas comemorativas padrão e reativáveis (19/10/2026)

Usuário confirmou que excluir a assinatura “Datas comemorativas” a removeu da lista e solicitou opção padrão permanente, desativável e reativável. A fonte pública brasileira continua ICS sem login Google. Gerenciar conexões deve manter a linha Brasil·Datas comemorativas sempre presente, com estado/Ativar/Desativar em vez de remoção definitiva. Instalações que já a excluíram devem recuperar o cadastro padrão ativo ao abrir; uma desativação explícita nova deve persistir, inclusive ao reabrir.

Adoção de assinatura legada com a mesma URL sem duplicar ID/cache nem alterar contas pessoais. Desativar preserva registro/cache, mas exclui fonte do seletor, consultas automáticas, marcações e conteúdo da Agenda; trabalhos pendentes não podem reativá-la. Reativar devolve fonte/atualização. Tarefas criadas e horas permanecem independentes, demais fontes mantêm desconexão normal. Cadastro/estado por operação explícita idempotente no aplicativo, sem reescrita automática em toda leitura genérica nem sobrescrever arquivo inválido. Fixtures e verificações proporcionais agora, revisão média no fechamento.

Evidência RC-29/CAL-07: fonte padrão restaurada/adotada por inicialização explícita idempotente; remove_account da fonte passa a desativar, mantendo cache; toggle estrito/persistido, cache tardio ignorado. Gerenciar sempre mostra opção padrão com Ativar/Desativar, fonte inativa fora da seleção/sync/Agenda/marcações e trabalhos enfileirados cancelados.31 testes direcionados aprovados (7persistência+16frontend+8atividade), regressão dirigida de dados externos aprovada, sintaxe/diff check limpos. Fonte padrão é de dia inteiro e já não gera alertas temporizados; não alterar JS de lembretes por hipótese. No fechamento da implementação, aplicação e GUI estavam pendentes; revisão média agrupada na fila.

Validação manual registrada em 20/10/2026: usuário confirmou que a fonte de Datas comemorativas funcionou na instalação atual. O ciclo persistente desativar→reabrir→reativar não foi explicitamente confirmado. Revisão média consolidada permanece na fila de fechamento.

## RC-30 — Widgets gêmeos de conversão BRL/moeda fiduciária e USD/cripto (20/10/2026)

**Escopo de interface supersedido em 21/10/2026 pelo RC-40:** o usuário decidiu unificar Fiat e Crypto em um único widget **Conversor de moedas**. Este registro preserva os requisitos originais de moedas, sentidos e fontes; não manter dois widgets separados.

Pedido confirmado: dois widgets gêmeos, com apresentação e interação consistentes. No fiat, escolher qualquer moeda fiduciária oferecida pela fonte pública confiável, mostrar BRL → moeda escolhida e permitir inverter para moeda → BRL. A moeda/direção selecionadas ficam fixas e persistem. No widget cripto, escolher Bitcoin ou outra criptomoeda coberta por uma fonte pública confiável, mostrar USD → ativo escolhido e permitir inverter para ativo → USD; o seletor deve permitir buscar/selecionar outras criptomoedas, não apenas BTC. Os limites de cobertura da fonte devem ser explícitos; não inventar moedas ou cobertura total.

Requisitos fiat confirmados: usar somente a cotação mais recente disponível no provedor, sem previsão, datas futuras, histórico ou cache antigo como atual. Atualizar a cada quatro horas (14.400.000 ms) e permitir refresh manual e inversão pela modal. O widget mostra somente par e valor, sem metadados. A regra corrigida em 21/10 usa duas casas arredondadas metade para cima (`0.19829 → 0,20`); valores Fiat abaixo de `0.005` aparecem `0,00`. Isso não se aplica a USD→ativo cripto, que preserva a precisão fornecida. Frankfurter publica referências diárias em dias úteis, não cotações em tempo real; em falha, não manter valor antigo como atual.

Critérios comuns: resultado e par de origem/destino corretos nos dois sentidos; seleção e direção persistem ao reabrir/reiniciar; catálogos carregam sem bloquear a interface; chamadas e estados de erro são delimitados e claros. Os dois widgets têm apresentação/controles gêmeos, mas podem usar fontes, cadência e regras de precisão diferentes conforme mercado/provedor. Não exigir chave compartilhada nem prometer preço transacional.

Implementação inicial (snapshot de 20/10): Fiat consultava Frankfurter latest; polling era 1h, depois ajustado para 4h. Esse registro dizia que Crypto e provedor ainda estavam pendentes; o modo Crypto, seleção e fonte CoinPaprika foram implementados no RC-40 em 21/10. O snapshot de truncamento e contagem de 12 testes não representa o estado atual. Para implementação e evidências atuais, consultar RC-40 e `docs/sprint-backlog.md`. Fins de semana/feriados podem legitimamente manter a referência diária mais recente; nunca buscar histórico para compensar.

## RC-31 — Idioma de interface PT-BR / EN-US (20/10/2026)

Pedido confirmado: opção de idioma em Settings, canto superior esquerdo alinhado horizontalmente com Add Widget, permitindo escolher Português (Brasil) ou English (United States); a preferência persiste e controla o idioma da aplicação.

Critérios de aceite: todas as strings de interface mantidas pelo Orbitz devem ser externalizadas para um catálogo PT-BR e traduzidas para EN-US; cobrir extensão/preferências, Workspace, widgets e aplicações próprias, diálogos, mensagens de erro, estados vazios, tooltips, acessibilidade e notificações. Conteúdo do usuário e textos de serviços externos não são traduzidos automaticamente. A escolha deve sobreviver ao reinício e evitar mistura de idiomas; validar layouts com textos mais longos e formatos de data/número por locale sem reescrever dados armazenados. PT-BR permanece o padrão inicial para preservar a experiência atual.

Decisões para implementação: catálogo JSON compartilhado por locale com IDs semânticos, opção GSettings `ui-language`, PT-BR padrão e fallback; mudança de idioma atualiza as janelas abertas sem reiniciar a sessão. Dados/IDs, conteúdo do usuário, textos dos serviços externos e idioma configurado para cada PDF não mudam. Implementação na fonte concluída em 22/10/2026 para Settings, Workspace, widgets/painéis, Sticky Notes, YouTube e mensagens. Erros Orbitz já exibidos carregam metadados explícitos de origem para re-renderizar; erros externos de mesmo texto não são traduzidos. Os catálogos atuais têm 1.735 chaves idênticas, com placeholders pareados. Suíte Python consolidada após as correções: 428 casos passaram, 4 skips ambientais, sem falhas; 36 scripts Node passaram. Instalação e QA visual ainda pendentes.

## RC-32 — Linha residual e barra de rolagem em Sticky Notes (20/10/2026)

Pedido confirmado a partir das capturas: remover a linha horizontal que aparece ao final do texto da nota e exibir a barra translúcida somente quando o conteúdo exceder a área visível.

Critérios de aceite atualizados: eliminar a linha residual no fim da área de texto; manter notas longas roláveis por mouse, teclado e meios já suportados; mostrar a barra somente quando houver overflow e ocultá-la quando o texto couber (“test 2”); trilho transparente/indicador translúcido sem cor sólida; não sobrepor texto nem expandir a nota. Preservar conteúdo, gravação, cabeçalho, dimensões e alça de redimensionamento. Confirmar aparência e interação em GTK real, além das verificações locais proporcionais.

Escopo restrito ao visual e à interação de rolagem: não alterar persistência SQLite/WAL, conteúdo da nota ou comportamento de redimensionamento. Ainda sem prioridade de sprint.

As tentativas anteriores não resolveram as linhas e uma deixou a scrollbar branca. O usuário esclareceu que a barra deve rolar o conteúdo sem expandir a nota. Em 20/10, o requisito visual foi atualizado: trilho transparente e indicador limpo/translúcido, aparecendo somente quando houver conteúdo excedente. UX revisou captura anterior; após novo relato de barra indevida em nota curta (“test 2”), o usuário definiu explicitamente ocultá-la quando não há overflow, prevalecendo sobre a recomendação anterior de reservar gutter constante (`ALWAYS`). Frontend implementou `AUTOMATIC`, overlay desligado e altura natural contida; o CSS neutraliza bordas/fundos/sombras em `TextView`, viewport e nós de overflow GTK. Quatro testes passaram; o smoke GTK de texto curto→longo→curto foi pulado porque não há display neste ambiente. Aplicação e confirmação visual/rolagem na sessão do usuário pendentes.

## RC-33 — Widget unificado Workspace (20/10/2026)

Pedido confirmado: consolidar os widgets de desktop que hoje aparecem separados em um único widget chamado Workspace. A captura enviada, com relógio, data e clima numa só superfície, é a referência inicial; o pedido também abrange os demais widgets separados.

Critérios de aceite: os módulos confirmados são apresentados dentro de uma única superfície/widget do GNOME Shell, sem manter cada módulo como janela/widget independente; cada módulo conserva controles e estados distinguíveis; configurações e dados atuais continuam acessíveis, com migração reversível se a consolidação alterar sua estrutura; atualização, acessibilidade, redimensionamento e interação permanecem funcionais.

Antes de implementar, inventariar módulos e confirmar o limite de “todos” (incluindo desempenho/sistema, rede, mídia, lançadores e aplicações separadas como Sticky Notes/YouTube), além de definir grade/layout, posicionamento, tamanho e habilitação individual das seções. Distinguir o widget **Workspace** do aplicativo **Orbitz Workspace** existente para evitar ambiguidade. Ainda sem prioridade de sprint.

## RC-34 — Relógio mundial adicional (20/10/2026)

Pedido confirmado: adicionar um relógio secundário ao relógio digital atual. O usuário seleciona cidade/região num catálogo pesquisável com identificador de fuso, e a hora correspondente aparece na tela junto ao horário local, apoiando quem trabalha remotamente. O mesmo seletor substitui a entrada manual usada para sobrescrever o fuso dos relógios digitais e analógicos.

Critérios de aceite: lista pesquisável, sem campo para digitar identificador, com nome de cidade/região, identificador tzdata e offset atual; preferência persiste após reiniciar; hora secundária é atualizada sem bloquear a interface; conversão usa identificadores e regras de fuso horário, incluindo horário de verão e mudanças de offset, mantendo correto o relógio local. Exibir região/fuso escolhido com a hora para evitar ambiguidade.

Estado: NÃO RESOLVIDO conforme relato do usuário em 20/10/2026: a opção está aparecendo somente no relógio analógico; também deve aparecer no relógio digital e usar dropdown com região/cidade, sem input manual. O checkout contém uma tentativa de catálogo pesquisável baseado em `/usr/share/zoneinfo/zone.tab`, mas os testes do parser e da formatação GLib não comprovam que o controle esteja exposto e utilizável nas duas interfaces. Manter aberto até reprodução e validação visual/funcional; não considerar a tentativa implementada como aceite.

## RC-35 — Itens de menu para Google Drive e Zoho WorkDrive (20/10/2026)

Pedido confirmado com baixa prioridade: adicionar Google Drive e Zoho WorkDrive como itens de menu no Orbitz. A navegação/consulta cotidiana deve ocorrer dentro do aplicativo, sem abrir browser. A autorização inicial OAuth pode abrir o browser do sistema; o aplicativo nunca solicita a senha da conta. Usar WorkDrive, pois Zoho Docs foi descontinuado.

Escopo inicial proposto: conectar/desconectar a conta; ver recentes e favoritos; buscar arquivos; mostrar estado de conexão; abrir arquivos compatíveis no aplicativo local padrão. Restringir permissões ao mínimo necessário, descrever o acesso solicitado e proteger/remover tokens pelo cofre seguro. Formatos nativos de Google Docs/Zoho Writer podem exigir browser para edição colaborativa completa; informar isso claramente.

Antes da implementação, decidir escopos OAuth, arquivos compartilhados, formatos suportados, cache e arquivos temporários, revogação de autorização e requisitos de verificação dos provedores. Navegação, busca e estados offline/erro não podem bloquear a interface. Prioridade baixa (P3 proposta); não atribuída a sprint.

## RC-36 — Aba central Integrations (20/10/2026)

Pedido confirmado: incluir uma aba **Integrations** ao lado de **Settings** e **About**. Ela será o ponto único para encontrar e gerir os serviços externos usados pelo Orbitz e as respectivas API keys, certificados e tokens, evitando que os formulários de conexão fiquem dispersos.

Critérios de aceite: inventariar integrações existentes e planejadas; listar cada serviço com status, conta/identificador conectado, permissões e ações contextuais para conectar, configurar, renovar/substituir credencial ou desconectar/revogar. Telas dos recursos que precisem de credenciais devem encaminhar para a entrada central sem criar cópias do formulário; preferências funcionais não secretas podem continuar junto ao recurso. Erros de autenticação e expiração devem informar próximo passo sem expor detalhes sensíveis.

Segurança: não revelar valores completos de tokens ou API keys por padrão, nem salvá-los em texto claro, logs ou configurações comuns; usar o cofre seguro do Orbitz, mascarar valores e permitir substituição/remoção explícita. Para certificados, mostrar tipo e validade/estado, proteger chaves privadas e oferecer importação/substituição/remoção com confirmação apropriada. Migração dos fluxos atuais deve preservar conexões e dados; não exigir que o usuário reconecte serviços sem necessidade.

Ainda sem prioridade de sprint. A cobertura só será considerada completa após inventário dos serviços integrados.

## RC-37 — Foco automático nas ações de terminal (20/10/2026)

Pedido confirmado: quando uma ação do Orbitz abrir Tilix para solicitar confirmação ou autorização, a janela nova deve receber foco para que o usuário possa confirmar imediatamente com Enter. Abrange ações dos painéis de atualizações, processos, leitura de firmware da RAM e limpeza, além do atalho btop.

Critérios de aceite: propagar o contexto de ativação GNOME apropriado à sessão (X11/Wayland) até Tilix; abrir janela separada sem redirecionar para uma janela antiga; preservar exatamente os argumentos do comando e a confirmação existente por Enter, inclusive a regra de EOF/cancelamento; não executar comandos privilegiados automaticamente nem alterar seu conteúdo. Validar com testes de argv, contexto e rotas, além de foco real na sessão GNOME.

Implementação local anterior: helper GJS cria startup/activation token e passa o contexto pelas ações; helper Python abre nova janela Tilix e herda o token. O usuário aplicou e observou Tilix sem foco; Enter não chegava ao prompt. Diagnóstico estático apontou captura modal do GNOME ainda ativa nos painéis. Correção local fecha o diálogo antes de iniciar o processo filho para não disputar foco e reabre o diálogo se o spawn falhar, preservando tokens, argv e confirmação. Testes focados passaram; auditoria independente não encontrou bloqueio para teste local. Em 20/10/2026, o usuário confirmou a conclusão após aplicar e reiniciar. A confirmação vale para o ambiente testado, sem generalização para outras sessões/sistemas.

## RC-38 — Abrir referências com Ctrl+clique em Sticky Notes (20/10/2026)

Pedido direto do usuário: Ctrl+clique em texto de uma nota abre um caminho local no gerenciador de arquivos, uma URL no navegador padrão ou um endereço de e-mail no aplicativo padrão de e-mail.

Critérios de aceite: só abrir referência com o modificador Ctrl; clique normal continua posicionando o cursor e editando texto. Enquanto Ctrl estiver pressionado sobre destino válido, destacar somente o texto do link em negrito e mudar o cursor para ponteiro; ao soltar Ctrl, sair do link, editar ou perder foco, restaurar estilo e cursor de edição. Identificar o item lógico sob o cursor, inclusive quando caminhos ou URLs quebram visualmente em várias linhas. Aceitar apenas diretórios/arquivos locais existentes e esquemas `http`, `https` e `mailto`; não interpretar o texto como comando nem usar shell. Abrir pelo serviço URI/aplicativo padrão do desktop e tratar falha sem perder ou alterar conteúdo. Testar sinteticamente detecção, Ctrl/clique normal, hover/tecla Ctrl, alcance exato do destaque, espaços em caminhos, texto multilinha e URIs inválidas; confirmar aparência e abertura real separadamente na sessão do usuário.

Implementado em `sticky-notes/card.py` + `sticky-notes/link_targets.py`: Ctrl+clique resolve apenas caminhos locais existentes (arquivos abrem a pasta contêiner), URLs HTTP/HTTPS e mailto, encaminhando-os ao serviço de aplicativo padrão via Gio sem shell. Clique normal permanece editável. Dez testes sintéticos, `py_compile` e diff check passaram; abrir os destinos e verificar negrito/cursor em sessão gráfica continua pendente. Sem prioridade de sprint atribuída.

## RC-39 — Alça de redimensionamento de Sticky Notes (20/10/2026)

Pedido confirmado: a alça/seta atual é difícil de atingir e fica longe da borda. Facilitar o redimensionamento ampliando a região de interação e posicionando-a junto ao canto inferior direito.

Critérios de aceite: área clicável de aproximadamente 28×28 px, ancorada a 2 px das bordas inferior/direita; indicador visual próximo de 6 px das bordas. O cursor deve indicar redimensionamento sobre toda a área; arraste nativo preserva canto/direção e tamanho salvo. A área ampliada não pode interceptar o texto editável nem mover/expandir a geometria inicial do cartão. Validar testes de contrato e gesto real em GTK após aplicar.

Frontend implementou a área usando `Gtk.Overlay`, manteve o drag pelo canto sudeste e reservou espaço inferior de conteúdo. Quatro testes unitários de layout/gesto passaram; smoke de geometria foi pulado sem display. Posição, alvo clicável e redimensionamento real continuam pendentes de conferência visual/interativa do usuário.

## RC-40 — Conversor único Fiat/Crypto e Configure funcional (21/10/2026)

Pedido confirmado: continuar o widget de conversão, corrigir o botão **Configure** que não abre a configuração e reunir o conversor de Bitcoin no widget existente. Não criar um segundo widget de conversão cripto.

Critérios: uma única configuração **Conversor de moedas**, com modos Fiat e Crypto. Fiat preserva BRL → USD como padrão, catálogo de moedas existente, inversão USD → BRL, modal com atualização manual e atualização automática a cada quatro horas. Crypto usa USD → BTC por padrão, permite procurar e escolher ativo por ID/nome/símbolo e inverter para ativo → USD; guardar categoria/ativo/direção na configuração, sem colisão por símbolos duplicados. A lista disponível deve refletir a cobertura real da fonte, sem alegar conter todas as criptomoedas. Apresentar somente a conversão no widget; precisão cripto preserva valores pequenos, e a modal identifica a fonte. Falha de rede, cotação velha/inconsistente ou ativo indisponível não pode mostrar cotação antiga como atual. Sem histórico, previsão ou fallback.

Configure deve construir/selecionar uma página visível e funcionar na faixa libadwaita/GNOME declarada, incluindo libadwaita 1.1. O teste precisa percorrer botão Configure → janela de configurações → subpágina do conversor, além do controle de categoria e contrato CLI; teste que apenas verifica o clique em um construtor falso não basta. Reproduzir a abertura em GTK/GNOME real é uma verificação separada.

Estado de implementação em 21/10: incompatibilidade real confirmada (`Adw.SwitchRow` não existe em libadwaita 1.1) e substituída por `Gtk.Switch` dentro de `Adw.ActionRow`. Backend acrescenta CoinPaprika sem chave, com catálogo dos ativos efetivamente precificados no plano, validação de ID/timestamp/preço e sem cache/fallback. Ao validar a ausência do segundo elemento na área de trabalho, foi encontrada outra corrida: a gravação assíncrona do comando após carregar o catálogo sobrescrevia o marcador temporário `ElementAdded` antes de o Shell processá-lo. O frontend agora preserva marcadores estruturais pendentes e compara a topologia de elementos persistida com a topologia em execução para reconstruir quando divergirem. Revisão posterior encontrou e corrigiu também duas corridas de ciclo de vida: renomear um elemento não invalida mais os controles do catálogo, e uma resposta atrasada não substitui a cotação quando o comando muda de Fiat para Crypto. O parser também converte JSON aninhado, expoentes numéricos inválidos e inteiros acima do limite do Python em erro genérico, sem traceback ou mensagem interna. O texto do widget preserva agora as casas fornecidas quando o destino é cripto; Fiat e cripto→USD continuam com duas casas. Os testes dirigidos passaram; instalação e execução visual no GNOME ainda não confirmadas pelo usuário.

Restrição do provedor: CoinPaprika Free é de uso pessoal; exibição/redistribuição para clientes exige licença/plano compatível. Esta implementação não constitui autorização para distribuição comercial dos dados. Reavaliar termos/provedor ou usar chave/licença apropriada antes de promover esse serviço em produto comercial. Nunca embutir chave compartilhada.

## FX-01 — formatação com centavos e precisão cripto (21/10/2026)

Usuário esclareceu no exemplo Fiat: preservar centavos, usando duas casas decimais arredondadas (metade para cima), vírgula decimal e ponto de milhar: `0.19829 → 0,20`, `5.04 → 5,04`, `83060.16777893 → 83.060,17`. Isso se aplica a Fiat e a cripto→USD. Para USD→ativo cripto, não arredondar a cotação unitária para centavos: mostrar os dígitos da taxa recebida, remover apenas zeros fracionários finais e nunca substituir uma fração pequena por `0,00` ou inventar precisão. JSON mantém a taxa original. Sem efeito em invoices. Testes dirigidos aprovados; instalação/validação visual pendentes.

## FX-02 — calculadora na modal (21/10/2026)

Pedido confirmado: informar um valor livre na modal e ver o total convertido para o par/sentido selecionado, fiat ou cripto. Campo inicia em 1 e recalcula ao digitar, sem nova consulta de rede. Aceita vírgula decimal e milhares brasileiros (`1.000,50`), ou ponto decimal sem agrupamento; `1.000` significa mil. Zero permitido; vazio, negativo, notação científica e entradas malformadas não geram total. Valor digitado é temporário na modal, não salvo nas configurações. Resultado com duas casas e separadores pt-BR. Multiplicação decimal exata da taxa JSON original via BigInt, arredondando metade para cima somente no total; nunca calcular sobre o valor unitário exibido. Atualizar/inverter invalida o total até resposta válida; erro não mantém total antigo. Sem efeito em invoices ou gravação financeira.

Implementação fonte e verificações dirigidas concluídas (19 testes Python FX, Node modal/erros/calculadora e composição; sintaxe/diff). Revisão focada independente concluída sem defeito bloqueador reproduzido; auditor confirmou os exemplos de multiplicação e arredondamento também no GJS real. Instalação e validação visual/interativa GNOME pendentes.


## FX-03 — precisão completa na calculadora cripto (21/10/2026)

Pedido confirmado pela captura: o total cripto não deve desaparecer como `0,00`. Na calculadora em modo Crypto, em ambos os sentidos, exibir o produto decimal da quantidade pela taxa recebida sem limite de duas casas nem notação científica; remover apenas zeros finais sem significado. A mesma regra de precisão suficiente vale para a cotação unitária USD→ativo no widget; no sentido ativo→USD a cotação continua em centavos. Exemplo sintético: `400 × 0.000016273845678 = 0,0065095382712 BTC`. Precisão limitada à taxa fornecida, sem inventar dígitos adicionais.

Implementado na fonte com BigInt; testes Node da calculadora/modal e composição aprovados. Revisão média agrupada no fechamento; instalação e validação visual GNOME pendentes.

## WX-02 — alinhamento dos cartões da previsão (22/10/2026)

Pedido confirmado pela captura: centralizar dia/data, condição, temperaturas mínima/máxima e probabilidade de chuva no mesmo eixo do ícone de cada cartão. Centralização também nas linhas quebradas, preservando as sete colunas e suas larguras. Ajuste de apresentação de baixo risco implementado na fonte; teste sintético do painel aprovado. Instalação e conferência visual no GNOME pendentes.

## RC-41 — Emoji, movimentação e exclusão de Sticky Notes (22/10/2026)

Pedidos confirmados: o seletor “Insert emoji” deve abrir fora dos limites da nota e receber foco para que seja visível e utilizável. Durante o arraste de uma nota, mostrar um alvo de lixeira no centro inferior; soltar a nota sobre ele a exclui permanentemente da tabela ativa do banco de dados. No menu, remover “Archive note” e “Restore archived note” e oferecer “Delete note”. Notas são descartáveis e não há fluxo de restauração.

Critérios: manter foco/cursor do editor após inserir emoji ou fechar o seletor; posicionar o seletor em uma janela transitória espaçosa; mostrar e retirar a lixeira em todos os caminhos de início, cancelamento, Escape, soltura e destruição da nota; excluir apenas após soltura dentro do alvo, mantendo a janela se salvar/exclusão falhar. A exclusão deve usar ID e revisão esperada para não apagar uma edição concorrente; antes de remover do banco ativo, purgar a nota por ID em todos os backups diários retidos. Se a purga de algum snapshot falhar, não remover o registro ativo nem fechar a nota; repetir a operação deve completar a purga idempotentemente. Chamadas repetidas para nota já ausente são idempotentes. Notas previamente marcadas como arquivadas continuam visíveis como notas normais, sem migração destrutiva.

Implementado na fonte: a exclusão valida a revisão ativa, purga por ID os snapshots SQLite retidos e só então confirma a remoção ativa; falha antes ou durante promoção preserva a nota ativa e permite retry. A substituição entre vários snapshots não é uma transação filesystem única. 47 testes Sticky passaram, 2 smokes GTK foram pulados sem display; I18N 6/6, domínio 11/11, `py_compile`, JSON e `git diff --check` passaram. Dois casos adversariais de symlink/sidecar encontrados na primeira revisão foram corrigidos e ganharam testes. Reauditoria independente aprovada para aplicação local; limite residual documentado contra ator concorrente do mesmo UID. Inspeção GTK/instalação pendente.

## RC-42 — Título de nota editável e feedback do alvo de exclusão (22/10/2026)

Pedido confirmado pela captura: remover notas antigas arquivadas que ficaram visíveis, mas falham ao excluir; transformar o cabeçalho padrão “Sticky Notes” em título editável por nota; mudar o cursor quando ele estiver sobre a lixeira durante o arraste.

Critérios de aceite: corrigir a causa da falha nas notas legadas `archived=1`, sem abrir banco pessoal durante desenvolvimento; menu “Delete note” e drop sobre a lixeira devem conseguir excluir uma nota arquivada, purgando seu ID do banco ativo e de todos os backups retidos; manter erro acionável e preservar nota se operação não terminar. Título é independente do corpo, editável por usuário, individual por nota, persiste ao reabrir e não modifica o texto existente; título vazio/legado mostra o rótulo padrão localizado. Cursor muda ao entrar no alvo de drop e restaura ao sair, cancelar ou finalizar.

Implementado na fonte: migração idempotente adiciona título sem alterar IDs/textos existentes; título independente usa CAS; cursor muda sobre a lixeira. Exclusão arquivada foi testada com snapshots legados e atuais. Snapshots WAL órfãos agora são normalizados por SQLite com checkpoint completo; WAL ocupado, symlinks e arquivos inválidos falham fechados. Isso é uma causa compatível com a captura, mas o armazenamento pessoal não foi examinado e a causa real não está confirmada. Migração do título e ativação do WAL têm serialização/retry limitado; teste concorrente com quatro pares de processos passou em quatro rodadas. Testes integrados Sticky 55 (53 pass, 2 skips GTK), I18N 6/6 e domínio 11/11 passaram; compilação, JSON e diff-check passaram. Reauditoria independente focada aprovada para aplicação local; instalação e inspeção GTK pendentes.

Validação manual do usuário em 22/10/2026: após a atualização, as notas abriram normalmente e as notas parasitas legadas que haviam permanecido depois de arquivadas foram excluídas com sucesso. Isso confirma o fluxo no armazenamento real do usuário; não identifica retroativamente qual estado específico causava a falha anterior.

## RC-43 — Recuperação do clique e inicialização independente de Sticky Notes (22/10/2026)

Relato confirmado: ao acionar o controle de abrir todos os widgets, o ponteiro continua se movendo mas cliques deixam de funcionar; as Sticky Notes também não aparecem no carregamento dos widgets. Critérios: erros ao encerrar diálogos não podem deixar o backdrop da extensão reativo nem impedir cancelamento de timers/processos; token modal local deve acompanhar o ciclo de vida do ator e não ser reutilizado após `popModal` falhar. A inicialização do app de notas deve ser independente de falha na construção dos widgets, e falha assíncrona do filho precisa gerar diagnóstico.

Mitigações implementadas na fonte em `extension/extension.js`: sincronização do token no sinal de destruição do backdrop, descarte do token em `finally` após tentativa de `popModal`, limpeza isolada por callback, reativação do backdrop apenas na próxima abertura, fechamento não reativo se `pushModal` falhar ou retornar sem grab, e rollback de widgets sem encerrar o app de notas. A auditoria focada considerou seguro para teste local. Quatro testes Node direcionados e `git diff --check` passaram; o teste modal executa sucesso/falha/ausência de retorno do push. Validação manual do usuário em 22/10/2026 confirmou que o bloqueio de cliques foi resolvido. Limite: o teste sintético não cobre falha interna ao próprio `grab.dismiss()`; não generalizar além da sessão testada.

## RC-44 — Inicialização visual das Sticky Notes (22/10/2026)

Relato confirmado após corrigir o bloqueio de cliques: abrir uma nota exibia apenas um retângulo cinza. Diagnóstico nos logs da sessão: `Gtk.Entry.set_placeholder_text` recebeu um objeto `Message` em vez de texto durante `Card.__init__`, abortando a construção da janela. O launcher e os módulos instalados conferem com a fonte por hash. Correção: passar o placeholder por `ui.call`, que converte a mensagem e mantém a tradução dinâmica; teste AST de regressão adicionado. Testes de layout/interação, `py_compile` e `git diff --check` passaram; dois smokes GTK foram ignorados sem display. Validação manual do usuário em 22/10/2026 confirmou que as notas estão abrindo e funcionando após a aplicação.

## RC-45 — Placeholder visível para o título de Sticky Notes (22/10/2026)

O título vazio deve mostrar o placeholder `STICKY NOTE` ao criar/abrir a nota e também enquanto o campo recebe foco; o texto desaparece assim que o título deixa de estar vazio e reaparece se o usuário apagar todo o conteúdo. Manter campo editável, persistência e acessibilidade. Implementado como label traduzível sobreposto ao `Gtk.Entry`, com eventos encaminhados ao campo; os dois catálogos usam a grafia solicitada `STICKY NOTE`. Testes direcionados de layout/interação: 19 executados, 17 aprovados e 2 smokes GTK pulados por indisponibilidade de display; `py_compile`, JSON e diff-check passaram. Conferência visual na instalação ainda pendente.

## RC-46 — Menu do cabeçalho e gesto de arraste para lixeira (22/10/2026)

Remover a região clicável de arraste personalizada do topo da nota; a movimentação nativa por Super continua disponível. Substituir os três pontos por botão dropdown com as opções do clique direito. Um tooltip não pode ficar sobre o menu aberto. Preservar a lixeira inferior por um gesto diferente do cabeçalho; gesto escolhido após consulta de Design/UX: Shift+arraste somente na margem inferior vazia. Soltar a nota dentro da lixeira exclui permanentemente; soltar fora apenas move. Manter “Delete note” como alternativa no menu. O gesto não deve interceptar edição, Ctrl+clique em links ou redimensionamento. No Wayland GTK nativo, manter a exclusão pelo menu se o ambiente não fornecer coordenadas globais confiáveis para o alvo.

Critérios de aceite: o topo não inicia movimento; dropdown e clique direito expõem as mesmas opções; nenhum tooltip encobre o menu; Shift+arraste começa apenas na margem vazia e apresenta a lixeira; drop nela exclui e drop fora conserva a nota na nova posição; edição, links, resize, escape/cancelamento e Super+arraste continuam disponíveis. Fonte e testes sintéticos implementados; inspeção visual e smoke gestual na sessão GNOME ainda pendentes.

## RC-47 — Notas secretas protegidas por PIN na interface (22/10/2026)

Adicionar “Settings” como primeira opção do menu da nota. Settings deve permitir definir um PIN numérico de exatamente quatro dígitos e trocar PIN somente após validar o atual; nunca expor PIN em logs. Disponibilizar “Secret Note” para marcar a nota. Se ainda não existir PIN, abrir Settings para sua criação antes de alterar a nota; cancelar mantém a nota inalterada. Notas marcadas iniciam bloqueadas ao abrir/reiniciar o aplicativo e exigem PIN correto para revelar conteúdo. Depois de reveladas, exibir uma contagem regressiva de 15 segundos somente quando o ponteiro sair da janela; ao retornar, cancelar a contagem; no término, ocultar corpo e título e mostrar overlay opaco com cadeado, sem deixar conteúdo legível. Excluir nota secreta sempre exige PIN, inclusive após desbloqueio. Remover a marca secreta também deve autenticar para impedir contorno do bloqueio.

O usuário escolheu proteção somente na interface, sem criptografia em repouso. Portanto, esta função é uma barreira de visualização dentro do aplicativo, não proteção contra acesso direto aos arquivos: texto permanece legível no SQLite e em seus backups. Não anunciar confidencialidade contra outros processos/usuários com acesso aos arquivos. Critérios de aceitação incluem migração aditiva e preservação de notas existentes, bloqueio em reinício, PIN anterior ao alterar, cancelamento seguro, exclusão protegida, timer cancelável e limpo no ciclo de vida, ausência de vazamento visual/accessibility enquanto bloqueada, e compatibilidade PT-BR/EN-US.
