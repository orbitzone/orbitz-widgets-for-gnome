# Fila de sprint e revisões

Atualizado em 21/10/2026. Lote lógico, sem agenda automática. Política: [workflow](agents/workflow.md). Prioridades de produto continuam em [backlog](backlog.md).

## Estado atual

INV-01–04 já auditadas; WSP-01 está implementado e auditado nas fontes. O usuário confirmou Google Calendar e Datas comemorativas em 20/10; em 21/10 confirmou que feriados persistem em todos os calendários e aprovou visualmente as Sticky Notes. A revisão independente das mudanças desde 20/10 encontrou defeitos reproduzíveis e dados identificáveis em screenshots públicos. Os defeitos foram corrigidos com testes direcionados, as capturas foram redigidas e a documentação técnica harmonizada. A revalidação independente final não encontrou novos achados nos deltas verificados. Testes interativos de GTK para invoices/chooser e o aceite real de WID-02 continuam pendentes. Esta revisão não alterou a instalação nem publicou alterações.

| Item | Estado | Risco / responsável | Próxima ação |
|---|---|---|---|
| OPS-01 — fluxo econômico | Documentação ajustada | Baixo / supervisor | Aplicar nos próximos briefs; sem auditor ou UX para esta alteração |
| INV-01–04 — conjunto atual | Auditoria local concluída | Parecer INV-04 | Reusar evidência se o alvo não mudar; não reauditar por hábito |
| Invoices: histórico/versões e chooser em GTK real | 62 testes sintéticos passaram (PDF, histórico, versões, chooser/fluxos); GTK não inicializou neste processo, portanto interação/chooser nativos continuam sem validação | Frontend/usuário | Validar no Workspace instalado: gerar invoice de teste, abrir histórico/versões, exportar e abrir chooser; sem usar dados fiscais reais |
| CAL-06/07 — revisão média consolidada | Auditoria independente concluída sem defeito reproduzível; usuário confirmou Google, fonte de feriados funcionando e persistência em todos os calendários | Auditoria e validação do usuário concluídas | Fechado |
| CAL-01 — Calendly real | Integração por token implementada; conta real não confirmada | Usuário, se/quando desejar testar | Teste manual separado; não bloqueia funcionamento já confirmado do Google e da fonte pública |
| Formato decimal PT e rótulos de timesheets homônimas | Propostas opcionais | Baixo / frontend | Priorizar com futuro lote de UI; não ativar UX/auditor agora |
| STICKY-01 — borda e scrollbar translúcida sob demanda | Testes de contrato passam; usuário confirmou a apresentação atual das Sticky Notes como correta | Baixo / frontend | Fechado por validação do usuário |
| STICKY-02 — Ctrl+clique e feedback visual | Implementado; testes sintéticos passam; usuário confirmou que as Sticky Notes estão ótimas | Médio / frontend | Fechado por validação do usuário |
| STICKY-03 — alça de redimensionamento | Alvo 28×28 px junto à borda, cursor se-resize e gutter preservado; usuário aprovou a apresentação atual das Sticky Notes | Baixo / frontend | Fechado por validação do usuário |
| TERM-01 — foco automático do Tilix | Concluído conforme confirmação do usuário após atualização/reinício da sessão; testes dirigidos passaram e auditoria focada não encontrou bloqueio. | Médio / frontend | Fechado. Não generalizar a outras sessões/ambientes além do teste confirmado pelo usuário. |
| FX-01 — widget único conversor fiat/cripto | Fiat/cripto integrados; testes cobrem persistência, Configure, reconstrução, lifecycle, direção, erros de parse e precisão. Backend implementa CoinPaprika sem chave para uso pessoal; catálogo por IDs contém somente ativos cotados no plano. Unidade USD→cripto preserva frações; Fiat e cripto→USD usam duas casas pt-BR. 24 testes FX passam; auditoria independente final sem novos achados nos deltas conferidos. | Médio / backend + frontend + supervisor | Validar instalação e visualmente no GNOME; o usuário ainda precisa confirmar os dois modos e sentidos. Sem histórico/previsão/fallback; polling 4h. Plano gratuito pessoal, uso comercial voltado a clientes exige licença compatível. |
| CFG-01 — Configure e atualização dos elementos do conversor | `Adw.SwitchRow` ausente em libadwaita 1.1 abortava a construção da página; substituído por `Gtk.Switch`/`Adw.ActionRow`. Foi corrigida também a corrida em que o callback do catálogo substituía `ElementAdded` antes do debounce do Shell: marcadores estruturais pendentes são mesclados e a topologia armazenada é comparada à árvore ativa. Teste executa Configure → janela → subpáginas e adicionar elemento → callback assíncrono → atualização do Shell, cobrindo Fiat + Crypto, edição simples e exclusão. | Médio / frontend | Testes de fonte passaram; instalar e conferir visualmente no GNOME; usuário confirma que os dois elementos aparecem e Configure/remover funcionam. |

