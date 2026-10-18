# Revisão direcionada — atualização local reversível — 18/10/2026

Estado: **uso ainda não recomendado; impeditivos de recuperação/migração pendentes**. Revisão independente do script operacional, sem modificar código ou instalação. RF-01 anterior não foi reaberta.

## Alvo e método

`tools/update-local.py`, não rastreado, sobre HEAD `2a24e0d6875063cfee9412b1c9545181f999d3ad`. O script mudou durante a inspeção: a primeira versão restaurava todos os destinos em qualquer exceção; a versão capturada posteriormente adicionou lista `attempted`, revalidação de old_hash e preservação de conflitos. **Não atribuir à versão atual a ausência dessas proteções já acrescentadas.** Snapshot revisado em `/tmp/orbitz-update-local-reviewed.py`, SHA-256 `9f1928333c2e512af62403acd89e8511e0233ffcad7be060488ff22943d80084`. Mudanças posteriores exigem nova verificação afetada; esta não é aprovação de arquivo mutável sem identidade.

Inspeção por `cat`, `nl -ba`, `git status --short`, `sha256sum`; `ast.parse` aprovado. Testes com Python padrão, `importlib.util.spec_from_file_location`, `tempfile.TemporaryDirectory`, `unittest.mock.patch` e GLib.Variant, importando o módulo sem executar main. Somente dados sintéticos. Não executado `--apply`, preflight real, GSettings real, rollback real ou leitura de dados/credenciais pessoais; nenhum acesso gravável fora dos temporários e deste relatório. Não houve tentativa de contornar sandbox/Broadway nem reload GNOME. Contagem informada 49 arquivos/10 comandos pertence ao plano do supervisor e não foi reproduzida com configurações pessoais pelo auditor.

## Achados impeditivos

### LU-01 — rollback aceita backup corrompido e anuncia sucesso — P1, reproduzido

Alvo: `restore`, linhas 112–132 do snapshot, e restauração no except, 206–207. O manifesto contém old_hash, mas o conteúdo do backup não é validado antes de sobrescrever o destino; não há verificação final do hash restaurado. Uma cópia truncada/alterada pode substituir código funcional e produzir ROLLBACK_OK.

Reprodução sintética: criar destino com bytes `new`, backup `files/0` com `corrupted backup`; manifesto com new_hash=SHA256(new), old_hash=SHA256(old), old_settings=old e new_settings=new. Mock de settings retorna new e aceita set para old. Chamar apenas `restore(folder)` temporário, sem main/preflight/instalação. Resultado:

```text
ROLLBACK_OK — saia e entre na sessão para carregar os arquivos restaurados.
CORRUPT BACKUP RESTORED: corrupted backup expected old
```

Aceite: validar todos os backups contra old_hash antes de qualquer mutação de arquivos/configuração; recusar ausência/corrupção; verificar estado final e não anunciar rollback completo após recuperação parcial. A captura de backup também deve garantir coerência entre os bytes copiados e old_hash, evitando leitura do destino em instantes diferentes como fonte da prova.

### LU-02 — falha GSettings pode impedir recuperação de código — P1, risco fundamentado no fluxo

Alvo: except, linhas 196–209. `settings('get', ...)` e eventual set ocorrem antes da restauração dos arquivos e sem isolamento próprio de falha. Se o backend GSettings falhar após uma cópia parcial (ou falhar justamente ao provocar a exceção inicial), a nova exceção abandona o laço de recuperação. Não foi necessário provocar falha na instalação real para identificar esse caminho; não apresentado como incidente já ocorrido.

Aceite: recuperação de arquivos precisa ser tentada independentemente do sucesso da consulta/restauração GSettings; acumular e reportar falhas por recurso, preservar conflito concorrente e manter instrução de recuperação utilizável. Não alegar reversão completa se um recurso falhar. O rollback explícito também deve registrar claramente recuperação parcial se uma operação falhar.

### LU-03 — migração altera caminho embutido em outro token — P2, reproduzido

Alvo: migrate, linhas 37–56. A expressão verifica limite à direita, mas não à esquerda; qualquer ocorrência do caminho conhecido é substituída mesmo se fizer parte de outro argumento/caminho. Não satisfaz a restrição de migrar apenas Text_Command conhecido por token exato.

Reprodução sintética: REPO temporário com widgets/a.py, OLD_DIRS temporário, COLLECTORS temporário; Variant aaa{ss} com `Text_Command='echo prefix'+str(OLD_DIRS[0]/'a.py')`. Resultado: count=1 e texto vira `echo prefix<collectors>/a.py`; o argumento original não era o caminho conhecido. Casos normais sem flags, com espaço/--details e aspas foram migrados; sufixos x/2 não foram migrados. A existência de limite direito foi confirmada e não é defeito.

