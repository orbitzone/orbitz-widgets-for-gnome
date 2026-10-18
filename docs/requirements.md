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
