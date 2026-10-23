# Auditoria consolidada de fechamento — mudanças desde 21/10/2026

Data: 22/10/2026  
Revisor: auditor independente do projeto.

## Alvo e método

Alvo versionado: commits `dfea56a` (21/10/2026 04:14 -03:00) e `8b42557` (21/10/2026 17:49 -03:00), na linha de `main`. Alvo local: todo o diff não commitado contra `HEAD` (`git diff --stat HEAD`: 127 arquivos rastreados alterados), mais os novos arquivos não rastreados mostrados por `git status --short`. O checkout compartilhado não oferece uma base separada por data; portanto, mudanças locais são identificadas como estado atual, sem presumir que cada uma começou em 21/10.

Segui `docs/agents/workflow.md`, `docs/agents/auditor.md` e `docs/sprint-backlog.md`: reuso do parecer inalterado de Secret Notes em [2026-10-22-secret-note-pin-review.md](2026-10-22-secret-note-pin-review.md); leitura dirigida das áreas de alto risco (atualizador/rollback, armazenamento e backups, credenciais, invoices/assinaturas, preferências meteorológicas e persistência), além dos contratos de I18N, FX, calendário, painéis GJS e relógio mundial. Não editei código nem documentação de produto.

## Achado reproduzível

### AUD-01 — Rollback aceita destinos arbitrários do manifesto

**Severidade: média (P2); requer correção antes de usar rollback com pastas de backup não confiáveis.** Em [tools/update-local.py](/home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome/tools/update-local.py:359), `restore()` valida identidade/schema do manifesto e links simbólicos, mas não limita `files[].target` às raízes de instalação Orbitz nem confina `files[].backup` à pasta do backup. `identity_from_manifest()` restringe apenas identidade e schema da extensão.

Reprodução segura feita em diretório temporário: um manifesto com identidade/schema válidos apontou `target` para um arquivo temporário fora da instalação, e `backup` para um arquivo dentro da pasta de rollback. `restore()` retornou `ROLLBACK_OK` e substituiu o conteúdo do destino pelo backup. Assim, quem executar `tools/update-local.py --rollback` sobre uma pasta adulterada pode sobrescrever arquivos graváveis do usuário; com `backup: null`, também pode remover o destino. O fluxo normal `--apply` calcula destinos a partir das raízes configuradas e não reproduziu esse comportamento.

Critério de correção: validar o formato e cada entrada do manifesto antes de alterar Settings; aceitar somente destinos e caminhos-fonte esperados sob as raízes Orbitz da identidade ativa; exigir que cada caminho de backup seja relativo, sem `..`, e permaneça dentro da pasta de rollback. Acrescentar regressões para alvo fora da lista permitida e backup absoluto/atravessando diretórios; ambos devem recusar antes de chamar `gsettings` ou alterar qualquer arquivo.

### Correção local e validação dirigida (22/10/2026)

Backend aplicou validação integral do manifesto antes do preflight/Settings: formato, tipos e hashes, duplicatas, `source` correspondente ao `target` permitido, raízes da identidade ativa e backup relativo/canônico contido no diretório. `--force` não contorna a validação. Adicionados oito casos em `tests/test_local_update_manifest.py` e ajustadas fixtures existentes para caminhos de instalação válidos. Teste dirigido: `python3 -m unittest discover -s tests -p 'test_local_update*.py' -v` — 26 testes aprovados; cobre alvos externos (inclusive `backup: null`), fontes incompatíveis, backup absoluto/traversal, recusa antes de settings/mutação, `--force` e rollbacks legítimos de código, notas, ambas identidades e schema. `py_compile` e `git diff --check` passaram. O Auditor revalidou esse alvo e confirmou o fechamento sem bypass relevante no escopo. Risco restante: manifesto não assinado; usar somente pasta de rollback confiável. A correção não foi aplicada à instalação.

## Resultado dos demais riscos e verificações

Não encontrei outro defeito reproduzível nas rotas examinadas de integridade de invoices/assinaturas, backup/restauração do Workspace, armazenamento de credenciais no Secret Service, CAS/prefs de clima, FX ou fluxo de relógio mundial. Os casos direcionados existentes cobriram rejeição de entradas, conflito, rollback e respostas assíncronas obsoletas. Para Sticky Notes / RC-47, o alvo permaneceu igual ao parecer focado: 41 testes em fixtures passaram e nenhum bypass foi reproduzido. Isso não confirma proteção contra leitura direta do SQLite/backups, que o produto declara não oferecer.

Integração executada uma vez antes da inclusão dos oito testes de AUD-01: `python3 -m unittest discover -s tests -v` — 420 casos, 414 passaram, 4 foram ignorados por falta de display/sockets e 2 falharam em expectativas de idioma. As falhas são `test_manage_builtin_uses_toggle_and_never_disconnect` (espera rótulos PT-BR enquanto recebeu “Disable”) e `test_validator_never_changes_local_status_and_display_never_claims_validity` (espera “Imported — validation pending” enquanto recebeu a versão PT-BR). Não reproduzi falha funcional nesses fluxos; o frontend está tornando as expectativas independentes do locale ativo. Os oito novos testes de AUD-01 passaram na suíte dirigida do atualizador (26/26); a suíte global não foi repetida após esses deltas.

Após os ajustes focados de locale e AUD-01, o supervisor executou `GSETTINGS_BACKEND=memory python3 -m unittest discover -s tests -v`: 428 casos passaram e 4 foram ignorados por restrições ambientais, sem falhas. Os 36 scripts `tests/*.js` passaram com Node na validação de integração; o delta posterior alterou somente testes Python e documentação. Os dois testes de locale verificam agora PT-BR e EN-US e restauram o idioma de entrada.

Os 36 scripts `tests/*.js` foram executados uma vez com Node.js; todos passaram. O contexto de fechamento recebido também registra `py_compile`, `node --check` dos pontos de entrada e `git diff --check` aprovados. O inventário informado pelo supervisor confirma 1.735 IDs nos dois catálogos, sem chaves exclusivas.

## Pendências e limites

Na revisão inicial havia contagens desatualizadas em documentos internos (1.705 IDs e 360–420 casos, conforme o marco citado). O supervisor atualizou as páginas de estado para 1.735 IDs e o último resultado integrado, 428 pass/4 skips; o trecho histórico abaixo preserva o resultado do primeiro teste integrado para auditoria.

Sem instalação/aplicação, GTK/GNOME/ATK reais, busca meteorológica online ou teste com serviços externos; os testes de sockets e alguns smokes gráficos foram ignorados. O supervisor mediu apenas a primitiva PBKDF2 (600 mil iterações) em sete amostras locais: mediana 392 ms, faixa 378–410 ms. Como o código a executa sincronicamente durante uma transação do PIN, isso indica uma pausa potencial durante autenticação/alteração do PIN, mas não mede a resposta do modal nem certifica responsividade real do GNOME; registrado como PERF-01. Não medi uso de memória ou atualização prolongada. Fixtures ficaram em diretórios temporários; não li bancos pessoais, credenciais ou dados da instalação ativa. A ausência de outros achados reproduzíveis vale apenas para o alvo e a evidência descritos acima.
