# ID-01 — identidade própria e migração backend

Data: 18/10/2026. Responsável: backend. Estado: implementação estável com testes operacionais específicos; auditoria independente, preparo real, descoberta GNOME e ativação manual pendentes.

## Arquivos e decisões autorizadas

- Novo `tools/migrate-identity.py`: plano/preparo/rollback de identidade e configuração.
- Alterado `tools/update-local.py`: seleção explícita da identidade instalada e associação dos backups ao schema correto.
- Novo `tests/test_identity_migration.py`; ampliado `tests/test_local_update.py`.
- Propriedade desses arquivos transferida explicitamente pelo supervisor. Metadata/About/schema/textos JS pertencem ao frontend; documentação de produto pertence ao supervisor. Não foram alterados componentes RAM/EXT, instalação ativa, GSettings real, dados, histórico, binários no repositório ou ferramentas GNOME de ativação.

Contrato confirmado pelo frontend: UUID `orbitz-widgets@orbitzone.github.io`; schema `org.gnome.shell.extensions.orbitz-widgets`; path `/org/gnome/shell/extensions/orbitz-widgets/`. XML legado, gettext-domain e locales continuam disponíveis. Novo XML mantém chaves/tipos/defaults do legado; `DesktopSettings` também verifica ID e path ao carregar o schema.

Supervisor aprovou separar preparo e ativação: nenhum comando deste script escreve `enabled-extensions`, `disabled-extensions` ou `disable-user-extensions`. Snapshots dessas chaves são somente evidência privada. O script recusa operações se UUID novo consta em enabled-extensions, inclusive quando globalmente desativado; isso também recusa as duas identidades selecionadas. A verificação é conservadora, sem interpretar a lista como prova de execução gráfica atual.

## API/CLI

Importar os módulos não acessa desktop/configuração. `DesktopSettings` é criado apenas no CLI real; testes usam `FakeSettings`, exceto um subprocesso com backend GSettings **memory**, configurado antes de importar Gio.

- `prepare(old_directory, new_directory, source, backups, settings, apply=False)`: valida layout, manifestos, fontes, snapshots e conflitos. Plano padrão não altera instalação, configuração ou backups. Compilação para inspecionar schemas usa somente temporários.
- `--prepare`: faz backup privado, staging e cópia da configuração para o novo schema; nenhuma ativação.
- `rollback(folder, old_directory, new_directory, settings)` / `--rollback PASTA`: restaura/reset somente os valores anteriores do novo schema e remove somente a instalação nova não modificada; nunca regrava a instalação/configuração antiga.
- `--extensions-dir DIRETORIO`: local das duas identidades, padrão `~/.local/share/gnome-shell/extensions`.
- `--backup-dir DIRETORIO`: padrão `${XDG_STATE_HOME:-~/.local/state}/orbitz-widgets/identity-backups`; recusa locais dentro do repositório, fonte ou instalações. Sem `--force`.

Comandos abaixo são instruções para execução humana posterior à auditoria, não foram executados pelo agente:

```bash
/usr/bin/python3 tools/migrate-identity.py
/usr/bin/python3 tools/migrate-identity.py --prepare
/usr/bin/python3 tools/migrate-identity.py --rollback /caminho/privado/informado
```

## Instalação e integridade

Preparo exige destino novo inexistente. Recusa manifestos incompatíveis com dirname/UUID/schema, configurações novas explícitas divergentes, diferenças de chaves/tipos, links simbólicos e arquivos especiais. Configurações novas já explicitamente iguais são aceitas e seu estado anterior é preservado no backup.

Copia a árvore inteira da extensão antiga para staging irmão do destino, preservando arquivos instalados, assets, vendor e o `speedtest` existente com modo original. Aplica overlay de todos os arquivos da fonte `extension/`, incluindo metadata, XML novo/legado, assets, vendor e módulos próprios. Exclui da sobreposição `__pycache__`, `gschemas.compiled` e `speedtest`: a fonte nunca substitui o binário instalado e nenhum binário é redistribuído no repositório. Compila schemas estritamente no staging, confere hashes e publica por rename. A instalação legada permanece intacta.

O preparo não copia dados de agenda/notas/cofre nem muda os diretórios independentes de coletores/Sticky Notes. Os módulos novos de planner/UI que pertencem à extensão são incluídos pelo overlay integral. Cópias dos comandos configurados são preservadas literalmente, inclusive comandos personalizados/caminhos históricos; ID-01 não reescreve `Text_Command`. Isso mantém originais executáveis e evita migração silenciosa de comandos.

Backup privado contém snapshots completos/tipados das duas configurações, estado explícito ou default de cada chave, listas de ativação e hashes da instalação legada/preparada. Pasta `0700`, manifesto `0600`, gravação atômica com fsync. Conteúdo privado não é impresso nem copiado ao repositório. `widget-data` permanece `aaa{ss}` e `changed-data` permanece `a{ss}`; valores efetivos são escritos no schema novo sem alterar o original. Rollback restaura valor explícito anterior ou reseta quando originalmente era default.

Antes de publicar/gravar, revalida fontes, configuração e ativação; falhas recuperam os valores tentados e a árvore nova apenas quando correspondem aos estados esperados, preservando alterações posteriores. Pendências ficam registradas no manifesto. Rollback parcial usa estado `rollback-pending` e pode ser repetido; manifesto `staged`/`recovery-pending` permite recuperar preparo interrompido com configuração parcialmente aplicada. Valores que não correspondem nem ao estado anterior nem ao planejado impedem sobrescrita. Ativação nova bloqueia remoção/restauração também durante recuperação.

## Atualizador local e backups DEP01

