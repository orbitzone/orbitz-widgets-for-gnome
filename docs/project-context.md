# Contexto atual do Orbitz

Atualizado em 20/10/2026. Índice operacional, não histórico completo nem promessa de memória infalível. Conferir código/diff/instalação conforme a tarefa; não carregar todo o arquivo histórico por padrão.

## Processo vigente

[Equipe](agents/team.md), [fluxo econômico](agents/workflow.md), [fila de sprint](sprint-backlog.md). Auditoria média no fechamento; alto risco antes da operação. UX sob demanda; frontend faz a revisão básica. Testes afetados continuam com o desenvolvedor. Supervisor conclui com comando de atualização quando há código e orientação de reabertura/reinício.

## Produto e limites

- Orbitz Widgets for GNOME, Felipe Santiago/orbitzone; UUID `orbitz-widgets@orbitzone.github.io`, schema `org.gnome.shell.extensions.orbitz-widgets`, versão exibida 1.0. Repositório https://github.com/orbitzone/orbitz-widgets-for-gnome.
- Ubuntu 22.04/GNOME 42.9 local; manifesto declara GNOME 42–44, sem validação abrangente dessas versões. Instalação legada preservada/desativada para retorno; créditos/licenças e gettext de compatibilidade preservados.
- Fonte no repositório não atualiza instalação automaticamente. `tools/update-local.py` faz plano/aplicação reversível; `tools/migrate-identity.py` separa preparo da ativação. Aplicação real precisa evidência. Não mover/apagar pastas históricas nem dados pessoais.
- Agenda/timesheets locais independentes de calendários externos; Secret Service para credenciais; notas SQLite/WAL. Preservar backups, locks e gravações atômicas.

## Mapa para leitura dirigida

| Área | Fonte |
|---|---|
| Apresentação pública | `README.md` — benefícios, uso, compatibilidade e limites relevantes ao usuário |
| Manutenção, evidências e dependências | `docs/maintenance.md`, `stack.md` |
| Requisitos/decisões | `docs/requirements.md`, `docs/decisions.md` — buscar pelo ID da tarefa |
| Prioridades de produto | `docs/backlog.md`; fila de revisão em `docs/sprint-backlog.md` |
| Shell/preferências | `extension/extension.js`, `panels/`, `settings/`, `prefs.js` |
| Agenda UI/domínio | `extension/planner/calendar-app.py`, `*_ui.py`, `store.py`, `timesheet.py`, `ui_state.py` |
| Fontes externas e alertas | `external_store.py`, `apple_client.py`, `ics_client.py`, `calendar.js`, `reminders.js` |
| Invoice e histórico | `invoice.py`, `invoice_pdf.py`, `invoice_profiles.py`, `invoice_history.py`, `invoice_signatures.py` e respectivos UI |
| Coletores/notas/YouTube | `widgets/`, `sticky-notes/`, `extension/youtube-widget/` |

## Lote atual

Os marcos CAL abaixo preservam evidências de cada entrega; esta seção resume o estado mais recente e prevalece sobre pendências históricas dos marcos.

CAL-07/RC-29: Brasil · Datas comemorativas padrão, permanente, reativável e persistente.31 testes dirigidos+regressão externa aprovados; usuário confirmou a fonte funcionando na instalação atual em 20/10. Persistência do ciclo desativar→reabrir→reativar ainda sem confirmação explícita; revisão média segue agrupada na fila.

CAL-06/RC-28: projeção de eventos, feriados de outras fontes e atividades locais na Agenda; link opcional para ativação da Calendar API.18 testes dirigidos aprovados. Usuário confirmou Google Calendar funcionando na instalação atual em 20/10; validação limitada ao fluxo/conta usados, sem estender ao Calendly ou todas as contas. Revisão média agrupada na fila.

CAL-05/RC-27: causa client_secret ausente confirmada por probe oficial com código fictício; configuração privada matching fornecida pelo mantenedor preparada e conferida, arquivo0600/dir0700. [Revisão](audits/2026-10-19-google-client-config-audit.md):35pass/2skips/6 adversos/6hashes. Login real foi confirmado pelo usuário posteriormente em CAL-06. Setup privado desta instalação não é release público universal.

CAL-04/RC-26: usuário reportou callback recebido, Orbitz aguardando/botãoinativo, zeroGoogleaccountssalvos. Defeito BrokenPipe reproduzido e corrigido (estado validado antes de resposta); progresso por4chaves e erros OAuth sanitizados. Backend25pass+2skips efrontend11pass. [Revisão focada concluída](audits/2026-10-19-google-callback-audit.md):36 testes aprovados/2skips e8 adversos;6hashes conferidos. Plano4arquivos/0comandos, sem aplicação. Não afirmar causa única real/cofre/API ou login concluído.

