# Fila de sprint e revisões

Atualizado em 22/10/2026. Lote lógico, sem agenda automática. Política: [workflow](agents/workflow.md). Prioridades de produto continuam em [backlog](backlog.md).

## Estado atual

INV-01–04 já auditadas; WSP-01 está implementado e auditado nas fontes. O usuário confirmou Google Calendar e Datas comemorativas em 20/10; em 21/10 confirmou que feriados persistem em todos os calendários e aprovou visualmente as Sticky Notes. A revisão independente das mudanças desde 21/10 encontrou AUD-01 no rollback do atualizador: manifesto adulterado podia apontar para arquivo fora das raízes Orbitz; `--apply` não reproduziu o efeito. Backend corrigiu o código; revisão independente focada confirmou o fechamento e 26 testes passaram. Manifestos ainda não são assinados; usar somente pastas de rollback confiáveis. Duas expectativas de locale nos testes foram corrigidas e a suíte global passa. Contagens documentais foram atualizadas ao resultado consolidado. GTK/AT, instalação, busca meteorológica online e latência real da UI ainda não foram validados. O caminho síncrono do PIN mediu 378–410 ms para a primitiva PBKDF2 nesta máquina; rastrear como PERF-01. Esta revisão não alterou a instalação nem publicou alterações.

| Item | Estado | Risco / responsável | Próxima ação |
|---|---|---|---|
| OPS-01 — fluxo econômico | Documentação ajustada | Baixo / supervisor | Aplicar nos próximos briefs; sem auditor ou UX para esta alteração |
| AUD-01 — integridade do rollback | Correção local pelo backend e revalidação independente concluídas; 26 testes dirigidos passaram | Alto / backend + auditor | Fechado para o alvo. Manifesto não é assinado; manter somente backups confiáveis. |
| PERF-01 — latência síncrona do PIN | PBKDF2 600k dentro da transação de escrita e do fluxo modal síncrono; primitiva mediu 378–410 ms (mediana 392 ms) nesta máquina | Médio / backend + frontend | Medir autenticação GTK real; avaliar execução fora do lock e da thread GTK preservando serialização do cooldown e estado CAS. Sem correção aprovada ainda. |
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
| I18N-01 — PT-BR/EN-US em toda a interface | Implementação de fonte integrada: os catálogos têm 1.735 IDs iguais, preferência GSettings PT-BR padrão, atualização ao vivo em Settings/Workspace/Sticky Notes/YouTube/widgets/diálogos e mensagens de erro Orbitz já abertas. Metadados de erro preservam classe e args; texto externo e conteúdo do usuário não são inferidos por correspondência. Suíte Python consolidada após as correções de locale e rollback: 428 casos aprovados, 4 skips ambientais; 36 scripts Node passaram. | Médio / frontend + backend + supervisor | Usuário informou em 22/10 que aplicou a atualização e que aparentemente tudo funciona; smoke manual positivo registrado, sem ampliar isso para QA visual independente. Instalação e inspeção gráfica desta revisão seguem pendentes. |
| CFG-01 — Configure e atualização dos elementos do conversor | `Adw.SwitchRow` ausente em libadwaita 1.1 abortava a construção da página; substituído por `Gtk.Switch`/`Adw.ActionRow`. Foi corrigida também a corrida em que o callback do catálogo substituía `ElementAdded` antes do debounce do Shell: marcadores estruturais pendentes são mesclados e a topologia armazenada é comparada à árvore ativa. Teste executa Configure → janela → subpáginas e adicionar elemento → callback assíncrono → atualização do Shell, cobrindo Fiat + Crypto, edição simples e exclusão. | Médio / frontend | Testes de fonte passaram; instalar e conferir visualmente no GNOME; usuário confirma que os dois elementos aparecem e Configure/remover funcionam. |
| WX-01 — modal de previsão do tempo e localização | Na fonte: sete colunas de mesma largura sem rolagem horizontal, ícones por condição (inclui vento forte), C/F, refresh manual, unidade/local persistidos, busca única com até dez resultados Cidade · Região · País via Open-Meteo/GeoNames. Vento máximo diário validado em km/h; 40 km/h seleciona ícone de vento, tempestades conservam prioridade. Salvar unidade dispara nova execução imediata do resumo sem alterar intervalo normal. Testes WX: 24 Python, teste do painel com 740/1034 px e 36 scripts Node passam. | Médio / backend + frontend + supervisor | Busca live, instalação e validação visual GNOME pendentes; a suíte consolidada passa, com 4 skips ambientais. Auditoria independente concluída; consultar parecer e pendências desta sprint. |
| STICKY-04 — seletor de emoji e exclusão de notas | UI transfere o emoji picker para diálogo transitório focado; menu remove arquivar/restaurar e adiciona exclusão; drop na lixeira inferior apaga SQLite por ID/revisão. Arquivadas legadas continuam visíveis como notas normais. Exclusão purga o mesmo ID dos backups retidos antes do commit ativo, falhando fechada se não for possível. Testes: 47 Sticky (45 pass, 2 skips por falta de display), I18N 6/6, domínio 11/11, `py_compile`, JSON e diff-check aprovados; dois casos adversariais corrigidos. | Alto / backend + frontend + supervisor; auditor independente | Reauditoria aprovada para `update-local.py --apply`; depois smoke GTK/instalação. Limitação: promoção de vários snapshots não é atomicamente agrupada; em falha parcial a nota ativa permanece e retry completa. A revisão não certifica isolamento contra ator do mesmo UID. Wayland nativo não oferece coordenada global de hit-test; menu “Delete note” permanece disponível. |
| STICKY-05 — menu no cabeçalho e gesto alternativo para lixeira | Frontend removeu o arraste do cabeçalho, substituiu os três pontos por botão dropdown que compartilha as ações do clique direito e oculta tooltips enquanto aberto. A lixeira é mantida por Shift+arraste na margem inferior vazia; Delete note permanece no menu. 23 testes direcionados: 21 passaram e 2 smokes GTK foram ignorados sem display; compilação, catálogos e diff-check passaram. | Médio / frontend | Aplicar e validar interação visual na sessão GNOME; auditoria média agrupada no fechamento da sprint. Em Wayland nativo, usar Delete note no menu. |
| STICKY-06 — PIN de interface e notas secretas | Backend e frontend implementaram PIN global de quatro dígitos, hash/salt, cooldown após cinco tentativas, flag por nota, autenticação para revelar/desmarcar/excluir, bloqueio automático após 15 s fora da janela e Settings primeiro no menu. Usuário escolheu explicitamente não criptografar conteúdo; Settings avisa que DB/backups continuam legíveis. Testes integrados 84 Sticky (82 passaram, 2 skips GTK) + idioma 6/6; compilação e diff-check passaram. | Alto / backend + frontend + supervisor + auditor | Auditoria focada concluída sem bypass reproduzível (41 casos do alvo); apto para aplicação local. Teste visual GTK pendente. Limite: bloqueio só na UI; tentativa offline do PIN e acesso direto aos arquivos continuam fora da proteção. |
| RC-42 — título editável, cursor do drop e legado arquivado | Implementado: migração de title aditiva/CAS, Entry editável com placeholder localizado e limite de 200 caracteres, cursor pointer no alvo; exclusão de archived=1 em snapshots legados/atuais. WAL válido é checkpointado e normalizado antes do purge; locks/symlinks/invalid DB continuam falhando fechados. Testes Sticky 55 (53 pass, 2 skips GTK), I18N 6/6, domínio 11/11, sintaxe/JSON/diff-check passam. Migração/WAL concorrentes testados em 16 inicializações; auditoria focada aprovada. Causa real da captura não confirmada; teste usa dados sintéticos. | Alto / backend + frontend + supervisor; auditor independente | Apto para `update-local.py --apply`. Smoke GTK/instalação pendentes. |

