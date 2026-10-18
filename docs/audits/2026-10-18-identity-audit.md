# ID-01 — auditoria dirigida de identidade — 18/10/2026

Estado desta etapa: **frontend aprovado no escopo estático/funcional local; migração backend e ativação pendentes**. Não constitui aceite integrado ID-01 ou confirmação de nova identidade descoberta/ativada no GNOME.

## Escopo e evidência independente frontend

Alvo: checkout sobre HEAD `2a24e0d6875063cfee9412b1c9545181f999d3ad`, arquivos abaixo, declarados estáveis pelo supervisor. Lidos relatório frontend `2026-10-18-identity-frontend.md`, metadata, schemas, About e docs/credits.md. Backend ainda em desenvolvimento; não executados seus scripts nem suíte global durante mutações.

```bash
node tests/test_identity.js
glib-compile-schemas --strict --dry-run extension/schemas
node --check extension/settings/AboutPage.js
node --check extension/extension.js
git diff --check -- extension/metadata.json extension/settings/AboutPage.js extension/extension.js
```

Todos aprovados. O teste executa construção About com atores sintéticos e checa metadata, autoria, URLs dos três links, crédito upstream, controles Load/Save, ausência de doação antiga e ícone genérico. Não houve janela/GTK renderizado ou rede. URLs foram verificadas como valores de contrato autorizado, sem consulta externa ou afirmação sobre conteúdo remoto.

Comparação independente Python XML: novo schema difere do legado apenas em id/path, ambos contêm **duas chaves idênticas** com textos/tipos/defaults: widget-data aaa{ss} e changed-data a{ss}. O teste Node também compara os XMLs integralmente após substituir exclusivamente id/path. XML legado comparado byte a byte com git show HEAD: intocado. Compilação strict dry-run valida coexistência sem gerar gschemas.compiled no repositório. Não se leu dconf/GSettings pessoal.

Metadata corresponde ao contrato: UUID orbitz-widgets@orbitzone.github.io, schema org.gnome.shell.extensions.orbitz-widgets, path /org/gnome/shell/extensions/orbitz-widgets/, URL GitHub Orbitz, nome próprio e versão1. gettext-domain azclock e shell-version42/43/44 preservados. Manifesto não prova compatibilidade gráfica nem descoberta instalada.

About destaca Orbitz e Felipe Santiago/orbitzone, usa símbolo genérico, conserva crédito explícito a azclock/Andrew Zaech e link upstream. docs/credits.md distingue manutenção/modificações próprias de autoria herdada e retém autores de recursos/traduções/licenças. LICENSE e extension/LICENSE comparados byte a byte ao HEAD: inalterados. Texto GPL2+ do About é preexistente; docs/credits registra arquivo GPLv3 existente. Esta revisão verifica preservação, não emite conclusão jurídica/relicenciamento nem atribui originalidade integral ao Orbitz.

Nenhum impeditivo reproduzido nesta etapa. Ícone/nome/textos não receberam aprovação de pixels, foco, dimensões ou navegação real. RAM/EXT permanecem fora do escopo e pendentes; mudança de identidade não os corrige.

## Próxima etapa backend (não executada)

Quando estável, conferir preparação/migração com dados sintéticos tipados, nova árvore/schema compilado, preservação do legado, cópia de todas chaves, conflitos sem sobrescrita silenciosa, backup/rollback e falhas parciais. Verificar que ferramentas não alteram enabled-extensions/ativação: usuário deve descobrir/verificar nova identidade antes de desativar a antiga e nunca manter ambas ativas. Nova identidade não pode ser declarada operacional somente por metadata/schema válidos. Operação real/instalação/reload não autorizados ao auditor; somente temporários/mocks.

## Hashes frontend revisados

| Arquivo | SHA-256 |
|---|---|
| `extension/metadata.json` | `047cd098268ee34ffda69a349bdf9401294debf052d876e9c2c43d91224216a0` |
| `extension/schemas/org.gnome.shell.extensions.azclock.gschema.xml` | `a628642ac736cdebaf675344f0db980eb5fa8e69a0cf3bb192733e22862460f3` |
| `extension/schemas/org.gnome.shell.extensions.orbitz-widgets.gschema.xml` | `cef22a1c31eb842bc00d957349a01a1babed2278e679f87c6a6a6deff2cb6842` |
| `extension/settings/AboutPage.js` | `49e814b12e3fdcbe63c45cc4965ac747d7068e82b040ae24dfff874d3d62a699` |
| `extension/extension.js` | `236b535243fe480ee8bdbff01ec38fd82cf2ddc670a780c9839458f7993f5ad3` |
| `tests/test_identity.js` | `6adbf7649bff8648383bada97b2caa5c4016493abfcf73168c78e5d539dce0d7` |
| `docs/credits.md` | `fdd0a3e72842204be9f546fd14a2f5a8a9eaa549a7c134379e77d6e5ba91cee1` |

