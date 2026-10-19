# Equipe e coordenação vigente

Autorização da equipe: 18/10/2026. Fluxo econômico revisado pelo usuário em 19/10/2026: [workflow.md](workflow.md) prevalece sobre os procedimentos históricos. Leia o [contexto atual](../project-context.md) e o contrato do papel; não carregar todos os relatórios anteriores.

| Papel | Chat | Responsabilidade |
|---|---|---|
| Supervisor | `01a14cdf-dbce-7990-a8db-a482e49b4975` | Requisitos, contexto, prioridades técnicas, integração e documentação |
| Backend | `01a14cfe-1021-73b2-b031-b1ae67f7687e` | Domínio, persistência, coletores e integrações |
| Frontend | `01a14cfe-1f6d-7733-b2b8-cac3d8275670` | Interfaces e integração; revisão básica de UX |
| Auditor | `01a14cfd-f9ef-7ac3-a8ed-d5f7d9a31e66` | Revisão independente no fechamento ou por risco alto |
| Design/UX | `01a14d0f-088b-7cc2-a4c3-f34f483c21a1` | Consultoria visual/experiência focada, somente sob demanda |

## Canais e autonomia

Supervisor↔backend/frontend/auditor e backend↔frontend autorizados. Auditor pode esclarecer achados indispensáveis diretamente com desenvolvedores, informando supervisor. UX comunica-se exclusivamente com frontend, que repassa a conclusão relevante. Não criar agentes/chats/automação nem ampliar canais por inferência.

Usuário define objetivos, prioridades de produto e escopo. Especialistas decidem implementação e investigam o necessário dentro do escopo; não aguardam aprovações rotineiras. Mudança de contrato incompatível, propriedade de arquivo ou escopo exige alinhamento, não aprovação fictícia por silêncio.

## Propriedade

- Supervisor: AGENTS, documentação de produto, contexto e contratos. Responsável permanente pelo README público orientado ao usuário; detalhes internos ficam em docs/maintenance.md e documentos técnicos. Especialistas reportam mudanças, sem assumir a manutenção editorial.
- Backend: `widgets/`, domínio/persistência Python, `sticky-notes/storage.py`, ferramentas operacionais e testes respectivos.
- Frontend: GJS, GTK/HTML e módulos `*_ui.py`, agenda/janelas e testes respectivos.
- Auditor: pareceres/fila de auditoria; não corrige código.
- UX: `docs/design/`; não corrige código nem altera escopo.

Delimitar arquivos no brief quando a área se sobrepuser. Checkout compartilhado: sem edições concorrentes no mesmo arquivo, resets destrutivos ou commits concorrentes. Preserve vendor, licenças, histórico e dados privados. Não aplicar instalação, recarregar GNOME ou publicar sem escopo autorizado.

## Conclusão

Implementação, teste local, revisão independente, validação gráfica e instalação têm estados distintos. Auditoria média vai para a fila de sprint; alto risco recebe revisão focada antes da operação. Comando de atualização e orientação de reabertura/reinício continuam obrigatórios na conclusão de código. Veja [workflow.md](workflow.md) e [project-owner.md](project-owner.md).

Contratos anteriores e marcos preservados em `docs/archive/2026-10-19-agent-workflow/`; não são instruções ativas. Decisões funcionais do produto permanecem em requisitos/decisões, não se perdem por esta compactação.
