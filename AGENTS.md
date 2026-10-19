# Orbitz Widgets — instruções do projeto

## Contexto

Este repositório é a fonte de desenvolvimento do Orbitz Widgets for GNOME. Leia `README.md` e `stack.md` conforme o componente da tarefa. Código: `extension/` (GJS e aplicativos da agenda/YouTube), `widgets/` (coletores Python) e `sticky-notes/` (GTK/SQLite).

A instalação local ainda referencia pastas históricas do Codex e arquivos em `~/.local/share`. Modificar o repositório não atualiza automaticamente os aplicativos instalados. Não mova nem apague arquivos históricos necessários à execução. Não copie dados pessoais ou credenciais para o repositório.

## Coordenação

Fluxo vigente e econômico (19/10/2026): consulte `docs/agents/workflow.md` e `docs/sprint-backlog.md`. Auditoria independente de risco médio é agrupada no fechamento de sprint; alto risco exige revisão focada antes da operação. UX fica sob demanda, sem acionamento automático por tarefa. Esta política prevalece sobre rotinas históricas. Leia o contexto atual e somente arquivos pertinentes, sem carregar todo o histórico.

O papel persistente de documentação, análise de requisitos, Product Owner, gestão e liderança técnica está definido em `docs/agents/project-owner.md`. Esse documento é um contrato de responsabilidades; não representa um processo em execução contínua.

- O usuário decide objetivos, prioridades comerciais e mudanças de escopo. O agente transforma pedidos em requisitos verificáveis e propõe prioridades técnicas, sem inventar aprovações.
- Registre requisitos e critérios de aceite em `docs/requirements.md`, prioridades e pendências em `docs/backlog.md` e decisões relevantes em `docs/decisions.md`. Crie ou amplie os arquivos quando houver conteúdo concreto; evite duplicar o README.
- Diferencie comportamento observado, requisito confirmado, proposta e trabalho validado. Um pedido sem evidência de teste não equivale a entrega aprovada.
- O README é a apresentação pública do produto, com linguagem comercial e foco no usuário, sem referências ao Codex ou contexto interno. Sua manutenção é responsabilidade permanente do analista de requisitos/supervisor, conforme `docs/agents/project-owner.md`; contexto técnico e evidências ficam em `docs/maintenance.md` e documentos internos.
- Ao alterar comportamento, atualize a documentação afetada na mesma entrega. Para correções simples, não exija um processo burocrático ou aprovação adicional.

## Trabalho e validação

Preserve dados históricos, gravações atômicas, backups, cofre de credenciais e independência de tarefas/timesheets em relação aos calendários externos. Preserve créditos e licenças, inclusive das bibliotecas em `extension/planner/vendor/`.

Execute verificações proporcionais à mudança. A suíte Python é `python3 -m unittest discover -s tests -v`; testes JavaScript individuais são executados com `node tests/<arquivo>.js`. Consulte `docs/maintenance.md` e as evidências históricas referenciadas para as três falhas conhecidas na publicação inicial. Não remova expectativas ou enfraqueça testes apenas para obter aprovação.

Não edite dependências vendorizadas sem necessidade demonstrada. Não recarregue a sessão GNOME, altere a instalação ativa ou publique no GitHub apenas por estar atualizando documentação; siga o escopo autorizado pelo usuário. No relatório, diga o que mudou, o que foi verificado e quais limites permanecem.

## Equipe autorizada em 18/10/2026

Consulte `docs/agents/team.md` e somente o contrato do papel acionado (`backend.md`, `frontend.md`, `auditor.md` ou `designer-ux.md`). Este chat de requisitos supervisiona entregas e atualiza documentação ao receber os relatórios. Backend e frontend alinham contratos diretamente, mantendo o supervisor informado. A comunicação supervisor/backend/frontend/auditor foi autorizada pelo usuário. Design/UX atua exclusivamente com frontend; frontend repassa conclusões ao supervisor. Respeite a propriedade dos arquivos e o fluxo de auditoria; não implica monitoramento contínuo.

As regras vigentes de autonomia, comunicação crítica, conclusão e economia de contexto ficam em `docs/agents/team.md` e `docs/agents/workflow.md`. Especialistas podem investigar o necessário e tomar decisões técnicas dentro do escopo sem aprovações rotineiras. Auditor mantém verificação independente; validações funcional, visual e de segurança são distintas.
