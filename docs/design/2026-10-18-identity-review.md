# ID-01 — revisão estática de identidade e créditos

Data: 18/10/2026. Destinatário: frontend. Escopo confirmado recebido: identidade Orbitz atribuída a Felipe Santiago/orbitzone; metadados/About com projeto, autor e GitHub em destaque; CTA de doação upstream removido; origem azclock/Andrew Zaech e licenças preservadas. Sem redesign, novas fontes, spacing, dimensões ou logo. RAM/EXT permanecem assuntos separados.

## Fontes e método

Leitura de `extension/metadata.json`, `extension/settings/AboutPage.js`, seus diffs contra HEAD e `tests/test_identity.js`. Não houve navegação externa, execução GTK/GNOME, captura ou leitura da instalação ativa. URLs foram conferidas como destinos literais solicitados; disponibilidade/conteúdo remoto não foram verificados. Testes e compilação informados pelo frontend não foram repetidos pelo UX.

## Parecer

**Hierarquia declarada e textos correspondem estaticamente à ID-01. Nenhum impedimento de texto ou atribuição identificado nesta revisão.**

| Critério | Evidência inspecionada |
|---|---|
| Identificação principal | Metadata usa `Orbitz Widgets for GNOME`; descrição atribui o projeto a Felipe Santiago (orbitzone). About usa `Me.metadata.name` com a classe de título preexistente `title-1`, seguido de descrição das funcionalidades. |
| Projeto e autoria | Linhas `Orbitz no GitHub` e `Felipe Santiago · orbitzone` ocupam os lugares das linhas GitLab/PayPal principais no grupo de informações. Destinos literais: `https://github.com/orbitzone/orbitz-widgets-for-gnome` e `https://github.com/orbitzone`. |
| Origem explícita | Grupo `Créditos` abaixo das configurações informa `Base original: azclock · Andrew Zaech`, com destino `https://gitlab.com/AndrewZaech/azclock`. Distingue autoria do projeto atual da base original sem apagar a atribuição. |
| Licença e doação | Constante de aviso GNU e seu link permanecem iguais no diff. CTA/URL PayPal e metadata donations removidos, sem substituição por conta de doação inventada. Este parecer não é auditoria jurídica de todas as licenças do repositório. |
| Identidade técnica visível | UUID `orbitz-widgets@orbitzone.github.io`, URL GitHub e versão 1 correspondem ao contrato recebido. Schema novo e gettext legado são mudanças técnicas cuja compatibilidade/migração não é certificada por UX. |
| Ícone e estilos | Ícone genérico `view-grid-symbolic` substitui referência ao logo upstream; conserva `pixel_size:100` e `margin_bottom:5`. Não é logo novo. Diff não altera fontes, propriedades existentes de spacing/tamanho ou controles Load/Save. Preservação do arquivo de logo e demais assets foi informada pelo frontend; não auditada aqui. |

O novo grupo de créditos acrescenta conteúdo e pode ampliar a altura natural da página, embora não mude propriedades de tamanho/spacing existentes. O nome e a descrição também são mais longos. Portanto, não se afirma geometria total ou ausência de truncamento preservadas apenas pelo diff; isso é limite visual a observar, sem propor compactação/redesign nesta entrega.

## Aceite e limites

Aceite estático desta revisão: título Orbitz vinculado ao metadata; versão/configurações nomeadas Orbitz; projeto e autor com destinos corretos; origem upstream em créditos; aviso GNU mantido; ausência de CTA PayPal; mesmas propriedades explícitas de estilo/dimensão dos componentes preexistentes. Esses critérios foram atendidos na leitura dos arquivos/diffs.

Frontend reportou `node tests/test_identity.js`, compilação estrita dos schemas e sintaxe JS aprovados. O teste lido constrói About com atores sintéticos e verifica textos, destinos de ativação, controles, ícone e identidade/schema. Isso não valida renderização, foco, árvore acessível nativa, truncamento ou navegação real.

Validação visual permanece pendente: quando houver ambiente isolado permitido, verificar título/descrição completos ou alcançáveis, créditos/aviso GNU acessíveis por rolagem e teclado e foco das linhas de link. Nenhuma tentativa gráfica bloqueada é solicitada agora. Não há recomendação de redesign ou de ampliar escopo para tradução geral dos rótulos herdados.

Somente este documento em `docs/design/` foi criado por UX. Nenhuma alteração de produção, instalação, dados pessoais, commit ou publicação. Próximo responsável: frontend encaminha o parecer e os limites ao supervisor; validações técnicas e migração seguem seus responsáveis.
