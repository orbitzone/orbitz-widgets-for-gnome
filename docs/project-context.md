# Contexto atual do Orbitz

Atualizado em 19/10/2026. Índice operacional, não histórico completo nem promessa de memória infalível. Conferir código/diff/instalação conforme a tarefa; não carregar todo o arquivo histórico por padrão.

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

CAL-01/RC-22: Google Calendar (OAuth desktop leitura) e Calendly (PAT pessoal leitura) implementados nas fontes; [auditoria focada de credenciais concluída](audits/2026-10-19-calendar-audit.md), sem impeditivo reproduzido. 35 testes direcionados aprovados e2skips de socket real; Nodeidentity aprovado. Pré-requisitos reais e diagnóstico About em [guia](operations/calendar-integrations.md). About fonte/instaladoOrbitz conferidos1.0; captura corresponde ao conteúdo legado, gatilho janela/cache não comprovado. Não sobrescrever legado. Plano atual10arquivos/0comandos; nenhuma aplicação realizada neste lote.

WSP-01 implementado e auditado: [parecer integrado](audits/2026-10-19-workspace-audit.md), 169/169 Python e restauração temporária aprovados; PDFPT/EN inspecionado. Essa evidência pertence ao alvo WSP; não equivale a GUI/autenticação dos provedores novos.

## Último estado verificado das fontes

- Refatoração modular, identidade Orbitz e marca 1.0 implementadas; usuário confirmou CPU/SSD funcionando. RAM sem abertura reportada e diferenças de dispositivos externos/alertas continuam pendências separadas (BUG-01/02); não declaradas resolvidas pelas invoices.
- INV-01–04: invoice PT/EN por timesheet, períodos em calendário único, histórico privado por empresa/cliente/mês de emissão, versões importadas e assinatura gov.br assistida.
- Evidência anterior desse conjunto: 62 testes de invoices aprovados e seis hashes conferidos no [parecer INV-04](audits/2026-10-19-invoice-signatures-audit.md). É teste dirigido, não nova suíte global nem execução gráfica real.
- Original e versões preservados; portais abertos só por ação do usuário, upload/login manuais. Importação/hash não validam assinatura ou correspondência; estado pendente. IH-A01/02 corrigidos no histórico: corrupção isolada e guarda de destino gerenciado.
- GTK/AT/chooser/browser real permanecem testes manuais separados. Fechar/reabrir agenda após atualizar Python, sem logout obrigatório. Conferir plano/retorno do atualizador antes de afirmar instalada a última alteração.
- Histórico/perfis privados em `~/.local/share/orbitz-widgets/`, fora do repositório; nunca usar dados reais nos testes. Histórico de invoices separado dos backups da agenda.

Histórico anterior preservado em `docs/archive/2026-10-19-agent-workflow/project-context.md`; evidências originais em `docs/audits/` e `docs/design/`. Ler somente quando a investigação exigir.