## Cadastro de próxima tarefa

Uma linha por mudança: ID, escopo/arquivos, risco, responsável, critérios, evidência/testes e estado da revisão. Estados: planejada, em desenvolvimento, testes locais aprovados, auditoria pendente, revisada ou impedida. Para alto risco indicar operação bloqueada até revisão focada; para risco médio manter na fila de fechamento, sem ocultar pendência ao usuário.

## Fechamento do lote

1. Congelar alvo/diff e reunir testes/evidências dos responsáveis.
2. Acionar auditor uma vez para mudanças pendentes e integração; não repetir itens já revistos sem mudança.
3. Corrigir impeditivos e verificar somente o que foi afetado, ampliando se necessário.
4. Supervisor atualiza estados, limites, comando de atualização e roteiro de teste. Publicação segue autorização do usuário e revisões exigidas; nenhuma é disparada automaticamente.

## QA consolidado — 21/10/2026

Suíte Python completa: 284 testes executados, 281 aprovados e 3 pulados (dois cenários de socket bloqueados no sandbox e smoke de geometria GTK sem display acessível). Os 31 testes Node e os dois testes GJS passaram; `git diff --check` passou. Checagens dirigidas: FX 24/24 e Sticky Links 15/15. Os testes cobrem os defeitos encontrados: CLI com JSON aninhado, expoente inválido e inteiros acima do limite do parser, limites Decimal, renomeação/identidade do catálogo, descarte de resposta antiga, precisão USD→cripto, regex de email de tempo limitado e URI local malformada. A auditoria independente revalidou os últimos deltas e não encontrou novos achados; instalação e interação visual no GNOME continuam pendentes. A rota e o formato da Frankfurter foram conferidos com a documentação oficial; consulta externa direta não foi possível neste ambiente.

GTK nativo para invoice/chooser, inspeção visual dos widgets de moeda e o seletor real de WID-02 permanecem pendentes de sessão interativa. O usuário validou as Sticky Notes e confirmou a persistência de feriados em todos os calendários. A instalação não foi atualizada nesta revisão; a fonte e os testes não comprovam a experiência visual nem a versão carregada pela sessão GNOME. WID-02 continua explicitamente pendente e não é declarado concluído.

## WID-02 — Relógio mundial: requisito de seletor ainda não resolvido

Em 20/10/2026 o usuário informou que a opção continua aparecendo apenas no relógio analógico e reiterou que precisa estar disponível também no digital como dropdown com região/cidade, sem input manual. Embora exista tentativa de implementação local e testes sintéticos do catálogo, isso não atende como evidência de aceite. Manter pendente; quando retomado, verificar a página de configuração digital e a analógica na UI real, corrigir a exposição/seleção e só então atualizar o estado. O usuário pediu seguir outras implementações enquanto isso.

## WSP-01 — Orbitz Workspace (revisado, 19/10/2026)

Usuário aprovou todas as recomendações e ampliou identificação da timesheet. Um lote integrado, sem revisões por incremento; auditor independente ao final, antes de aplicar mudanças de dados/backup.

