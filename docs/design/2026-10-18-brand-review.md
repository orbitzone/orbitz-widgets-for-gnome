# BRAND-01 — revisão do logo Orbitz

Data: 18/10/2026. Destinatário exclusivo: frontend. Escopo recebido: SVG original com órbita/O, transparente, sem relógio/dígitos/azclock; integração no About conservando 100 px e margem inferior 5; versão exibida 1.0 com metadata inteiro 1. Sem alteração de fontes/geometria da página ou componentes Hardware/RAM/EXT.

## Evidência e resultado

Inspecionados `extension/media/orbitz-logo.svg`, trechos de integração em `extension/settings/AboutPage.js`/`extension/metadata.json` e prévia fornecida pelo frontend em `/tmp/orbitz-logo-preview.png`. A prévia foi informada como renderização real librsvg/Cairo a 100/32 px em fundos claro/escuro; UX inspecionou o resultado, sem reproduzir o processo de geração ou abrir janela. Não foi copiada para o repositório.

**Parecer favorável ao marco BRAND-01 no escopo do asset e da integração estática.** Na prévia, o anel central vazado e a órbita diagonal são reconhecíveis nos dois fundos a 100 px. O contorno teal mantém a borda no fundo claro; cyan/teal claros dão destaque no escuro. Não há aparência de relógio ou dígitos. A 32 px a silhueta ainda é distinguível, mas cruzamentos ficam mais densos e satélite menos separado; isso não impede o alvo solicitado de 100 px. Não se amplia o aceite a favicons ou tamanhos menores.

Verificação XML local passou: apenas svg/title/desc/circle/g/ellipse; ausência de atributos href e eventos; sem scripts, imagens raster ou recursos externos na fonte inspecionada. Fundo e centro não recebem preenchimento opaco. A composição usa formas geométricas simples no viewBox 128 × 128 e aparenta caber sem corte na prévia. Originalidade foi informada pelo frontend e é consistente com o código simples criado; não foi realizada busca de similaridade ou avaliação marcária.

## Contraste e acessibilidade

Cálculo próprio de luminância relativa sRGB para cores sólidas da fonte, sem medir pixels de antialiasing:

| Cor | Contra branco #ffffff | Contra escuro de referência #151a21 |
|---|---:|---:|
| Contorno #0f766e | 5,47:1 | 3,19:1 |
| Anel #2dd4bf | 1,86:1 | 9,39:1 |
| Órbita/satélite #22d3ee | 1,81:1 | 9,67:1 |

Os fundos são referências explícitas para cálculo, não medição do tema GTK nem certificação de todos os fundos possíveis. Os tons claros isolados têm baixo contraste contra branco, mas o contorno teal delimita suas formas. Preservar o contorno faz parte do aceite deste asset; não substituir toda a silhueta pelo cyan em fundo claro. Esses números não constituem aprovação geral de acessibilidade nem requisito de contraste textual aplicado ao logo.

SVG contém title `Orbitz`, desc e `role=img` com aria-labelledby correto; IDs e associação foram conferidos. Isso oferece semântica em contextos SVG que a exponham, mas **não prova nome acessível no Gtk.Image** quando carregado por Gio.FileIcon. O título textual Orbitz permanece na página; inspeção da árvore acessível nativa segue pendente. Não se exige redesign para encerrar esta análise do asset.

## Integração e limites

Leitura confirma caminho explícito por `Me.path/media/orbitz-logo.svg`, carregamento Gio.FileIcon, `pixel_size:100` e `margin_bottom:5`. About lê version-name com fallback para 1.0 quando o metadata inteiro é 1. Atributo version-name 1.0 está presente. Essa mudança substitui o ícone genérico da ID-01; não altera o parecer anterior sobre autoria/créditos. O aviso de licença foi posteriormente informado pelo frontend como neutro e vinculado ao LICENSE do projeto; a afirmação de GNU inalterada no relatório inicial ID-01 descreve apenas aquele estado anterior.

Teste_identity aprovado é evidência reportada pelo frontend, não repetida por UX. Não foi verificado o carregamento da imagem em Gtk.Image real, abertura de preferências do novo UUID, cache de janela legada, foco, rolagem, temas nativos ou DPI. A captura anterior da janela legada não serve como evidência do novo About. Não houve instalação, acesso à sessão ativa, pesquisa externa, commit ou alteração de produção por UX.

Aceite atendido: SVG transparente e inspecionável, silhueta de órbita/O legível na prévia de 100 px em claro/escuro, ausência de relógio e dependência externa, semântica SVG explícita e integração estática conservando espaço solicitado. Validação da página GTK integrada permanece pendente até evidência permitida. Próximo responsável: frontend repassa parecer/limites ao supervisor e preserva distinção entre validação do asset e da janela instalada.
