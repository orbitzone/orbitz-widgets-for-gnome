# WSP-01 — lote backend consolidado

19/10/2026. Estado estável para integração e **uma auditoria final** de dados/backup/cálculo; nenhuma instalação/restauração real, publicação ou commit.

## Entrega e APIs alinhadas com frontend

- `sheet_context.py`: contexto opcional validado `client_name`, `project_contract`, `department_costcenter`, strings de até 200 caracteres; nome obrigatório da timesheet, até 80. `timesheet.py`/`store.py`: `sheet_create{name,context?}`, novo `sheet_update{sheet_id,name?,context?}`; `sheet_rename` continua compatível. Contexto não altera IDs/horas e leitura de dados antigos não insere campos nem os regrava.
- `invoice_profiles.load(sheet_id,path=None,context=None)`: preenche apenas nome do cliente quando **não existe perfil salvo** para a sheet. Perfil fiscal guardado nunca é substituído pelo contexto.
- `invoice.py`/`invoice_pdf.py`: snapshots novos podem conter `context` e `source_entries[{id,date,start,end}]`; versões 1 antigas sem extras continuam válidas, inclusive no histórico/versões. Contexto é separado do destinatário fiscal, com labels PT/EN e XML escapado. Cálculo Decimal/rounding anterior preservado.
- `invoice_duplicates.check(snapshot,root=None)` e wrapper `invoice_history.possible_duplicates`: `{matches:[{id,reference,minutes,basis}],warnings:[],incomplete:bool}`. Compara união dos intervalos efetivamente faturados na mesma sheet; não usa somente período/referência, não duplica contagem de sobreposições. Vínculo por ID só é declarado quando também há sobreposição temporal daquele ID. Legados sem proveniência e registros indisponíveis geram ressalva explícita. Exclusões não entram; valores monetários arredondados a zero não anulam minutos reais. Aviso não bloqueia reemissão nem marca horas automaticamente.
- `invoice_payments.get(id)` / `set_paid(id,bool)`; wrappers history `get_payment` / `set_payment(id,'not_reported'|'reported_paid')`. Retorno `{status,updated_at}`. Estado manual em `payment.json` privado separado, sob lock do acervo; original PDF/metadata e versões/assinaturas não são alterados. Default “Não informado”; valor positivo é apenas “Informado como pago”, não verificação bancária.

Alterados seis módulos existentes: timesheet/store/invoice/invoice_pdf/invoice_history/invoice_profiles. Quatro novos helpers coesos acima. Sem alterações em renderer de assinatura, UI/frontend, vendor ou ferramentas de instalação.

## Backup completo restrito ao aplicativo

`workspace_backup.py`:

- `export_backup(path,overwrite=False,data_dir=None) -> Path`.
- `inspect_backup(path,data_dir=None) -> {token,sha256,files,bytes,scope,current_active_timer}`.
- `restore_backup(path,confirmed=True,expected=preview['token'],quiescent=True,data_dir=None) -> {restored,previous_backup}`.
- `rollback_restore(recovery_folder,confirmed=True,quiescent=True,data_dir=None)` permite recuperar interrupção, inclusive par PDF/metadata parcialmente restaurado. Não exige nova tela; API para recuperação operacional.

