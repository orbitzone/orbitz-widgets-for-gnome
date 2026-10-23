# Auditoria focada — Secret Notes / PIN da interface

Data: 22/10/2026  
Alvo: delta `STICKY-06 / RC-47` no checkout Orbitz.  
Revisor: auditor independente do projeto.  
Escopo: `sticky-notes/storage.py`, `sticky-notes/card.py`, `sticky-notes/postits.py`, catálogos PT-BR/EN-US e testes de PIN/UI/backup.

## Resultado

Nenhum bypass reproduzível foi encontrado nas rotas de desbloqueio, remoção da marca secreta, exclusão autenticada, comparação de revisão (CAS), cooldown ou timer de relock. A purga de backups falha fechada; os casos testados incluem sidecars WAL, symlink, falha parcial e retry. A UI e a mensagem de Settings informam que o PIN bloqueia somente a interface e que texto/título permanecem sem criptografia no SQLite e nos backups, de acordo com a escolha explícita do usuário.

## Verificações independentes

`python3 -m unittest tests.test_sticky_storage_pin tests.test_sticky_secret_ui tests.test_sticky_storage_delete -v`: 41 testes aprovados. Os cenários usam bancos temporários/fakes e não leem dados pessoais nem instalação ativa. Não houve correções pelo auditor.

## Limites

A auditoria não comprova a interação GTK/accessibility em sessão gráfica, a instalação local nem proteção contra acesso direto aos arquivos, tentativa offline contra o hash do PIN ou processo local com acesso aos dados. Dois smokes GTK automatizados do conjunto integrado foram ignorados por falta de display. Revisão limitada ao delta acima; não substitui auditoria geral do repositório.
