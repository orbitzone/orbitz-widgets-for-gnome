# BRAND-01 — logo própria e versão 1.0 — 18/10/2026

Estado: **implementado com testes específicos aprovados; parecer UX favorável no escopo do asset/integração estática; página GTK pendente**. Escopo recebido do supervisor: logo SVG original, Sobre com versão 1.0 e identidade própria, sem alteração de hardware/RAM/EXT, sem instalação.

## Entrega

- `extension/media/orbitz-logo.svg`: desenho vetorial original implementado diretamente no repositório. Anel/O central teal com órbita elíptica cyan inclinada e pequeno satélite; fundo transparente, viewBox128, title/desc e aria-labelledby. Sem relógio, dígitos, logo azclock, raster, scripts, fontes ou referências externas. Cores #0f766e/#2dd4bf/#22d3ee; contorno teal mantém definição sobre fundo claro e interior luminoso sobre fundo escuro. Não foi usado ImageGen por se tratar de asset vetorial nativo.
- `extension/settings/AboutPage.js`: carrega SVG por `Gio.FileIcon`/`Gio.File.new_for_path`, caminho explícito `Me.path/media/orbitz-logo.svg`, sem depender de cache do icon theme. Tamanho100px e margem inferior5 preservados. Versão exibida usa version-name; fallback1.0 para metadata em cache com version inteiro1. Nome/autoria/GitHub preservados. Crédito upstream e aviso LICENSE/ausência de garantia reunidos no grupo Créditos, sem apagar avisos ou arquivos de licença.
- `extension/metadata.json`: version permanece inteiro1; adicionado version-name1.0. UUID/schema/compatibilidade/gettext do ID-01 preservados.
- `tests/test_identity.js`: verifica inteiro1/version-name1.0 e fallback sem version-name; arquivo SVG original sem recursos externos/scripts/raster, title/desc/viewBox; caminho de FileIcon;100px/margem5; licença dentro de Créditos; demais links/autor/schema e controles mantidos.

## Evidências

- `node tests/test_identity.js`: aprovado.
- `gjs tests/test_identity_gtypes.gjs "$PWD"`:20/20 pares de GTypes legado/Orbitz distintos no mesmo processo aprovados.
- `node --check extension/settings/AboutPage.js`: aprovado.
- `git diff --check -- extension/settings/AboutPage.js extension/metadata.json tests/test_identity.js`: aprovado também após o agrupamento final de Créditos.
- SVG parseado/renderizado com librsvg/Cairo reais, sem janela, em100px e32px sobre fundos branco e #141a21 aproximado. Prévia local `/tmp/orbitz-logo-preview.png` inspecionada pelo frontend e enviada ao UX. Alvo100px aprovado pelo parecer UX;32px tem cruzamentos/satélite densos e não integra o aceite. Isso não certifica contraste/acessibilidade completa ou renderização Gtk.Image.

Fonte SVG é o artefato original; PNG de preview é apenas evidência temporária, não integra o pacote. Sem mudanças em vendor, recursos/créditos legados ou licenças.

## Coordenação e limites

Backend informado das fontes estáveis para hashes/overlay; ferramentas operacionais permanecem de sua propriedade. Backend reportou whitelist SVG/metadata coberta por hashes/backup/rollback e testes próprios, não repetidos pelo frontend.

Supervisor informou que captura do usuário mostrava janela legada Desktop Clock7/PayPal; fonte About da nova instalação foi conferida por ele como Orbitz. Não se usa essa captura como prova de falta de atualização no novo UUID. Na orientação final de teste, fechar preferências antigas e abrir explicitamente `gnome-extensions prefs orbitz-widgets@orbitzone.github.io` sob coordenação do supervisor. Nenhum comando de preferências/instalação/reload foi executado pelo frontend.

UX recebeu brief, SVG, prévia e limites para revisão. Renderização gráfica da página Sobre/foco/rolagem continua pendente em ambiente permitido; não houve nova tentativa Broadway nem acesso à sessão ativa. RAM/EXT não foram alterados ou declarados resolvidos. Sem commit/push. Próximos responsáveis: UX parecer ao frontend; supervisor consolida e solicita auditoria/atualização autorizada.

## Parecer UX recebido

`docs/design/2026-10-18-brand-review.md`: favorável para asset100px e integração estática, sem mudança pedida. SVG/prévia inspecionados, transparência/órbita/O e ausência de recursos externos conferidas. UX calculou contrastes sólidos do contorno teal contra branco5,47 e fundo referência #151a21 3,19; cores internas claras dependem desse contorno. Não é certificação de todos os temas/pixels. A32px há densidade nos cruzamentos/satélite; não ampliar aceite além do alvo100px. title/desc/aria SVG não comprovam nome acessível efetivo de Gtk.Image via FileIcon; há título textual na página. Caminho, tamanho/margem e versão/fallback aprovados estaticamente. Página GTK/foco/DPI/cache/UUID ativos permanecem sem validação. Supervisor recebe parecer e fontes estáveis, sem instalação pelo frontend.

Ressalva final recebida do UX: consolidação do aviso GNU/LICENSE/garantia no grupo Créditos foi considerada coerente com o escopo, porém não reinspecionada por UX após esse último ajuste. A evidência desse agrupamento é o teste de identidade do frontend; o parecer favorável do asset SVG permanece.