Whitelist: notes.json (tarefas/horas), invoice-profiles.json, planner-ui.json, planner-backups/*.json, PDFs/metadata originais e versões em invoices e payment.json manual. Exclui cofre/credenciais, calendários externos, Sticky Notes SQLite, GSettings, executáveis e demais arquivos. Conteúdo desconhecido não é lido/substituído/removido. Export é arquivo ZIP privado `0600`, manifesto versionado com SHA-256/tamanhos. SHA verifica integridade, não autenticidade de origem.

Limites: até 10.000 arquivos, 512 MiB descomprimidos totais, PDF individual 128 MiB; notes/backup histórico 64 MiB, perfil 2 MiB, UI 8 MiB, metadata 4 MiB e pagamento 32 KiB. Export usa ZIP_STORED. Import recusa traversal, membros duplicados/fora da whitelist, symlink/especial/encriptado, excesso de contagem/tamanho/diretório central e razão de compressão suspeita. Todos os membros são validados antes da mutação. JSON/modelos/hashes de invoices e versões também são conferidos.

Locks estáveis `notes.json.lock`, `invoice-profiles.json.lock`, `planner-ui.json.lock`, `invoices/.lock`, além do lock do próprio backup. Aquisição não bloqueante recusa operação concorrente. **Não renomeia nem substitui a raiz invoices ou seu .lock**: inode confirmado por teste. Preview pode criar infraestrutura de lock/diretório vazio, sem alterar conteúdo dos dados. Token vincula hash do backup e fingerprint atual da whitelist; mudanças desde a prévia exigem nova revisão. Cronômetro ativo atual ou no backup impede exportação/restauração. Arquivo danificado impede a operação de forma conservadora, sem sobrescrita automática.

Frontend confirmou flush de drafts antes de inspect; depois de confirmação deixa timesheets readonly, encerra executor/sincronização/timers, executa restore sem iterar mainloop e fecha a aplicação mesmo em erro, sem regravar UI antiga. `quiescent=True` confirma esse procedimento; não prova que processos externos não cooperantes estejam fechados. Backend mantém locks/CAS e checagens por arquivo, mas não alega transação global contra terceiros que ignorem locks.

Antes de aplicar, cria backup privado integral anterior e journal em `data_dir/workspace-backups/<id>/` (pasta 0700, arquivos 0600), fora da whitelist restaurada. Aplicação por arquivo atômico privado; falha ordinária reverte bytes anteriores, removendo apenas arquivos criados pelo restore. Edições posteriores incompatíveis são preservadas e ficam pendentes. `rollback_restore` usa hashes before/after para retomar interrupção sem confiar em pares temporariamente incompletos; recusa mudanças posteriores desconhecidas. Backup anterior também pode ser selecionado em uma nova prévia/restauração explícita. Não há garantia integral contra corte físico de energia ou escritores que ignorem os locks.

## Verificação

53 testes específicos aprovados, sem suíte global durante mutações frontend:

| Seleção unittest | Resultado |
|---|---|
| test_workspace_domain.py | 7/7 |
| test_workspace_backup.py | 9/9 |
| test_planner_backend.py | 8/8 |
| test_invoice_history.py | 11/11 |
| test_invoice_signatures.py | 10/10 |
| test_invoice_backend.py -k InvoiceDomainTests | 5/5 |
| test_invoice_backend.py -k InvoiceProfileTests | 3/3 |

Dez sintaxes backend aprovadas. Novos testes verificam criação/update sem perder IDs/horas, contextos/fiscal distintos, prefill somente sem perfil, snapshots legados, labels/escape PT/EN por extração, minutos duplicados reais/legados/corrompidos/excluídos/zero monetário, pagamento sem mudar documentos, backup completo com versões/pagamento, roundtrip e uso do pré-backup, lock inode estável, consentimento/quiescência/CAS, timers/lock ocupado, falha injetada com igualdade byte a byte, interrupção de invoice parcialmente aplicada e recuperação, preservação de mudanças posteriores, hash/traversal/symlink/zipbomb/limites e arquivos fora da whitelist. Nenhum teste anterior foi enfraquecido.

Fixtures sintéticas e diretórios temporários; store recebe path explícito (não depende de patch no default DATA capturado). PDF skill já lida e marker cumprido na primeira autoria desta conversa. Teste PDF faz geração/extração específica, sem duplicar renders/QA visual: supervisor revisou PT/EN 2 páginas cada, contexto longo/fiscal distinto/acentos/XML e 8h × 125,50 = 1004,00; evidência visual/hashes sob sua responsabilidade em work/workspace-pdf-qa. Nenhuma alteração de layout posterior foi feita pelo backend.

## Próximo responsável

Frontend conclui navegação/integração e testes próprios; supervisor integra documentação e encaminha **uma rodada final** ao auditor antes de qualquer aplicação real, dado o risco de dados/backup/monetário. Não foi solicitado aceite fiscal, bancário ou criptográfico, não há marcação automática de horas nem consulta a serviços externos. Nenhum acervo pessoal foi consultado ou restaurado.