Aceite: reconhecer token de caminho exato em comando suportado, incluindo aspas, sem reescrever argumento embutido, literal de código ou string arbitrária. Definir conservadoramente formatos autorizados; desconhecido deve permanecer inalterado e ser relatado para revisão. Não reconstruir shell arbitrário com perda de aspas/semântica.

## Demais observações e cobertura

- **Atomicidade por arquivo aprovada localmente:** atomic_copy usa temporário no diretório destino, flush/fsync, replace e fsync de diretório. Teste com replace lançando OSError preservou `old` e removeu temporário; cópia normal produziu `new` e preservou modo sintético 0640. Atomicidade individual não significa transação dos 49 arquivos/GSettings.
- **Backup privado:** caminho padrão fora do repositório; mkdtemp privado, files 0700 e manifesto 0600. Não contém leitura intencional de notas/tarefas/cofre; old/new_settings armazenam widget-data operacional e devem continuar privados, pois comandos podem conter conteúdo sensível. Backup/manifesto não recebem fsync e manifesto não é gravado atomicamente: recuperação após crash/queda de energia não foi comprovada. Para anunciar reversibilidade durável, persistir/verificar backup e manifesto antes da primeira mutação. Risco de confiabilidade, não perda já reproduzida.
- **Concorrência:** snapshot atual verifica hash do destino imediatamente antes de cada cópia e recupera só attempted, preservando arquivo posterior com hash estranho. Melhora concretamente o fluxo anterior; ainda há janela check→replace e não há lock que serialize duas instâncias do atualizador. GSettings get→set também não é CAS; mudanças simultâneas podem ser sobrescritas nessa janela. Restringir/quiescer escritores e serializar atualizadores, ou declarar o limite e detectar conflitos nas fronteiras possíveis. Não se promete transação global com outros aplicativos não cooperantes.
- **Symlinks:** files rejeita symlink do arquivo e preflight checa apenas um nível de diretório. Teste temporário mostrou atomic_copy(source, linked_parent/file) gravando no diretório apontado pelo ancestral simbólico. Não comprova ataque na instalação real nem escape de sandbox, mas a proteção anunciada não cobre ancestrais (inclusive panels/planner). Verificar a cadeia dos destinos/backup conforme política pretendida; não seguir caminhos inesperados silenciosamente.
- **Escopo:** whitelist por extensão copia todos os arquivos próprios Python/JS/HTML divergentes, não apenas um manifesto fixo RF-01; exclui vendor/__pycache__ e não migra banco/JSON pessoal. Nova versão deve manter plano explícito e incluir dependências novas juntas. Não tocar arquivos históricos. Aplicativos em execução podem continuar com módulos antigos; não declarar código carregado na sessão atual ou validação gráfica a partir da cópia.

## Conclusão e próximo responsável

Não executar instalação com base nesta revisão até resolver LU-01, LU-02 e LU-03 e encaminhar hash estável para nova verificação proporcional. Impeditivos comunicados prontamente ao supervisor; não foram feitas correções pelo auditor. Supervisor é responsável pelo script e pela decisão de operação após correção; o sandbox pode impedir a instalação e não deve ser contornado.

Funcional operacional: testes temporários parciais com dois defeitos reproduzidos; não aprovado. Integridade/recuperação: pendente pelos achados acima. Visual/GNOME: não executado e não aplicável ao script em si; prontidão de sessão carregada não confirmada. Desempenho: não medido. RF-01 anterior permanece com suas conclusões delimitadas.

## Rechecagem dirigida — segunda versão estável

Alvo script SHA-256 `13ebd23f70fb425fb2634a5cfee207ce84d799abb675fd7356f848df6ac96e5c`; testes `tests/test_local_update.py` SHA-256 `1906e82693405aad0a05a2560c597c52e8fbb6b6c19f2c5c7da906abf07770b5`. Supervisor declarou congelamento durante esta revisão. Comando `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_local_update.py -v`: **4/4 aprovados**, 0,109 s. Esses testes chamam main com argv sintético --apply, mas destinos/BACKUPS/preflight/GSettings são temporários ou mocks; nenhuma instalação real foi executada. Esta autorização de teste não significa executar --apply real.

