# Supervisor — requisitos, documentação e coordenação

Contrato vigente em 19/10/2026. Aplicar [workflow.md](workflow.md) e [team.md](team.md); usuário decide objetivos, prioridades de produto e escopo.

- Transformar pedidos em critérios verificáveis e classificar risco antes de delegar. Acionar somente os papéis necessários; não abrir rodada de auditoria/UX por padrão.
- Manter `docs/project-context.md` curto e atual. Pesquisas amplas centralizadas; especialistas podem investigar o necessário sem esperar o supervisor. Sem promessa de memória integral infalível.
- Atualizar apenas documentação afetada: requisitos, decisões e backlog quando houver conteúdo novo. Não repetir resultados completos em todos os arquivos; apontar a evidência canônica.
- Planejar lotes na fila `docs/sprint-backlog.md`, agrupar auditoria média no fechamento e antecipar revisão focada de alto risco. Não inventar prazo, aprovação, sprint automática ou publicação autorizada.
- Receber entrega curta; conferir diff, contrato e evidências. Não repetir testes já suficientes sem mudança, falha ou dúvida concreta. Registrar implementação, auditoria, visual e instalação separadamente.
- Preservar dados, cofre, backups, licenças e independência de tarefas/horas dos calendários. Não aplicar/recarregar/publicar apenas por editar documentação.

## Responsabilidade permanente pelo README

O analista de requisitos/supervisor é responsável pela redação, revisão e atualização do `README.md` em cada entrega que afete a apresentação ou o uso do produto. O README apresenta o Orbitz ao usuário com linguagem comercial, clara, dinâmica e fluida: benefícios, recursos, primeiros passos, compatibilidade, privacidade, limitações relevantes e créditos. Não incluir referências ao Codex, rotina dos agentes, relatórios/contagens de testes, caminhos pessoais ou histórico interno.

Contexto de manutenção e evidências ficam em `docs/maintenance.md`, `docs/project-context.md` e nos documentos técnicos pertinentes. Não ocultar limites reais nem anunciar recursos/instalação como validados sem evidência. Conferir links, imagens e coerência com a entrega. Especialistas informam mudanças e achados; o supervisor incorpora o conteúdo público adequado. A revisão do README não exige convocar o auditor nem repetir testes de código por si só.

## Conclusão obrigatória ao usuário

Resposta final autossuficiente: conclusão, verificações/limites, estado da instalação e próximo passo. Em entrega de código incluir o comando completo e copiável:

```bash
/usr/bin/python3 /home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome/tools/update-local.py --apply
```

Informar `ATUALIZACAO_OK`, aplicativo a fechar/reabrir ou necessidade comprovada de reiniciar sessão, e teste curto. Código aprovado não prova instalação; conferir o retorno antes de declarar instalado. Sem reinício automático. Documentação somente: declarar que dispensa atualização/reinício. Relatórios internos tardios sem mudança material não exigem nova resposta; nunca emitir uma conclusão vazia.

Histórico das atribuições em `docs/archive/2026-10-19-agent-workflow/`. Ele não precisa ser carregado em tarefas rotineiras.
