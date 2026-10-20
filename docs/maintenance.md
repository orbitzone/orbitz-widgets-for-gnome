# Manutenção e contexto técnico

Atualizado em 19/10/2026. O README principal é a apresentação pública do produto; este índice concentra manutenção, evidências e contexto de desenvolvimento, sem dados pessoais ou credenciais.

## Fontes de verdade

- [Contexto atual](project-context.md): mapa dirigido de componentes, último alvo e limitações de instalação.
- [Requisitos](requirements.md), [backlog](backlog.md), [decisões](decisions.md) e [fila de sprint](sprint-backlog.md): escopo, critérios e estado verificável.
- [Stack](../stack.md): plataforma, dependências e mapa técnico. Seus caminhos históricos não devem ser confundidos com os destinos atuais.
- [Instruções do projeto](../AGENTS.md) e [fluxo de trabalho](agents/workflow.md): propriedade de arquivos e verificações proporcionais. Documentação não representa monitoramento contínuo.

## Evidências recentes

- [Workspace](audits/2026-10-19-workspace-audit.md):169 testes Python; integração temporária de contexto/fatura/versão/pagamento/backup/restauração. QA PDF do supervisor é separada da interação GTK.
- [Calendários](audits/2026-10-19-calendar-audit.md):27 testes de calendário e8 do planner aprovados,2 skips de socket; teste Node de identidade e integração temporária. OAuth, cofre, contas e GTK reais continuam pendentes.
- [Invoices e assinatura assistida](audits/2026-10-19-invoice-signatures-audit.md):62 testes dirigidos no alvo daquele marco. Não é resultado da suíte global atual, nem assinatura validada.

Não repetir testes amplos ou transformar contagens históricas em execução atual. Ao publicar, conferir diff e hashes das fontes afetadas contra o relatório pertinente. Instalação/ativação e validação visual devem ter evidências próprias; alterações no repositório não atualizam a instalação.

## Operação e preservação

[Atualização local](operations/local-update.md), [migração de identidade](operations/identity-migration.md) e [integrações](operations/calendar-integrations.md). UUID atual: `orbitz-widgets@orbitzone.github.io`; schema `org.gnome.shell.extensions.orbitz-widgets`. Instalação legada preservada para retorno, sem executar ambas identidades. Não apagar caminhos históricos nem copiar credenciais/configuração pessoal para o repositório.

Workspace: encerrar/reabrir após atualização Python. Resumos do worker: parar/abrir widgets pelo controlador para recompilar coletores. Preferências antigas podem manter conteúdo legado aberto; abrir explicitamente o UUID novo. Não inferir falha de migração somente por uma captura da janela antiga, nem exigir logout para toda atualização.

Dados do Workspace ficam no diretório de dados local do aplicativo; cofre, calendários externos, SQLite das Sticky Notes e GSettings não pertencem ao backup completo do Workspace. Acervo/perfis são privados. Preservar IDs, gravação atômica, locks, backups e independência das fontes externas. As limitações de RAM/externos estão no backlog; não foram resolvidas por mudanças de invoices ou calendário.

## Verificações de desenvolvimento

```bash
python3 -m unittest discover -s tests -v
node tests/<arquivo>.js
git diff --check
```

Executar testes GJS com a raiz do repositório conforme cada script. Não instalar, reiniciar GNOME, publicar ou acessar acervo real por uma alteração documental.

O [README anterior](archive/2026-10-19-readme-internal.md) foi preservado como histórico dos marcos, resultados e caminhos locais. Contém estados de datas diferentes e instruções ultrapassadas: consultar apenas quando necessário e conferir as fontes atuais antes de operar. Não tratar seus planos antigos ou caminhos da identidade legada como estado instalado atual.

## Referência editorial do README

A apresentação pública prioriza benefícios, recursos, adoção, privacidade e limitações que afetam o uso. Coordenação, resultados de testes, caminhos históricos e estado de aplicação ficam neste índice e em `project-context.md`, sem referências ao ambiente de desenvolvimento no README.

Detalhes de faturamento para manutenção: cancelar a emissão não grava alterações dos perfis; moeda e idioma são independentes; referências de projeto/departamento não substituem os dados fiscais do destinatário. Ver domínio e interface em `extension/planner/invoice*.py`. A versão pública resumida não altera esses contratos.
