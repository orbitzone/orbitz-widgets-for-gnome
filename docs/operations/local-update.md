# Atualização local reversível RF-01

O usuário autorizou aplicar o refactor localmente e reiniciar a sessão manualmente após confirmação. O instalador não reinicia/recarrega o GNOME, não para aplicativos nem altera dados da agenda/notas/cofre.

## Identidade própria ID-01

Os passos abaixo documentam a atualização da identidade anterior. Com fontes Orbitz e instalação ainda azclock, o atualizador agora recusa sobrepor UUIDs. Preparar a [migração de identidade](identity-migration.md) antes de usar o atualizador futuro; após preparar a árvore Orbitz válida, ele identifica o destino novo. Backups antigos continuam explicitamente ligados ao schema legado. Não substituir o UUID somente renomeando pastas/metadados.

## Situação em 18/10/2026

Plano real: 49 arquivos de código e 10 comandos dos coletores. A aplicação pelo agente foi impedida antes de qualquer mudança em código instalado/GSettings: `Errno 30 Read-only file system` na sondagem prévia do diretório da extensão. O sandbox não permite gravar `~/.local/share`; não há ampliação de permissão disponível. Portanto a instalação permanece antiga e não está pronta para validar o refactor.

`tools/update-local.py` atualiza arquivos próprios `.py`, `.js` e `.html`, além da whitelist explícita de identidade da extensão (`metadata.json` e `media/orbitz-logo.svg`). O único JSON de aplicação adicional é a whitelist dos catálogos `pt-BR.json` e `en-US.json`, instalada em `~/.local/share/orbitz-widgets/i18n` junto de `ui_i18n.py`; outros JSONs/SVGs e dados pessoais não são incluídos por extensão de arquivo. Para o I18N-01, o atualizador acrescenta somente a chave `ui-language` ao schema ativo compatível, compila e valida o schema temporariamente e instala XML/compilado pelo manifesto com backup e rollback. Não substitui os demais schemas nem altera outras preferências GSettings. Vendor, binários e licenças não são sobrescritos. Coletores vão para `~/.local/share/orbitz-widgets/collectors`; apenas caminhos conhecidos no campo Text_Command são migrados, preservando demais campos e argumentos. Pastas históricas ficam intactas. Caches locais descartáveis podem ser recriados pelo novo caminho; não se trata de migração de dados pessoais.

Backup privado de código anterior e configuração widget-data em `~/Documents/Codex/work/orbitz-local-updates/<execução>/`, fora do repositório. O manifesto contém hashes e configuração local; não publicar nem copiar para o Git. Dados JSON/SQLite pessoais e credenciais não fazem parte desse backup e não são modificados.

## Execução pelo terminal do usuário

Salvar trabalhos e evitar editar preferências/arquivos enquanto a atualização acontece. A partir de qualquer diretório:

```bash
/usr/bin/python3 /home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome/tools/update-local.py
# Mostra o plano, sem alterar instalação.
/usr/bin/python3 /home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome/tools/update-local.py --apply
```

Reiniciar a sessão **somente** se terminar com `ATUALIZACAO_OK` (hashes e configuração conferidos) ou `INSTALACAO_JA_ATUAL`. Se houver `ATUALIZACAO_NAO_CONFIRMADA`, `RECUPERACAO_*` ou `CONFLITO`, interromper e fornecer o erro para análise; não presumir rollback completo ou prontidão. O processo atual pode manter código antigo em memória até sair/entrar; confirmação do instalador valida arquivos/configuração, não aparência/foco.

Após entrar: abrir e fechar widgets/notas, conferir dados existentes, agenda e tarefa→timesheet, preferências/fuso e YouTube. Não publicar segredos ou capturas de conteúdo pessoal ao reportar resultados. Validação gráfica e funcional da versão instalada ainda precisa ser registrada separadamente.

## Rollback

O instalador mostra o caminho específico do backup e o comando. Usar:

```bash
/usr/bin/python3 /home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome/tools/update-local.py --rollback /caminho/do/backup
```

Rollback confere hashes dos backups e recusa mudanças posteriores conflitantes em código/configuração; restaura arquivos anteriores e remove módulos novos da operação, sem apagar dados pessoais/pastas históricas. A opção `--force` sobrescreve mudanças posteriores e não deve ser usada sem avaliar o conflito. Após `ROLLBACK_OK`, sair/entrar manualmente para carregar o código anterior. Diretórios vazios podem permanecer.

## Evidências e limites do instalador

Cinco testes sintéticos em `tests/test_local_update.py` aprovados: migração precisa/idempotência/preservação, aplicação+rollback com rejeição de backup corrompido, recuperação de falha parcial e preflight bloqueado sem cópia. O quinto cenário verifica continuação da recuperação quando uma das restaurações falha, com pendência explícita e preservação do erro original. A revisão independente detectou problemas na versão inicial; supervisor corrigiu limites de token, validação de backup, revalidação dos destinos e recuperação mesmo com GSettings indisponível. Auditor verificou o terceiro alvo estável (SHA-256 `2ced0620876bf34ac7c13255816a77b502e825530e71923a436be41fd6055fbd`), executou os cinco testes e cenários adicionais de falha simultânea. LU-01 a LU-04 resolvidos nos cenários auditados; nenhum impeditivo reproduzido remanescente nesses pontos. Parecer em `docs/audits/2026-10-18-local-update-review.md`. Limites: não há transação global contra escritores concorrentes, nem garantia integral contra corte de energia; evitar preferências/editores durante aplicação. A instalação real permanece não aplicada por bloqueio do sandbox. Testes usam apenas diretórios temporários/configuração simulada; não comprovam aplicação real no desktop.

## Confirmação de aplicação — 18/10/2026

Usuário executou --apply fora do sandbox e recebeu ATUALIZACAO_OK. Supervisor confirmou por leitura: 49 hashes de destinos coincidem com manifesto, configuração GSettings coincide com novo valor esperado, zero diferenças de código e zero migrações restantes. Execução privada `20261018-010701-upda7txp`, com 12 arquivos anteriores copiados para backup e ausência dos novos registrada. Instalação pronta para sair/entrar manualmente; resultado visual/interativo após nova sessão ainda pendente. Essa confirmação substitui o estado anterior “não aplicada” para a execução indicada, sem apagar o registro do bloqueio inicial.

## Atualização da marca e Sobre1.0 — BRAND-01

O instalador prepara logo SVG, metadata da mesma identidade e código About em uma atualização verificável/rollback. UUID/schema fonte e destino devem coincidir. Fechar preferências antigas antes de aplicar e reabrir explicitamente com `gnome-extensions prefs orbitz-widgets@orbitzone.github.io`. A captura DesktopClock7/GitLab/PayPal corresponde à página do legado, não à fonte instalada da identidade nova já conferida. Não apagar legado/backup para resolver confusão de janela. Após confirmar ATUALIZACAO_OK, basta reabrir preferências; não orientar logout sem necessidade demonstrada.

BRAND-01 aplicada pelo usuário com ATUALIZACAO_OK, execução `20261018-021732-_vzv_1d9` (3 arquivos/0 comandos). Preferências inicialmente recusaram nova abertura por janela já existente; instruído fechar janelas antigas e abrir UUID Orbitz explicitamente. Usuário relatou aparente normalidade e revisão posterior do supervisor confirmou zero arquivos/comandos pendentes. Não exigiu reinício da sessão.
