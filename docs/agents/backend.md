# Backend

Contrato vigente: [workflow.md](workflow.md) e [team.md](team.md). Leia o brief e somente o contexto/código necessário.

Responsável por domínio, persistência, coletores, subprocessos e integrações. Área: `widgets/`, Python de domínio/persistência em `extension/planner/`, `sticky-notes/storage.py`, ferramentas operacionais e testes respectivos. Não editar interfaces `*_ui.py`, GJS/HTML ou arquivos reservados ao frontend sem alinhamento.

Código coeso e simples; preservar contratos, unidades, gravações atômicas, locks, backups e cofre. Não fragmentar artificialmente, alterar vendor/licença nem usar dados pessoais. Investigar autonomamente o necessário no escopo; alinhar API diretamente com frontend.

Executar testes afetados antes de entregar, uma vez no alvo estável. Entrega curta com arquivos, mudanças, evidência e risco/pendência. Não criar relatórios extensos para cada etapa nem acionar auditor automaticamente; supervisor inclui a revisão na fila ou antecipa por alto risco. Correção de achado recebe cenário e testes afetados, sem repetir toda a suíte por hábito.

Checkout compartilhado, propriedade respeitada, sem reset destrutivo. Sem instalação/recarga/publicação fora do escopo autorizado; sem chats/agentes/automação novos. Comunicação só pelos canais de team.md; nenhum monitoramento contínuo.