CAL-03/RC-25: usuário forneceu ClientIDpúblico do Orbitz; login normal passa a Entrar com Google semJSON/CloudUI. Backend21pass+2skips ambientais efrontend9pass; [revisão focada concluída](audits/2026-10-19-google-login-audit.md),30 testes aprovados/2skips. Plano2arquivos/0comandos, sem aplicação. Guia distingue configuração do mantenedor de login do usuário. CAL-02 abaixo é histórico substituído nesse fluxo.

CAL-02/RC-24: diálogo Google guiado, links de preparo e validação local do JSON implementados; nove testes frontend aprovados. Plano1arquivo/0comandos; GUI/aplicação pendentes, revisão média na fila. Backend/auth/cofre CAL-01 não alterados.

CAL-01/RC-22: Google Calendar (OAuth desktop leitura) e Calendly (PAT pessoal leitura) implementados nas fontes; [auditoria focada de credenciais concluída](audits/2026-10-19-calendar-audit.md), sem impeditivo reproduzido.35 testes dirigidos aprovados e2skips de socket real; Nodeidentity aprovado. O usuário confirmou Google Calendar funcionando em 20/10; Calendly ainda não foi confirmado com conta real. Pré-requisitos e diagnóstico About no [guia](operations/calendar-integrations.md). Não sobrescrever o legado.

WSP-01 implementado e auditado: [parecer integrado](audits/2026-10-19-workspace-audit.md), 169/169 Python e restauração temporária aprovados; PDFPT/EN inspecionado. Essa evidência pertence ao alvo WSP; não equivale a GUI/autenticação dos provedores novos.

FX-01 conversor fiat: usuário confirmou que o widget apareceu após aplicar cinco arquivos (`ATUALIZACAO_OK`); saída só com par e valor está instalada (hash igual à fonte), sem arquivos pendentes naquele momento. Backend chama apenas endpoint latest Frankfurter, sem cache, histórico, timer backend ou fallback; 12 testes FX passam. Frontend implementou na fonte polling de 4h, modal acionável no widget com atualização manual/inversão persistida e formatador que trunca a saída para 2 casas (exemplo `0.19829 → 0.19`). Valores abaixo de `0.01` exibem `0.00`; isso não serve a cripto de baixa unidade sem precisão própria. Modal, cadência e precisão ainda não foram instaladas nem verificadas em GTK/GNOME real. README e backlog atualizados. Requisitos cripto USD↔ativo selecionável continuam pendentes, conforme `docs/requirements.md` e `docs/backlog.md`. WID-02 relógio mundial permanece não resolvido conforme relato do usuário; não tratar tentativa local como aceite.

## Último estado verificado das fontes

- Refatoração modular, identidade Orbitz e marca 1.0 implementadas. Usuário confirmou em 20/10 que o clique RAM não é mais um problema; BUG-01 encerrado por observação manual. Diferenças de dispositivos externos/alertas permanecem pendência separada (BUG-02).
- INV-01–04: invoice PT/EN por timesheet, períodos em calendário único, histórico privado por empresa/cliente/mês de emissão, versões importadas e assinatura gov.br assistida.
- Evidência anterior desse conjunto: 62 testes de invoices aprovados e seis hashes conferidos no [parecer INV-04](audits/2026-10-19-invoice-signatures-audit.md). É teste dirigido, não nova suíte global nem execução gráfica real.
- Original e versões preservados; portais abertos só por ação do usuário, upload/login manuais. Importação/hash não validam assinatura ou correspondência; estado pendente. IH-A01/02 corrigidos no histórico: corrupção isolada e guarda de destino gerenciado.
- GTK/AT/chooser/browser real de invoices/assinatura permanecem testes manuais separados. O usuário confirmou instalação funcional das integrações Google Calendar e Datas comemorativas em 20/10. Fechar/reabrir agenda após futuras atualizações Python; conferir plano/retorno do atualizador antes de afirmar instalada uma versão futura.
- Histórico/perfis privados em `~/.local/share/orbitz-widgets/`, fora do repositório; nunca usar dados reais nos testes. Histórico de invoices separado dos backups da agenda.

Histórico anterior preservado em `docs/archive/2026-10-19-agent-workflow/project-context.md`; evidências originais em `docs/audits/` e `docs/design/`. Ler somente quando a investigação exigir.