`select_identity()` prefere diretório novo existente e válido; na ausência, detecta legado. Verifica UUID do manifesto instalado igual ao dirname e UUID da fonte igual ao destino, além do schema correspondente. Fonte Orbitz sobre diretório legado é recusada com instrução de migrar. Diretório novo inválido não faz fallback silencioso para o antigo.

O atualizador continua destinado a módulos próprios `.py/.js/.html`, notas e coletores; a migração de identidade é responsável por copiar metadata/assets/vendor/XML e compilar schemas. Não instala identidade nova por uma atualização parcial.

Manifests de atualização novos incluem `extension` e `schema`. `identity_from_manifest()` valida a combinação. **Manifests DEP01 sem esses campos sempre significam identidade/schema azclock**, mesmo se a instalação nova também existir ou o global SCHEMA já estiver no novo valor. Tanto `restore()` quanto o ramo CLI de rollback aplicam essa resolução antes de qualquer configuração. Não há inferência silenciosa para o schema novo. Os checks de hashes/conflitos/recuperação anteriores continuam disponíveis.

## Procedimento manual seguro de ativação — aprovado pelo supervisor

Preparo não confirma descoberta da nova extensão pelo Shell. Primeiro verificar:

```bash
gnome-extensions info orbitz-widgets@orbitzone.github.io
```

Se não for encontrada, sair/entrar manualmente para descoberta **mantendo a antiga habilitada**; então repetir `info`. Não desativar o legado enquanto a nova identidade não estiver descoberta/disponível. Após confirmar descoberta e ausência de erro impeditivo, a pessoa desativa a antiga, confere em `gnome-extensions info azclock@azclock.gitlab.com` e na lista de habilitadas que ela não está ativa/habilitada e só então ativa a nova:

```bash
gnome-extensions disable azclock@azclock.gitlab.com
# Verificar a antiga inativa antes do comando seguinte.
gnome-extensions enable orbitz-widgets@orbitzone.github.io
```

Confirmar depois somente a identidade nova ativa. Se o enable falhar, restaurar manualmente a antiga após conferir a nova desativada. Retorno manual: desativar nova/verificar inativa/habilitar antiga. **Rollback da ativação é separado de `--rollback` do preparo**: este exige nova já fora de enabled-extensions e não altera listas GNOME. Não há comando automático em lote para alternar identidades.

## Evidências específicas

- `python3 -m unittest discover -s tests -p test_identity_migration.py -v`: **10/10 aprovados**; repetição após normalização dos caminhos também 10/10.
- `python3 -m unittest discover -s tests -p test_local_update.py -v`: **7/7 aprovados** (cinco anteriores + seleção de identidade/mismatch e rollback legado sem schema explícito).
- `compile(source, path, 'exec')`: quatro sintaxes operacionais aprovadas.

Cenários do migrador: plano sem mutações; cópia integral/overlay/compilação real e preservação de vendor/asset/binário instalado; configuração tipada/copias personalizadas/backup privado e rollback; conflito de configuração/tipos/destino existente; ambos UUIDs habilitados; links; falha de gravação após mutação e recuperação; falha de compilação antes de publicar; rollback recusando nova ativa/arquivo/config alterados; rollback parcial registrado e repetível; preparo interrompido; Gio real carregando schemas em subprocesso `GSETTINGS_BACKEND=memory`. Todos os arquivos e configurações usados eram sintéticos/temporários. Nenhum shell live foi ativado/desativado.

## Limites e próximo responsável

Sem preparo/aplicação real, GSettings live, dconf dump pessoal, GNOME reload, commit/push ou publicação. Backend memory e mocks não comprovam integração com GNOME instalado/Secret Service; esses dados não são alvo da migração. Não há transação global com escritores externos: fechar preferências e evitar operações concorrentes durante preparo/rollback; alterações detectadas são recusadas/preservadas, mas o script não controla ações manuais simultâneas. Não se alega tolerância integral a corte de energia; backup e estado staged permitem recuperação dos cenários testados, não simulação de falha física.

Supervisor integra documentação/CLI aprovado e encaminha os quatro arquivos e schemas/frontend estáveis ao auditor. Auditor valida de forma independente antes de orientar preparo humano. Descoberta, troca manual de identidade e revisão visual/funcional da instalação são etapas posteriores distintas. Nenhum trabalho novo em RAM/EXT foi iniciado.

## Correção após auditoria — remoção parcial do rollback

Auditor reproduziu P2: `rmtree` removia um arquivo e falhava; o manifesto registrava `rollback-pending`, mas a tentativa seguinte exigia todos os hashes originais e recusava a árvore parcial. Instalação/configuração legadas permaneciam intactas, porém a retomada operacional prometida não cobria esse caso.

Corrigido em `tools/migrate-identity.py`: persistir `removal_started=True` e estado pendente antes da remoção (inclusive recuperação automática do preparo). Apenas com essa marca a validação aceita subconjunto dos hashes preparados; qualquer arquivo novo, conteúdo alterado, symlink ou arquivo especial continua recusado. Sem a marca, continua exigindo a árvore completa. A checagem de UUID novo inativo permanece antes de remoção/retomada. Não houve mudança em ativação, dados ou instalação real.

Acrescentado teste reproduzindo remoção de `helper.py` seguida de `OSError`; verifica estado/marca, recusa e preservação de arquivo novo e arquivo modificado na árvore restante, e sucesso da retomada após retirar os conflitos. Confirma configuração nova restaurada e hashes legados inalterados. `python3 -m unittest discover -s tests -p test_identity_migration.py -v`: **11/11 aprovados** após a correção. Auditor notificado para verificação independente do alvo atualizado; a reprodução anterior de 10 testes não representa validação dessa mudança pelo auditor.