| Grupo | Escopo confirmado | Responsável | Risco / revisão |
|---|---|---|---|
| WSP-01A | Nome Orbitz Workspace, termos Agenda/Tarefas/Horas/Invoices, navegação visível e Hoje com compromissos/tarefas/timer | Frontend | Médio; integra no fechamento |
| WSP-01B | Nome/contexto da timesheet: cliente, contrato/projeto, departamento/centro de custo; fiscal separado; contexto em preview/PDF; alerta de possível duplicidade e pagamento manual independente de assinatura | Backend + frontend | Alto por persistência/faturamento; revisar antes de aplicar |
| WSP-01C | Backup/restauração do conjunto tarefas/horas/perfis/invoices/versões/estado UI, com proteção e recuperação; credenciais/calendários/Sticky Notes fora do escopo | Backend + frontend | Alto; revisar antes de restaurar/aplicar |

Fechamento: backend/frontend concluídos; uma auditoria integrada sem impeditivos reproduzidos, 169/169 testes Python e cenário completo temporário de backup/restauração aprovados. [Parecer](audits/2026-10-19-workspace-audit.md). Hashes finais conferidos pelo supervisor; UX não acionado. Plano de atualização: 21 arquivos, zero comandos. GTK/choosers reais e instalação pendentes; fechar/reabrir Workspace após aplicar, sem logout obrigatório. Nenhuma instalação ou publicação realizada.

WSP-01 PDF QA (supervisor): geradas duas amostras exclusivamente sintéticas PT/EN em `work/workspace-pdf-qa`, renderizadas por `/usr/bin/pdftoppm` e inspecionadas as quatro páginas. Contrato longo/acentos/XML literal/departamento/contexto e destinatário fiscal distintos ficaram legíveis, sem corte/sobreposição; cabeçalhos repetidos/rodapés separados. Caso 8h × BRL125,50 =1004,00 conferido. Hashes das fontes em `work/workspace-pdf-qa/source-hashes.json` para conferência final. Evidência limitada às amostras, não à interface GTK nem a documentos pessoais. Skill PDF aplicada; marcador registrado antes da criação.

## CAL-01 — integrações e About (revisado, 19/10/2026)

RC-22. Backend: clientes Google/Calendly, autenticação/cofre e testes. Frontend: conectar/sincronizar/desconectar, erros e investigação da identidade About. Risco alto em credenciais: uma revisão focada ao final, antes da aplicação. UX não acionado. Nenhuma conta real, instalação ou publicação alterada. Dependências de credenciais externas serão documentadas.

Fechamento CAL-01: [auditoria focada](audits/2026-10-19-calendar-audit.md) sem impeditivos reproduzidos,35 testes aprovados/2skips ambientais de socket, identidade Node e integração temporária com backup/desconexão aprovados. Hashes finais conferidos. About não regrediu na fonte/artefato Orbitz instalado; conteúdo da captura corresponde ao legado, acionamento exato pendente de teste visual. Plano10arquivos/0comandos, nenhuma aplicação. Reabrir Workspace e abrir prefs explicitamente por UUID após atualização; sem logout obrigatório. OAuth/PAT/cofre/GTK reais pendentes.

## CAL-02 — orientação da conexão Google (testes locais aprovados, 19/10/2026)

RC-24. Frontend: passos com links oficiais, seletor JSON identificado, nome sugerido, validação/estado dinâmico e autorização habilitada quando pronta. Backend/auth intactos; testes afetados agora, revisão média agrupada no próximo fechamento. Sem UX/auditor automáticos nem aplicação instalada. Supervisor mantém README/guia.

CAL-02: nove testes frontend aprovados (inclui JSON Desktop válido/inválido/ausente, estados de prontidão e regressões de cancelamento), sintaxe/diff conferidos. Uma fonte a atualizar, zero comandos. Autenticação/cofre intactos; revisão média permanece agrupada para fechamento. GUI real e aplicação pendentes; fechar/reabrir Workspace, sem logout.

## CAL-03 — Login Google direto (revisado, 19/10/2026)

