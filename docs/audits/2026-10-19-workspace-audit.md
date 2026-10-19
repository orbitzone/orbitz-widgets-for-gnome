# WSP-01 — auditoria integrada — 19/10/2026

**Parecer:** sem impeditivo reproduzido no escopo auditado; funcional local/integridade aprovados. GTK/AT/choosers reais e instalação permanecem pendentes. Nenhuma revisão estética adicional, dado pessoal, sessão ativa, instalação ou renderização duplicada.

**Alvo:** HEAD `d5d8aae14711ebf33da9fd13a1673b1558a966d5` + alterações locais estáveis. Manifesto de código/schemas/tests SHA-256 `9803e3cef8ab4e44ef995094f28cdb10cf4bae273e757f983b61f29c73a369f5`; nenhuma mudança durante a auditoria. Backup: `a4310ceeea230bfa03483dbc8c63e04ffb0c042e90b44a887ac98e21d538dbd4`.

**Execução:** `/usr/bin/python3 -m unittest discover -s tests -v`, com PYTHONDONTWRITEBYTECODE=1: **169/169**,10,874s. Logs completos: `/tmp/orbitz-workspace-audit/python-full.log`; manifesto/logs auxiliares no mesmo diretório. AST de todos os módulos planner, `node --check extension/planner/calendar.js` e `git diff --check` aprovados. JS alterou somente textos de lançamento/erro; não justificou repetir testes Node de lógica intacta.

**Integração adicional real temporária:** criar contexto/horas→snapshot8h×125,50=1004,00→histórico→versãoPDFsintética/pagamento→backup→mutar→restaurar. Whitelist restaurada byte a byte; IDs, horas, destinatário fiscal separado, contexto, versão e pagamento preservados; inode invoices/.lock estável; PDFs externos e sentinelas credenciais/calendários/SQLite/fora-whitelist intactos.

**Revisão:** ZIP trava nomes/hash/limites/contagem/razão/links; valida antes de mutar. Restore exige confirmação/quiescência/CAS, locks estáveis e pré-backup/journal; testes de falha/interrupção/paresPDFincompletos e rollback preservam edições posteriores detectadas. UI flush antes da prévia, readonly antes de cleanup, executor/timers encerrados e sem writeback após restore; cancelamento não restaura. Cinco áreas/Hojecache, callbacks tarefa/evento↔horas, sheet selecionada, prefill somente sem perfil e confirmação de reemissão conferidos. Duplicidade usa união de intervalos e ID+tempo; pagamento é relato manual separado, sem alterar PDFs/versões/metadados. Legados sem extras continuam válidos.

**Limites:** mocks não certificam foco/pixels/GTK; hashes não autenticam origem; locks/CAS não controlam escritores externos não cooperantes nem garantem corte físico de energia. QA PDF PT/EN quatro páginas/1004,00 pertence ao supervisor e não foi repetida. Sem benchmark, validação bancária/fiscal/criptográfica. RAM/EXT separados.

Supervisor integra aceite/documentação e comando de atualização autorizado; auditor não aplicou. Após aplicação verificada, reabrir Workspace; teste manual deve incluir navegação/contexto/preview/cancelamento e backup em dados descartáveis. Nenhum logout GNOME demonstrado necessário.