## Complemento frontend — referência neutra à licença

Nova versão estável About SHA-256 `09873b387b7b77be911fdb040bf65ba6796c7d19edf87f3305ed86eae53748c2`; teste SHA-256 `6adbf7649bff8648383bada97b2caa5c4016493abfcf73168c78e5d539dce0d7`. Referência GPL2+ anteriormente descrita foi substituída por texto neutro GNU General Public License — veja LICENSE do projeto e link para o LICENSE do repositório Orbitz. Aviso sem garantia preservado. Não houve mudança no texto LICENSE nem conclusão jurídica/relicenciamento. Hash de ambos LICENSE raiz/extension permanece `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`.

Reexecuções dirigidas `node tests/test_identity.js` e `node --check extension/settings/AboutPage.js`: aprovadas. Teste exige o link e aviso sem garantia e rejeita a referência antiga version 2 or later; demais assertivas de autoria/créditos/schema/controles mantidas. Sem alteração de instalação, sem teste gráfico. Frontend permanece aprovado no escopo local; migração/ativação seguem pendentes.

## Auditoria integrada ID-01 — estado estável encaminhado

Fontes adicionais lidas: `2026-10-18-identity-backend.md`, scripts operacionais, testes de migração/updater e GTypes. Snapshot de código/metadados/schemas/testes capturado antes da suíte e comparado depois: nenhuma alteração. Sem preparo, instalação, ativação, dconf/GSettings pessoal, switch UUID ou reload. Plano real do supervisor é evidência reportada, não foi reexecutado pelo auditor; warnings dconf somente-leitura impedem tratá-lo como certificação de configuração da sessão.