RC-25 substitui importação de JSON no fluxo normal CAL-02. Backend configura cliente público fornecido pelo usuário, frontend simplifica diálogo, especialistas preservam cancelamento/auth/cofre. Testes afetados e uma revisão focada de autenticação antes de aplicar; semUX/global automático. Supervisor revisa README/guia para distinguir mantenedor de usuário final. Sem login real/instalação/publicação por inferência.

CAL-03 encerramento das fontes: [parecer focado](audits/2026-10-19-google-login-audit.md) sem impeditivo reproduzido;30 testes aprovados e2skips de sockets,4hashes conferidos. Plano2arquivos/0comandos. Sem login/GTK/cofre reais ou aplicação; fechar/reabrir Workspace após aplicar, sem logout obrigatório. CAL-02 foi substituído no fluxo público; revisão média daquele diálogo removido não exige auditoria separada.

CAL-04 (em investigação): erro pós-callback real, zero conexões Google salvas; diagnóstico seguro das falhas tokenendpoint, sem mudar grants/credenciais/protocolo. Testes direcionados agora; revisão média agrupada. Mensagem Orbitz do usuário ainda necessária para causa exata.

CAL-04 fechamento: defeito callback reproduzido em fixture (falha no envio perdia código/negação validados), corrigido registrando estado antes da resposta. Progresso fixo, falha reabilita botão, erros de token sanitizados. Revisão focada:36 testes aprovados/2skips socket e8 cenários adversos,6hashes conferidos; [parecer](audits/2026-10-19-google-callback-audit.md). Plano4arquivos/0comandos. Login real/causa exclusiva do usuário não comprovados. Instalação pendente; fechar/reabrir Workspace, sem reinício de sessão.

CAL-05/RC-27 em implementação: causa client_secret ausente confirmada no endpoint oficial com código fictício e rede autorizada, sem conta/token real. Backend configuração privada mantenedor+tool+diagnóstico; revisãofocada antes aplicar. Caminho JSON real solicitado por texto, nunca conteúdo/chat. UI normal loginGoogle intacta, distribuição pública pendente.

CAL-05 revisado: [parecer](audits/2026-10-19-google-client-config-audit.md),35pass/2skips/6 adversos,6hashes. Configuração real do mantenedor preparada após permissão, check e permissões privadas conferidos pelo supervisor; auditor usou só fixtures. Plano2arquivos/0comandos para instalação; login real pendente. Reabrir Workspace após aplicar, sem logout.

CAL-06/RC-28 em desenvolvimento: usuário confirmou loginGoogle, mas feriados/tarefas/horas marcados não aparecem na fonte ativa da Agenda. Frontend alinhar conteúdo/legenda/tooltips/rotas e link de ativação opcional; backend/auth intactos. Testes afetados agora, revisão média no próximo fechamento; semUX/auditor automático.

CAL-06 testes locais aprovados:18 testes (7novos+11frontend), AST/diff check; fonte estável,5arquivos/0comandos. Revisão média continua na fila para fechamento, sem convocação adicional por incremento. GUI/aplicação pendentes. Reabrir Workspace após atualizar, sem logout; conferir dias com feriado de outra fonte e atividade local.

Validação manual do usuário em 20/10/2026: Google Calendar funcionou na instalação atual. Confirma o fluxo usado pelo usuário; não generalizar a todas as contas, versões ou ao Calendly. A revisão média permanece no fechamento consolidado.

CAL-07/RC-29 em implementação: fonte pública padrão permanente com Ativar/Desativar e adoção/restauração idempotente. Backend estado/persistência; frontend gerenciamento/filtros/sync/cancel/Agenda. Testes afetados agora, revisão média agrupada; nenhuma nova auditoria/UX ou aplicação automática.

CAL-07 testes locais aprovados:31 dirigidos (7persistência+16frontend+8atividade) e regressão dados externos, sintaxe/diff. Plano3arquivos/0comandos. Risco médio, revisão na fila de fechamento; sem auditor/UX extra. Sem dados reais ou instalação alterados. Teste manual: reabrir→Gerenciar→fonte padrão recuperada→Desativar→reabrir e confirmar desativada→Ativar. Sem logout necessário.