## Cadastro de próxima tarefa

Uma linha por mudança: ID, escopo/arquivos, risco, responsável, critérios, evidência/testes e estado da revisão. Estados: planejada, em desenvolvimento, testes locais aprovados, auditoria pendente, revisada ou impedida. Para alto risco indicar operação bloqueada até revisão focada; para risco médio manter na fila de fechamento, sem ocultar pendência ao usuário.

## Fechamento do lote

1. Congelar alvo/diff e reunir testes/evidências dos responsáveis.
2. Acionar auditor uma vez para mudanças pendentes e integração; não repetir itens já revistos sem mudança.
3. Corrigir impeditivos e verificar somente o que foi afetado, ampliando se necessário.
4. Supervisor atualiza estados, limites, comando de atualização e roteiro de teste. Publicação segue autorização do usuário e revisões exigidas; nenhuma é disparada automaticamente.

## WX-01 — verificações locais (22/10/2026)

24 testes nos arquivos `test_weather.py` e `test_weather_locations.py` passaram, cobrindo °F no resumo em execuções futuras, busca/GeoNames sem CSC, CAS, limites, preservação de preferências e vento diário em km/h com atualização do cache; `test_weather_panel.js` verifica sete colunas e ausência de rolagem em viewports de 740 e 1034 px, ícones por condição/vento e prioridade de tempestade; `test_panel_language.js` e os 36 scripts Node passaram, além de compilação Python e `git diff --check`. Na suíte Python consolidada após correções: 428 testes passaram e 4 foram pulados por restrições ambientais; os dois testes de idioma que falhavam agora verificam PT e EN explicitamente. Busca live, instalação e inspeção visual GNOME pendentes.

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

## RC-43 — Input GNOME e Sticky Notes

Validado pelo usuário em 22/10/2026: cliques voltaram a funcionar e Sticky Notes abriram após aplicação. Fechado para a sessão testada; eventual falha interna em `grab.dismiss()` não foi reproduzida.

## RC-44 — Renderização de Sticky Notes

Fechado após o usuário confirmar que as notas abriram sem o bloco cinza e que conseguiu excluir as notas parasitas arquivadas.

## RC-45 — Placeholder do título de Sticky Notes

Implementado na fonte como label traduzível sobreposto ao entry, com forwarding de eventos e nome acessível. 19 testes direcionados: 17 passaram, 2 smokes GTK ignorados por falta de display; sintaxe/JSON/diff-check aprovados. Pendência: aplicar e confirmar visualmente na sessão do usuário.

## RC-46 — Menu e gesto alternativo da lixeira (22/10/2026)

Implementado pela equipe frontend com consulta focada de Design/UX: remover a área de arraste do cabeçalho; substituir os três pontos por dropdown com as ações do clique direito; suprimir tooltips durante a abertura do menu; preservar exclusão pela lixeira com Shift+arraste exclusivamente pela margem inferior vazia, mantendo “Delete note” no menu. 23 testes direcionados: 21 aprovados e 2 smokes GTK pulados por ausência de display; `py_compile`, catálogos JSON e `git diff --check` passaram. A aplicação e o teste visual/gestual do usuário estão pendentes. GTK Wayland nativo mostra a limitação e orienta a exclusão pelo menu. Revisão independente média será consolidada no fechamento da sprint.