### Execução integrada independente

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`: **83/83 aprovados**, 3,297 s.
- Todos `tests/test_*.js`, individualmente com Node: **18/18 arquivos aprovados**.
- `gjs tests/test_identity_gtypes.gjs "$PWD"` e `gjs tests/test_stats_pango.gjs "$PWD"`: **2/2 aprovados**.
- `glib-compile-schemas --strict --dry-run extension/schemas` e `git diff --check`: aprovados.
- ast.parse em Python próprio/testes/tools; Node --check via stdin em JS/GJS próprios/testes: **110 sintaxes aprovadas**.

GTypes: vinte registros usam nomes explícitos OrbitzWidgets únicos. Teste cria classe GObject.Object com nomes JS correspondentes para reproduzir colisão implícita e registrar os pares antigo/novo no mesmo processo. Composição/herança/alinhamento/preferências permanecem cobertos por testes Node atuais; o teste GType não instancia toda classe real St/Adw nem ativa/desativa Shell. Nomes JS/exports preservados. Proteção de nomes corrige colisão de registro reproduzida, não certifica sequência completa de migração real sem logout.

### Revisão operacional

- `DesktopSettings` compila XML copiado da instalação legada e fonte nova em temporários separados e verifica ID/path. check_contract exige conjunto de chaves/tipos compatível e parse tipado de efetivo/user; configuração nova explícita divergente impede sobrescrita. Backups preservam efetivo/tipo e distinção user/default; reset em rollback repõe ausência original. Um teste usa Gio real em subprocesso com GSETTINGS_BACKEND=memory antes do import, sem dconf pessoal.
- prepare exige destino inexistente, metadados/dirname compatíveis, fonte/ancestrais sem symlinks, rejeita arquivos especiais e backup dentro de fonte/repo/instalações. Copia árvore legada e overlay completo, com assets/vendor/schema/metadata, mantendo speedtest instalado e recusando sobreposição pelo binário fonte. Compila staging e publica por rename. Legado e seus valores permanecem intactos; comandos customizados são preservados literalmente, sem migrar Text_Command na ID-01.
- Plano não grava instalação/config/backups. --prepare não altera listas enabled/disabled/global-disable; guard recusa UUID novo presente em enabled mesmo com bloqueio global. Snapshot de listas não equivale a estado real de execução Shell. Usuário deve primeiro confirmar nova descoberta, depois desativar/verificar legado inativo e só então ativar nova, nunca ambas. Auditor não executou esses comandos.
- Revalida árvores, config e ativação antes da publicação e por chave. Recuperação preserva conflitos posteriores detectados e registra estados pendentes; não há transação global contra escritores não cooperantes. Fechar preferências/evitar concorrência é limite operacional necessário.
- Updater seleciona nova identidade válida se existente, recusa mismatch com fonte e não faz fallback de destino novo inválido para legado. Manifests DEP01 sem extension/schema são resolvidos explicitamente para azclock, mesmo com SCHEMA global novo; restore/CLI aplicam resolução antes de GSettings. Testes dirigidos dessas fronteiras passaram na suíte.
- Backup privado 0700/manifesto0600, private_json atômico com fsync arquivo/diretório; não copia notas/calendários/cofre ao repo nem altera dados locais independentes. Não se afirma tolerância integral a corte de energia ou transação durável de toda árvore/config.

### ID-A01 — repetição de rollback após remoção parcial da árvore — P2, reproduzido

Teste independente em temporários usando fixture de test_identity_migration: prepare(); patch em shutil.rmtree apenas para destino novo, remove helper.py e lança OSError('synthetic partial removal'). Primeiro rollback restaura config, grava rollback-pending e preserva legado; segundo rollback é recusado por comparação da árvore parcial com prepared_hashes integral:

```text
FIRST synthetic partial removal
STATE rollback-pending
RETRY Instalação nova mudou; rollback recusado.
LEGACY True NEW_PARTIAL True
```

Não houve perda de instalação/config legada; nenhum incidente real. O comportamento contraria a promessa ampla de rollback parcial repetível: os testes existentes comprovam repetição após falha de configuração, mas não remoção parcial de arquivos. Achado comunicado ao supervisor/backend. Critério proposto: remoção retomável deve aceitar somente subconjunto intacto e previamente registrado de arquivos em estado apropriado, recusando arquivos novos/alterados; ou usar estratégia de publicação/remoção com recuperação equivalente. Não enfraquecer comparação geral de conflito para tratar essa exceção. Enquanto sem correção, não afirmar repetição integral; manter pendência operacional explícita.

### Conclusão integrada vigente

Frontend/schema/GTypes e suíte completa aprovados no escopo local. Configuração tipada, preparação e principais guardas/recuperações passaram em memory/temp; **ID-A01 permanece pendente** neste alvo. Revisão não confirma prontidão da instalação real, descoberta/ativação, ausência absoluta de conflitos ou aparência GTK/GNOME. RAM/EXT continuam separados, desempenho não medido. Não reinstalar nem trocar identidade a partir de número de testes; supervisor integra achado e encaminha eventual correção estável para rechecagem proporcional, sem repetir suíte global sem motivo.

### Identidade do snapshot integrado

Logs brutos e manifesto completo temporários: `/tmp/orbitz-identity-audit/`. Abaixo arquivos críticos; demais fontes/testes foram comparados por hash sem alteração durante a suíte.

| Arquivo | SHA-256 |
|---|---|
| `extension/extension.js` | `d5e9ce9cd15da7240bb6da0fc540a96e0b32a4dd09d2952a84c0151448dd0d4c` |
| `extension/metadata.json` | `047cd098268ee34ffda69a349bdf9401294debf052d876e9c2c43d91224216a0` |
| `extension/prefs.js` | `984060f60d25f3dfec11019c8272bc64b35c45faedbe7e56b22c8e60575edbff` |
| `extension/schemas/org.gnome.shell.extensions.azclock.gschema.xml` | `a628642ac736cdebaf675344f0db980eb5fa8e69a0cf3bb192733e22862460f3` |
| `extension/schemas/org.gnome.shell.extensions.orbitz-widgets.gschema.xml` | `cef22a1c31eb842bc00d957349a01a1babed2278e679f87c6a6a6deff2cb6842` |
| `extension/settings/AboutPage.js` | `1bd5f6d55609726b88ebe999cf549a9c78b588784b1ffeb95dca38d7aa60345c` |
| `extension/settings/AnalogClockSubPage.js` | `1d29633427ab76015d11da6d5a7147fee1974c2bd03cf38764a534b500988914` |
| `extension/settings/CommandLabelSubPage.js` | `fc1d2a7862dd5d18d816acb4d6e437354a38cb906f8f48fe0d9f7e664ee0afff` |
| `extension/settings/DialogWindow.js` | `88ad596adedd4672e62ecca3aa5f92c848b03477f257fe3df0f8d173e2785389` |
| `extension/settings/DigitalClockSubPage.js` | `5cabd3d7c95bed5b4d70118b83a63283d8001b54d234e55b90435e7f760c82c0` |
| `extension/settings/SettingsImport.js` | `ee8c7ceebe28f346c0a0efd4e6d78639f4c413e309b297ee8f83a62f2749cf5f` |
| `extension/settings/SubPage.js` | `9747c5f20c5c4eb2f43d1c0d345532cfd1aed5fc6d589034b1fe0227a06da81c` |
| `extension/settings/TextLabelSubPage.js` | `aa98ae8d34775e48ec1b92b970d9b915f9f86b6d20e936331d26c073b01dfecc` |
| `extension/settings/TimeZoneDialog.js` | `bad56771ce554a57ed2b3a158df5546f4a0b0b15dbcc53d3cce7a7d9fe489401` |
| `extension/settings/WidgetSettingsPage.js` | `fffc2d7d17e275204e24841820f64266c03f51699afc4c7ff6d372308024ceac` |
| `extension/settings/WidgetSubPage.js` | `dd422f630a7b6d1fbfbcaf5b0002be9c0fa8747f6e336592294f727c1fc8963d` |
| `extension/settings/WidgetsData.js` | `0d32280a935975d85e4855ff8e7dc080f279158121a60144b8320d3572f3590d` |
| `tests/test_identity.js` | `ecb323e93cf50c4aa1b0a97a2ac0e275a19385fd4502b6de986b3ebaa4af4454` |
| `tests/test_identity_gtypes.gjs` | `78cc179393780e637d3fef794314b0288c4ba33dde8bc920b26b30aab481670f` |
| `tests/test_identity_migration.py` | `65ebeb9c708aa2e6087c3e129a868496591e9cd24d9c0dbce1c2a83d8551ecf5` |
| `tools/migrate-identity.py` | `9870b3865a1ee222e562be7edc8cc1ee4de8eb2474fffc884b630552558e6f25` |
| `tools/update-local.py` | `5c4f32919778984e5b3669f8804a2eb549906e067fb7a0613a572628d826d4e7` |

## Rechecagem ID-A01 — remoção parcial corrigida

Novo alvo estável: migrador SHA-256 `7de275c0214bf051a5fe0f2bbd73567af38f4b7e2a5f787830d762d18a812a88`; teste SHA-256 `189fda217a347ec9cf7ba3ed9a3b1f93abbc25a9c665860e160ddc4c7af4c851`. Hashes idênticos antes/depois desta rechecagem.

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_identity_migration.py -v`: **11/11 aprovados**, 0,632 s. Sintaxe AST dos dois arquivos aprovada. Não se repetiu suíte global: a mudança afeta somente validação de remoção e seu teste; os resultados integrados anteriores permanecem associados ao alvo anterior.

