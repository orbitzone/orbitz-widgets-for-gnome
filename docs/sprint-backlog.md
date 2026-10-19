# Fila de sprint e revisões

Atualizado em 19/10/2026. Lote lógico, sem agenda automática. Política: [workflow](agents/workflow.md). Prioridades de produto continuam em [backlog](backlog.md).

## Estado atual

INV-01–04 já auditadas; último conjunto passou em 62 testes dirigidos. WSP-01 está implementado e auditado nas fontes; não iniciar auditoria retroativa das entregas anteriores. Conferência GTK/instalação é separada. Próximos pedidos serão agrupados abaixo antes de convocar auditoria; usuário mantém prioridades.

| Item | Estado | Risco / responsável | Próxima ação |
|---|---|---|---|
| OPS-01 — fluxo econômico | Documentação ajustada | Baixo / supervisor | Aplicar nos próximos briefs; sem auditor ou UX para esta alteração |
| INV-01–04 — conjunto atual | Auditoria local concluída | Parecer INV-04 | Reusar evidência se o alvo não mudar; não reauditar por hábito |
| Teste da agenda/histórico/versões em GTK real | Pendente manual | Frontend/usuário | Registrar resultado quando houver teste permitido, sem repetir ambiente bloqueado |
| Formato decimal PT e rótulos de timesheets homônimas | Propostas opcionais | Baixo / frontend | Priorizar com futuro lote de UI; não ativar UX/auditor agora |

## Cadastro de próxima tarefa

Uma linha por mudança: ID, escopo/arquivos, risco, responsável, critérios, evidência/testes e estado da revisão. Estados: planejada, em desenvolvimento, testes locais aprovados, auditoria pendente, revisada ou impedida. Para alto risco indicar operação bloqueada até revisão focada; para risco médio manter na fila de fechamento, sem ocultar pendência ao usuário.

## Fechamento do lote

1. Congelar alvo/diff e reunir testes/evidências dos responsáveis.
2. Acionar auditor uma vez para mudanças pendentes e integração; não repetir itens já revistos sem mudança.
3. Corrigir impeditivos e verificar somente o que foi afetado, ampliando se necessário.
4. Supervisor atualiza estados, limites, comando de atualização e roteiro de teste. Publicação segue autorização do usuário e revisões exigidas; nenhuma é disparada automaticamente.

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