Validação manual do usuário em 20/10/2026: a fonte Brasil · Datas comemorativas funcionou na instalação atual. Não há confirmação explícita do ciclo desativar→reabrir→reativar; manter esse caso como teste manual opcional de fechamento. A revisão independente média continua agrupada para a sprint.

## WID-02 — relógio mundial adicional

Implementação local: opção na configuração do relógio digital para ativar o relógio secundário, escolher cidade/região em catálogo pesquisável e mostrar a localidade com hora formatada. O catálogo vem da base tzdata do sistema e não depende de GWeather; o mesmo seletor substitui o campo manual de sobrescrita de fuso nos relógios digitais e analógicos. Testes do catálogo e formatação/timezone passam. Risco médio; revisão independente fica no fechamento da sprint. GTK/preferências e visual ainda não conferidos em sessão real; não instalado.

## FX-01 — formatação com centavos corrigida (21/10/2026)

Usuário esclareceu a apresentação Fiat: duas casas decimais arredondadas metade para cima, vírgula decimal e ponto de milhar (`0.19829 → 0,20`, `5.04 → 5,04`, `83060.16777893 → 83.060,17`). Fiat abaixo de `0.005` aparece `0,00`; USD→cripto é exceção e preserva os dígitos fornecidos para não zerar o ativo pequeno. JSON mantém a taxa original. Testes FX dirigidos passaram; instalação e validação visual pendentes.

## FX-02 — calculadora na modal (21/10/2026)

Pedido confirmado: informar um valor livre na modal e ver o total convertido para o par/sentido selecionado, fiat ou cripto. Campo inicia em 1 e recalcula ao digitar, sem nova consulta de rede. Aceita vírgula decimal e milhares brasileiros (`1.000,50`), ou ponto decimal sem agrupamento; `1.000` significa mil. Zero permitido; vazio, negativo, notação científica e entradas malformadas não geram total. Valor digitado é temporário na modal, não salvo nas configurações. Resultado com duas casas e separadores pt-BR. Multiplicação decimal exata da taxa JSON original via BigInt, arredondando metade para cima somente no total; nunca calcular sobre o valor unitário exibido. Atualizar/inverter invalida o total até resposta válida; erro não mantém total antigo. Sem efeito em invoices ou gravação financeira.

Implementação fonte e verificações dirigidas concluídas (19 testes Python FX, Node modal/erros/calculadora e composição; sintaxe/diff). Revisão focada independente concluída sem defeito bloqueador reproduzido; auditor confirmou os exemplos de multiplicação e arredondamento também no GJS real. Instalação e validação visual/interativa GNOME pendentes.

Diagnóstico de instalação FX-01/FX-02 em 21/10: hashes SHA-256 do painel `currency.js` e do coletor `currency-widget.py` instalado conferem com a fonte atual. Usuário mostra modal sem calculadora e cripto com formato antigo ao abrir, embora o coletor já apresente centavos: evidência compatível com JavaScript antigo ainda carregado no Shell. Sessão declarada Wayland; orientar sair/entrar na sessão para carregar módulos atualizados, sem reinício automático. Calculadora/visual continuam sem aceite real após nova sessão; não repetir aplicação como solução para arquivos já iguais.


## FX-03 — precisão completa na calculadora cripto (21/10/2026)

Pedido confirmado pela captura: o total cripto não deve desaparecer como `0,00`. Na calculadora em modo Crypto, em ambos os sentidos, exibir o produto decimal da quantidade pela taxa recebida sem limite de duas casas nem notação científica; remover apenas zeros finais. A cotação unitária USD→ativo também preserva as casas fornecidas; ativo→USD permanece em centavos. Exemplo: `400 × 0.000016273845678 = 0,0065095382712 BTC`. Sem inventar precisão além da taxa recebida.

Implementado na fonte com BigInt; testes Node da calculadora/modal e composição aprovados. Revisão média agrupada no fechamento; instalação e validação visual GNOME pendentes.