A marca removal_started e estado pending são persistidos antes de rmtree, tanto no rollback quanto na recuperação automática. Sem marca, árvore incompleta é recusada; com marca, apenas arquivos restantes cujos nomes/hashes constem no manifesto são aceitos. Novo teste reproduz remoção de helper.py com OSError, recusa/preserva arquivo novo e arquivo alterado, depois conclui rollback mantendo legado e configuração original. Verificação adicional independente em tempdir confirmou: subset sem marca recusado; subset intacto com marca aceito; symlink introduzido no subset recusado. Não se afrouxou a verificação geral de conflito para todo rollback.

**ID-A01 resolvido no cenário reproduzido; nenhum achado impeditivo permanece no escopo auditado ID-01.** Configuração/migração/rollback e GTypes estão aprovados no nível local delimitado, combinando suíte integrada anterior e rechecagem específica atual. Não confundir contagens: 83 Python era a suíte integrada anterior; 11 é o arquivo específico atual, não nova suíte completa. Descoberta GNOME, preparo real, ativação manual com somente uma identidade, gráficos e operação instalada continuam não executados pelo auditor. RAM/EXT e limites de concorrência/durabilidade previamente registrados permanecem separados.

Supervisor pode concluir a revisão operacional documental e orientar preparo humano autorizado respeitando sandbox; nenhuma instalação, troca UUID, GSettings pessoal ou reload foi realizada nesta rechecagem. Backend e supervisor recebem o encerramento do achado.
