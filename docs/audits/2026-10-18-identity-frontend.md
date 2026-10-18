# ID-01 — identidade própria Orbitz — frontend — 18/10/2026

Estado: **implementado e estável com testes específicos; revisão UX/auditoria e validação gráfica pendentes**. Autorização/decisão recebida do supervisor: projeto Orbitz de Felipe Santiago/orbitzone, UUID/schema próprios, versão inicial própria 1. Isso não declara release instalada ou validada.

## Arquivos e contratos

- `extension/metadata.json`: nome Orbitz Widgets for GNOME; descrição de widgets/agenda/notas com autoria Felipe Santiago (orbitzone); URL `https://github.com/orbitzone/orbitz-widgets-for-gnome`; UUID `orbitz-widgets@orbitzone.github.io`; schema `org.gnome.shell.extensions.orbitz-widgets`; versão 1. Removidos metadado gerado SweetTooth e campo de doação upstream. Compatibilidade declarada 42/43/44 e gettext-domain `azclock` preservados.
- `extension/schemas/org.gnome.shell.extensions.orbitz-widgets.gschema.xml`: cópia integral das chaves, tipos e defaults do XML legado, alterando somente id/path para `/org/gnome/shell/extensions/orbitz-widgets/`. `widget-data` continua `aaa{ss}` e `changed-data`, `a{ss}`. XML azclock legado intocado para leitura/migração.
- `extension/settings/AboutPage.js`: título usa o nome dos metadados; descrição destaca funcionalidades; links principais GitHub Orbitz e Felipe Santiago · orbitzone. Removido CTA PayPal sem criar destinatário de doação. Crédito conciso azclock · Andrew Zaech e link original em grupo Créditos. Texto GNU GPL2+ e controles de importar/exportar preservados. Ícone simbólico genérico `view-grid-symbolic` ocupa o mesmo espaço de 100px; asset/logo upstream não foi apagado nem apresentado como logo autoral. Nenhum logo raster foi criado, nenhuma fonte/medida/spacing foi alterada.
- `extension/extension.js`: rótulo visível Configurações do Orbitz e prefixos de logs Orbitz; nome de fonte GLib `[orbitz]`. Classes internas AzClock preservadas, assim como lógica funcional.
- `tests/test_identity.js`: metadados, identidade dos schemas, construção real de About com atores sintéticos, autoria, destino dos três links, licença, ausência do CTA antigo, controles Save/Load e ícone genérico.

Backend recebeu os IDs/path e disponibilidade do XML. Propriedade de `tools/update-local.py` e `migrate-identity.py` mantida com backend, sem edição frontend. Migração, ativação e hashes instalados são etapas operacionais distintas.

## Evidências desta execução

- `node tests/test_identity.js`: aprovado.
- `glib-compile-schemas --strict --dry-run extension/schemas`: aprovado, sem gerar binário no repositório.
- `node --check extension/settings/AboutPage.js` e `node --check extension/extension.js`: aprovados.
- `git diff --check -- extension/metadata.json extension/settings/AboutPage.js extension/extension.js`: aprovado.
- Teste compara novo XML integralmente ao legado após substituir unicamente a tag id/path; sem alterações de valores/defaults.

Não foi repetida suíte global para mudança de identidade/textos sem alteração de lógica. Teste About usa mocks, portanto não certifica dimensões de texto, renderização real, foco ou navegação GTK. Registros de versão/UUID não substituem teste de migração.

## Créditos, UX e limites

Licenças, créditos existentes em recursos, vendor e locales preservados. UX recebeu proposta e marco estável pelo canal exclusivo, com pedido de revisão discreta da hierarquia, sem redesign ou alteração de tamanhos. Parecer será encaminhado ao supervisor quando recebido. Documentação de produto permanece com supervisor.

Nenhuma instalação, reload GNOME, alteração GSettings, commit/push ou acesso a dados pessoais. RAM sem modal e EXT permanecem pendências separadas; ID-01 não declara resolução desses defeitos. Próximos responsáveis: backend testa ferramenta/migração; UX envia parecer estático ao frontend; supervisor consolida documentação e encaminha auditoria/ativação explicitamente autorizada.

## Ajuste pontual do aviso de licença

Supervisor identificou divergência herdada entre aviso GPL2+ da página e texto LICENSE distribuído. A referência exibida passou a ser neutra: “GNU General Public License — veja LICENSE do projeto”, com link `https://github.com/orbitzone/orbitz-widgets-for-gnome/blob/main/LICENSE`. Aviso de ausência de garantia e créditos preservados; nenhum arquivo LICENSE foi editado e não houve interpretação/relicenciamento. `test_identity.js` agora exige link LICENSE, aviso de garantia e ausência da afirmação version2+. Teste, sintaxe About e diff-check específicos aprovados. Este complemento substitui apenas a descrição anterior de aviso GPL2+ preservado; restante do escopo inalterado.

## Coexistência de GTypes — correção necessária ID-01

Supervisor identificou risco na ativação da nova identidade no mesmo processo que já carregou o legado. Reprodução real, sem janela: registrar duas classes JavaScript com o mesmo nome e GType implícito resulta em `Type name Gjs_AzClockIdentityProbe is already registered`. Desativar extensão não remove os tipos registrados do processo.

Correção: nomes explícitos `OrbitzWidgets<Export>` em todos os **20** registros GObject de `extension.js`, `prefs.js` e páginas em `extension/settings/` (AboutPage, AnalogClockSubPage, CommandLabelSubPage, DialogWindow, DigitalClockSubPage, SubPage, TextLabelSubPage, TimeZoneDialog, WidgetSettingsPage, WidgetSubPage). Arquivos SettingsImport/WidgetsData não registram GTypes. Metadados existentes de propriedades/sinais são preservados; nomes das classes JavaScript, exports e controlador plain AzClock continuam iguais. XML/schema/legado não alterados nesta correção. Isso amplia apenas a superfície necessária de nomes de tipos para coexistência, conforme orientação explícita do supervisor.

`tests/test_identity_gtypes.gjs` lê os 20 registros atuais e usa representações com GObject.Object para registrar cada nome legado; confirma colisão implícita e registra a representação Orbitz com o GTypeName da fonte no **mesmo processo**. Resultado: **20/20 pares coexistem** com tipos distintos. Comando: `gjs tests/test_identity_gtypes.gjs "$PWD"`. Não é teste completo de atores St/Clutter ou janelas GTK; comprova o namespace GType e cobertura dos registros no código.

`node tests/test_identity.js` e `node tests/test_settings_alignment.js`: aprovados; mock de registro da identidade adaptado à assinatura metadata/class. `node --check`: **14 arquivos de produção** conferidos (extension, prefs e settings). `git diff --check` desses arquivos e teste de identidade: aprovado. A mensagem preliminar ao supervisor citou 17 arquivos de sintaxe por engano; a saída executada e este registro corrigem o total para 14.

Estado estável para auditoria; supervisor/backend informados de que os novos hashes/overlay devem incluir essas fontes. Nenhuma instalação ou carregamento na sessão ativa. Esta correção não prova coexistência funcional completa dos dois conjuntos de widgets, migração ou segurança contra ativação simultânea; esses fluxos permanecem na coordenação operacional/auditoria. RAM/EXT continuam independentes.
