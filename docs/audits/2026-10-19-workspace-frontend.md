# WSP-01 — frontend — 19/10/2026

**Estável para a única auditoria integrada coordenada pelo supervisor; validação GTK pendente.** Lote completo implementado, sem instalação, sessão ativa, dados reais, publicação ou acionamento automático de UX/auditor.

## Entrega

- **Orbitz Workspace**, subtítulo “Agenda, tarefas, horas e faturamento”. Stack/Switcher com Hoje, Agenda, Tarefas, Horas e Invoices. Contexto/data explícitos; Horas conserva notebook de timesheets/reordenação e botão criar mesmo sem nenhuma sheet. Invoices incorpora o conteúdo funcional do histórico existente e gerar PDF, sem limitar a área a atalhos de menu. Callbacks de eventos→tarefa, tarefa→horas, consultar vínculos e arquivadas foram redirecionados às áreas corretas.
- Hoje resume compromissos **em cache da fonte selecionada**, pendentes de hoje/total, atrasadas e cronômetros. Não se declara sincronização independente ou ausência de compromissos fora desse cache.
- Contexto criar/editar: nome obrigatório; cliente/destinatário de trabalho, contrato/projeto e departamento/centro de custo opcionais. Horas/contexto visíveis. Destinatário fiscal da invoice permanece separado; prefill do nome do cliente só quando não há perfil salvo. Contexto acompanha prévia/snapshot/PDF via backend, sem reinterpretar invoices antigas.
- Possível duplicidade consultada na prévia e novamente **antes do writer**. Horas sobrepostas/conferência incompleta exigem confirmação explícita de reemissão/correção intencional; não substituem invoices anteriores nem marcam horas automaticamente. Proteção IH-A02 contra destino gerenciado mantida.
- Pagamento manual na invoice: não informado/informado como pago, com confirmação específica de registro/cliente/emissão/total. Estado separado de PDF/metadados imutáveis e assinatura; não é conciliação bancária ou validação criptográfica.
- Menu global: arquivadas, exportar/restaurar backup completo, restauração legada da agenda e preferências de área inicial. Período em um calendário, versões/assinatura assistida/histórico continuam nos componentes existentes. UUID/schema GNOME não alterados.

## Backup/restauração

UI confirma abrangência e privacidade: tarefas/notas legadas, timesheets/contextos, backups anteriores da agenda, perfis, invoices/versões/pagamentos e estado de interface. Exclui credenciais, calendários externos, Sticky Notes e GSettings. Choosers com confirmação de substituição; backend define whitelist, valida ZIP/limites/hashes e recusa timers.

Rascunhos são persistidos **antes de inspect** e seus timers pendentes removidos. Confirmação usa token CAS da prévia (arquivo + dados atuais). Cancelar não chama restore/quiesce. Após confirmar, interrompem-se escritores/timers e aguarda-se executor externo; páginas passam a readonly **antes** de cleanup, impedindo autosave antigo. Sem iterar mainloop durante restore. Backend recebe confirmed/expected/quiescent; ao final, inclusive erro, Workspace fecha para reabrir do disco. Destroy/switch-page não regravam estado restaurado. Backend confirmou que execução coesa no processo quiescente é adequada, sem requisito adicional de subprocesso.

Não se garante exclusividade sobre processos independentes: API backend mantém locks/CAS/recusa de concorrência; UI orienta fechar outros editores. Restauração cria backup privado prévio e backend trata recuperação/rollback. Nenhuma restauração real foi executada pelo frontend.

## Arquivos e contratos

Novos helpers: `workspace_ui.py`, `timesheet_context_ui.py`, `workspace_backup_ui.py`. Integrações em `calendar-app.py`, `planner_menu.py`, `timesheet_ui.py`, `invoice_ui.py`, `invoice_history_ui.py`; ajustes finos de roteamento em `external_ui.py` e `task_timesheet_ui.py`; textos de lançamento/erro em `calendar.js`. Calendário MonthCalendar da agenda permanece intocado. `create_history_content` permite usar o mesmo histórico embutido e em diálogo.

APIs backend alinhadas: sheet_create/sheet_update e contexto canônico client_name/project_contract/department_costcenter; profiles.load(context=...); snapshot opcional context/source_entries; possible_duplicates; invoice_payments.get/set_paid; workspace_backup.export/inspect/restore. Frontend não editou domínio, renderer, storage ou ferramentas deploy.

## Verificações proporcionais

- `python3 -m unittest discover -s tests -p test_workspace_frontend.py -v`: **5/5**. Inclui inicialização/navegação das cinco áreas com widgets sintéticos, conteúdo Invoices/geração, rotas de data/contexto, Hours vazio/criação; resumo/contexto readonly; prefill/perfil fiscal preservado e pagamento REAL temporário sem mudar PDF/metadados; reemissão explícita; flush/quiesce sem writeback, cancel/timer/falha de shutdown não chamam restore e token CAS exato.
- `test_invoice_frontend.py`: **6/6**, menu atualizado e exportação/perfis/ReportLab; hooks de histórico isolados.
- `test_invoice_history_frontend.py`: **9/9**, incluindo IH-A02 e acervo temporário. Mocks atualizados com duplicate-check explícito, sem acesso ao histórico real.
- AST/whitespace: **13 arquivos Python afetados** aprovados; `node --check calendar.js` e diff-check dos rastreados aprovados. Uma linha vazia herdada com espaços em external_ui foi limpa.

Total **20 testes frontend afetados** aprovados. Sem suíte global ou nova QA/renderização de PDF pelo frontend. Backend informou evidências próprias do lote; supervisor centraliza QA PDF e uma auditoria final. Warning de dependência load_module já conhecido não foi alterado.

## Revisão básica e limites

Padrões nativos GTK, rolagem na navegação/formulários/listas, wrap por caractere para contextos longos, nomes acessíveis/callbacks existentes preservados, destinatário fiscal e estado manual rotulados. Testes com widgets sintéticos não comprovam pixels, foco, AT, DPI ou diálogos nativos. Não houve nova tentativa gráfica bloqueada nem parecer UX automático. Não se declara produto integralmente validado antes da auditoria de dados/backup.

Supervisor recebe fontes estáveis, consolida documentação/comando de atualização conforme RC-17 e aciona **uma auditoria integrada** antes de liberar. Instalação pendente; não orientar reinício por mera alteração do checkout. RAM/EXT/branding fora deste lote.
