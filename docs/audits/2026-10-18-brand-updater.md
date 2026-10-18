# BRAND01 — atualização reversível de logo e metadata

Data: 18/10/2026. Estado: backend estável, validado em temporários; auditoria independente/aplicação/revisão visual pendentes.

## Alterações e contrato

Alterados somente `tools/update-local.py` e `tests/test_local_update.py`. A seleção de arquivos mantém `.py/.js/.html` próprios e acrescenta whitelist estrita de dois caminhos relativos à raiz `extension/`:

- `metadata.json`;
- `media/orbitz-logo.svg`.

Não inclui outros SVGs, JSONs arbitrários, configurações pessoais, arquivos em vendor, binários ou XML/schema. Nenhuma mudança em `migrate-identity.py`. Seleção de identidade continua preferindo diretório Orbitz novo válido; fonte com UUID/schema incompatíveis com destino é recusada antes da cópia. Schema ausente na fonte agora também é recusado explicitamente, sem assumir o schema esperado.

`atomic_copy()` valida novamente UUID/schema para o alvo raiz `EXT/metadata.json`, usando os mesmos bytes que serão gravados. Isso protege também a fronteira de cópia caso metadata mude entre seleção e cópia, além da revalidação de hashes já existente. Nenhuma mudança de identidade/schema é feita por BRAND01.

SVG inexistente no destino e metadata alterado entram no manifesto/hash/backup de atualização normal. Manifestos continuam associados a extensão/schema; backups DEP01 antigos seguem tratados como legado. Rollback remove o asset criado e restaura exatamente os bytes anteriores do metadata, preservando as proteções anteriores contra backups corrompidos e alterações posteriores.

## Evidência

`python3 -m unittest discover -s tests -p test_local_update.py -v`: **9/9 aprovados** (sete anteriores e dois novos).

Novos cenários usam somente diretórios temporários e GSettings simulado:

1. Instalação nova sintética; fonte inclui metadata com `version-name: 1.0` e logo ausente no destino. Confirma whitelist exata (exclui `youtube.json`, `notes.json`, metadata aninhado, outro SVG, vendor e binários), aplica de fato com `main --apply`, valida bytes/hashes/manifesto da identidade nova, confirma plano posterior vazio e executa rollback removendo SVG/restaurando metadata original.
2. Cópia de metadata recusa UUID diferente, schema diferente e schema ausente sem modificar destino.

A expectativa da fixture anterior de seleção de identidade foi atualizada para fornecer schema explícito, conforme o contrato estrito. Nenhuma expectativa foi removida/enfraquecida.

## Limites e próximos responsáveis

Sem instalação, GSettings real, elevação, recarga de sessão, commit/push ou publicação. Nenhum desenho de logo ou arquivo frontend foi editado pelo backend. Fontes finais de `media/orbitz-logo.svg`, About e `metadata.json` são responsabilidade frontend; supervisor encaminha estado estável ao auditor antes de aplicação autorizada.

A verificação foi funcional da ferramenta/rollback; não é revisão visual da logo nem confirmação da versão no GNOME ativo. Abertura de preferências após aplicação deve ser explicitamente para `orbitz-widgets@orbitzone.github.io`, conforme orientação do supervisor. Não se atribui captura de Desktop Clock 7 à nova identidade instalada/ativa sem evidência.