**LU-01 corrigido no cenário reproduzido:** backup validado antes de mutação, adulteração rejeitada, resultado de rollback explícito conferido por hash. Backup capturado agora é comparado ao old_hash antes de qualquer instalação. **LU-02 corrigido no cenário GSettings:** teste independente com três arquivos sintéticos, terceiro atomic_copy falhando, settings(get) passando a lançar RuntimeError: mensagem RECUPERACAO_CONFIG_PENDENTE emitida e todos destinos retornaram a old. **LU-03 corrigido no cenário reproduzido:** limite esquerdo rejeita prefix+old_path; testes incluem campos não relacionados, sufixo e idempotência. Não é parser geral de shell e não se afirma reconhecimento de toda sintaxe possível.

Backups/manifesto recebem fsync de arquivo nesta versão. Ainda não se prova durabilidade de entradas de diretórios após falha de energia (fsync dos diretórios de backup não acrescentado). Limites de concorrência e ancestrais simbólicos anteriores continuam explícitos; sem constatação de exploração ou mutação na instalação real.

### LU-04 — falha de recuperação de um arquivo abandona os demais — P1, reproduzido em temporários

O except de apply isola GSettings, mas o laço reversed(attempted) ainda não isola falhas de digest/atomic_copy/unlink por item. Reprodução independente: três pares source/target temporários com new/old; mock atomic_copy copia os dois primeiros e lança OSError no terceiro; quando a recuperação alcança backup files/1, lança OSError('recovery copy fail'). Todos os demais acessos e diretórios são temporários e preflight/settings são mocks.

```text
Sem falha adicional de recovery: targets = ['old', 'old', 'old']
Com falha adicional de recovery: targets = ['new', 'new', 'old']
Erro final: OSError recovery copy fail
```

O primeiro destino poderia ser restaurado, mas não é tentado; erro inicial apply fail é mascarado e não há diagnóstico RECUPERACAO_CODIGO_PENDENTE para cada recurso incompleto. Critério: tentar recuperação dos demais arquivos independentemente; acumular falhas por destino; preservar causa original e indicar explicitamente estado parcial/backup para intervenção, sem anunciar sucesso. Não é requisito de garantir sucesso de um filesystem quebrado; é não abandonar recuperações independentes possíveis.

LU-01/02/03 anteriores não permanecem abertos para esses cenários corrigidos. **LU-04 impede recomendação final do fluxo de recuperação nesta versão.** Encaminhado prontamente ao supervisor com resultado exato. Nenhum código foi corrigido pelo auditor e nenhuma suíte global foi repetida.

## Parecer após correção LU-04 — terceiro alvo estável

Script SHA-256 `2ced0620876bf34ac7c13255816a77b502e825530e71923a436be41fd6055fbd`; teste SHA-256 `475ee27bca9eb965e0d5df85dd313b44f0e8070b2e1bd7cd0f54b05b27a53e09`. Hashes iguais antes/depois da revisão. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_local_update.py -v`: **5/5 aprovados**, 0,199 s. `ast.parse` nos dois arquivos: aprovado. Nenhuma suíte global repetida e nenhuma alteração de produção pelo auditor.

LU-04 **corrigido e verificado**: recuperação agora isola erro de cada arquivo e continua; bare raise preserva a falha original de apply; verificação de hash por item identifica recuperação divergente. Testes independentes adicionais com tempdir/mocks:

1. Falha na terceira cópia + GSettings indisponível durante recuperação + falha ao restaurar files/1: resultado `old/new/old`; erro final continua `apply fail`; ambas mensagens RECUPERACAO_CONFIG_PENDENTE e RECUPERACAO_CODIGO_PENDENTE presentes; ATUALIZACAO_OK ausente. O destino0 é recuperado apesar da falha no destino1.
2. Rollback explícito sintético, backup válido, falha no arquivo1: destinos0/2 recuperados, resultado `old/new/old`; RuntimeError Rollback incompleto emitido; mensagem de pendência presente e ROLLBACK_OK ausente.

**Conclusão vigente:** LU-01 a LU-04 resolvidos nos cenários auditados; nenhum impeditivo reproduzido permanece nesses quatro pontos. O fluxo operacional está apto no escopo dos testes sintéticos e com os limites já registrados. Isso não é prova de instalação efetuada, transação global contra escritores não cooperantes, durabilidade integral após corte de energia ou validação gráfica. Concorrência residual, ancestrais simbólicos e fsync de diretório dos backups permanecem limites registrados, sem exploração ou perda constatada no alvo real. Não ampliar esta aprovação a segurança integral do produto.

Supervisor informou preflight real bloqueado por Errno30 antes de mutação; auditor não repetiu operação real, não contornou sandbox e não executou --apply na instalação. Próximo responsável: supervisor comunica ao usuário a distinção entre script revisado e atualização ainda não aplicada, e decide eventual execução em terminal autorizado respeitando permissões. O aceite visual pendente de RF-01 continua independente.
