# BRAND-01 — auditoria dirigida — 18/10/2026

Estado: etapa backend aprovada no escopo temporário; frontend aguarda estabilidade formal para conclusão integrada. Sem instalação/ativação/reload ou dados pessoais.

## Atualizador — revisão independente

Lido `2026-10-18-brand-updater.md`, código e testes. Alvo updater SHA-256 `e7e044670c5c48695b36c6f907011e152210a2cc4472416dae8de4016bd491a1`; testes SHA-256 `1043f0f0fabb95325bd20fed9d31c6f9d2d81ed74e55a3b86ae96403efdc8d49`.

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_local_update.py -v`: **9/9 aprovados**, 0,234 s. Cenários usam temporários e GSettings mock; os argv --apply são sintéticos e não representam instalação real.

Whitelist acrescenta apenas extension/metadata.json e extension/media/orbitz-logo.svg, não JSON/SVG arbitrários, vendor, schema ou binários. select_identity exige UUID/schema instalado e fonte correspondentes; atomic_copy revalida metadata usando os mesmos bytes a gravar antes de criar temporário. Roundtrip em teste verifica manifesto/hash, cópia de metadata+logo, plano posterior vazio e rollback que restaura metadata anterior e remove logo novo. Rejeição UUID/schema divergente/ausente preserva destino. Guardas de backup/conflito e identificação de backups DEP01 antigos mantidas/testadas.

Nenhum impeditivo reproduzido nessa etapa. Persistem os limites operacionais de concorrência/durabilidade do atualizador já documentados; validação backend não certifica logo/GTK/GNOME nem instalação efetuada. Captura Desktop Clock 7/GitLab/PayPal foi associada ao About legado pelo supervisor; não inferir que migração falhou ou nova identidade possui esse conteúdo. Após aplicação autorizada, fechar preferências antigas e abrir explicitamente UUID novo é etapa operacional, não ação executada pelo auditor.

A conclusão frontend deverá conferir SVG passivo sem referências externas, filepath/Gio icon, version-name1.0 e version inteiro1, About sem PayPal e preservação dos créditos/LICENSE. Aguardando fonte estável; nenhum teste global repetido nesta etapa delimitada.

## Parecer integrado — frontend estável recebido

Lidos relatório frontend `2026-10-18-brand-frontend.md` e parecer UX `docs/design/2026-10-18-brand-review.md`. Versões abaixo declaradas estáveis; backend continua com hashes iguais aos da etapa anterior. Revisão independente dirigida concluída, sem instalação, sessão ativa, dados pessoais ou alterações de produção.

Comandos: `node tests/test_identity.js`, `node --check extension/settings/AboutPage.js`, `gjs tests/test_identity_gtypes.gjs "$PWD"`: aprovados. GTypes confirmou vinte pares legado/Orbitz distintos; não foi alterado registro GType nesta entrega. Teste identidade verifica FileIcon com caminho explícito `/synthetic/orbitz-extension/media/orbitz-logo.svg`,100px/margem5, inteiro version1 e version-name1.0, fallback1.0 quando version-name ausente, nomes/links/autoria, ausência PayPal e controles Load/Save preservados. Aviso de garantia/LICENSE e crédito upstream continuam no grupo Créditos; LICENSE raiz/extension comparados com HEAD e permanecem byte a byte intactos.

SVG validado independentemente por XML padrão e allowlist estrita: somente svg/title/desc/circle/g/ellipse, viewBox128, sem DOCTYPE/ENTITY, script, foreignObject, raster, atributo de evento, href/src/style ou url(). Geometria simples/cores locais, sem referência externa ou conteúdo ativo. SVG não depende de rede/fontes externas. Criação original é registro informado pelo frontend, coerente com a fonte vetorial; não foi realizada pesquisa de similaridade/marca e não se afirma originalidade jurídica absoluta.

Integração real de fonte lida: GLib.build_filenamev([Me.path,'media','orbitz-logo.svg']) e Gio.FileIcon/Gio.File.new_for_path; asset existe. version-name prevalece e version inteiro1 faz fallback1.0 para metadado em cache. UUID/schema/gettext mantidos. Whitelist operacional revisada inclui exatamente asset e metadata da extensão, com testes de hash/backup/rollback aprovados anteriormente nesta mesma entrega.

Renderização librsvg/Cairo sem janela e preview100px/32px são evidências reportadas por supervisor/frontend/UX, não nova execução do auditor. Parecer UX é favorável ao asset100px e integração estática; não ampliado a32px ou certificação de contraste/temas/acessibilidade. Não repetir renderização suficiente sem novo motivo. Integração Gtk.Image, foco/rolagem/DPI/cache e árvore acessível continuam sem execução real.

**Conclusão vigente: nenhum impeditivo reproduzido no escopo BRAND-01 auditado.** Atualizador/rollback aprovados em9 testes Python temporários, identidade/About em1 arquivo Node, GType em1 GJS; sintaxes afetadas aprovadas. Não houve suíte global adicional, benchmark ou alegação de instalação efetuada. Validação visual da página GTK segue pendente; aprovação do asset não a substitui. RAM/EXT permanecem fora do escopo.

Plano esperado reportado pelo supervisor:3 arquivos (metadata/About/logo), sem aplicação executada pelo auditor. Conferir hashes/plano antes da aplicação autorizada; fechar preferências antigas e abrir explicitamente `gnome-extensions prefs orbitz-widgets@orbitzone.github.io` para teste posterior. Captura Desktop Clock7/GitLab/PayPal corresponde ao legado segundo evidência do supervisor; não prova falha da nova identidade. Não é necessário presumir reinstalação/migração falha somente pela janela antiga.

### Hashes finais

| Arquivo | SHA-256 |
|---|---|
| `extension/media/orbitz-logo.svg` | `cda9b7e933d9c7d6a1583f8d2d36aaf692000afa18474bd30641b8e6bad42032` |
| `extension/metadata.json` | `0cbb022cde3ab667e07d212ae8bdadcd997875866c7e1753c42a1369980675ef` |
| `extension/settings/AboutPage.js` | `99c2d42af230ad64400fd2cd7cdf4ad7dbce3a48371575f9c96b0c3284b6bc53` |
| `tests/test_identity.js` | `40bf8ad57a9a64a4d9d70782356abfc9b58ace2a21c21a7a5b2c8ba63c9b0383` |
| `tools/update-local.py` | `e7e044670c5c48695b36c6f907011e152210a2cc4472416dae8de4016bd491a1` |
| `tests/test_local_update.py` | `1043f0f0fabb95325bd20fed9d31c6f9d2d81ed74e55a3b86ae96403efdc8d49` |
