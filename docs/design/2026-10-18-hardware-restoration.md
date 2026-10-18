# Hardware — parecer para restauração histórica

Data: 18/10/2026. Destinatário exclusivo: frontend. Escopo informado pelo frontend: orientação explícita do usuário, via supervisor, para restaurar tamanhos históricos como padrão mantido, sem redesign. Não é autorização para alterar outros componentes ou a instalação neste chat UX.

## Evidência disponível

Captura fornecida pelo usuário, inspecionada em `/tmp/codex-clipboard-70ecc3a9-9222-46a2-a3f5-181d2bc981d2.png`, com 548 × 596 pixels. Não foi copiada para o repositório. Ela mostra o estado relatado como maior, não uma comparação antes/depois: CPU/RAM/SSD em linhas com barras, percentuais alinhados à direita, cartão térmico abaixo e contorno de Hardware que cruza visualmente a região superior do contorno de Sistema. Esse cruzamento é observação da captura; sua causa e novidade não foram estabelecidas. Não há base para deduzir fonte nominal, escala GNOME, DPI, tamanho lógico ou spacing histórico apenas pelos pixels.

Fonte inicialmente lida, antes da restauração: `widgets/cpu-ram-widget.py`, funções `bar` e `main`; `extension/extension.js`, `Label.updateStyle`. Coletor declarava família monospace no markup, dez células por barra e linhas vazias entre CPU/RAM/SSD/EXT. A extensão lê `Text_Size`, mas o estilo observado usa 10px para CPU/RAM agrupado, 15px para outros agrupados e Text_Size em pt fora de grupo; markup pode especificar tamanho próprio. Assim, comprimento em células, tamanho/família efetivos e espaçamento entre linhas são dimensões distintas; reduzir a barra não comprova restauração da fonte.

Frontend confirmou, em mensagem posterior nesta execução, o padrão histórico apurado pelo supervisor e confirmado pelo usuário: `<span font_family="monospace" size="7680" line_height="1.5">`, oito células por barra, linhas sem newline inicial/final e sem linhas vazias. Configuração pré-update e atual reportadas iguais: Text_Size 8, padding L/R 20 e T/B 0, alinhamento X Start/Y Center/linha Center. Essas são referências confirmadas recebidas pela coordenação; o UX não inspecionou backup/configuração pessoal nem certificou sua origem independentemente. Backend foi acionado para restaurar apenas apresentação, preservando cálculos/cache/devices. Não alterar outros widgets ou GSettings. Relatório técnico associado: `docs/audits/2026-10-18-hardware-frontend-regression.md`.

## Parecer e critérios de aceite

Recomenda-se restaurar os valores demonstrados pelas fontes históricas identificadas pelo supervisor, preservando hierarquia, cores, transparência, posições, conteúdo e ações existentes. Não escolher um novo tamanho por aproximação estética. Comparar separadamente:

| Aspecto | Aceite da restauração |
|---|---|
| Fonte | Família, tamanho, peso e markup do Hardware iguais à referência histórica identificada; comparar configuração efetiva além do preset. Não alterar fontes de Desempenho/Sistema. |
| Barras | Oito células conforme referência confirmada, regra histórica de preenchimento, inclusive limites 0%/100% e arredondamento; CPU/RAM/SSD e EXT, quando presente, preservam nomes, percentuais e interpretação. Não extrapolar o comprimento para fonte/altura. |
| Espaçamento e dimensões | Restaurar line_height 1.5 e linhas sem vazios/newline inicial ou final, preservando configuração histórica reportada. Não compactar outros cartões para compensar. Verificar com e sem EXT, números de três dígitos e alerta de armazenamento. |
| Alinhamento e limites | CPU/RAM/SSD, barras e percentuais mantêm alinhamento da referência; ausência de truncamento, quebra inesperada e nova sobreposição atribuível à restauração. O cruzamento de contornos da captura exige comparação com histórico antes de ser classificado como regressão ou pedido de reposicionamento. |
| Interação | Após mudar comprimento/fonte, conferir que as regiões de clique correspondem às linhas CPU/RAM/SSD/EXT; preservar detalhes/ejeção e ausência de ação em espaços vazios. Alteração dimensional pode afetar hit test baseado em geometria de texto. |

Evidência mínima estrutural: origem/caminho ou hash do histórico e backup, valores antes/depois, diff limitado e teste sintético dos limites de barra/cliques afetados. Evidência visual, quando existir ambiente isolado permitido: mesmo tema, escala, monitor e fixtures com percentuais fixos antes/depois, anotando dimensões e fonte efetiva. Não é necessário iniciar novas tentativas gráficas bloqueadas agora; enquanto indisponível, registrar restauração estática separada da validação visual pendente.

RAM não abrir continua investigação funcional separada. A captura não demonstra evento de clique, comando disparado, foco ou erro; não atribuir sua falha à fonte, à barra ou ao spacing. O teste sintético anterior não comprova resolução na sessão real.

## Resultado desta entrega

Captura e trechos pertinentes inspecionados; critérios de restauração definidos. Nenhuma implementação, execução GTK/GNOME, acesso à sessão ativa, instalação, pesquisa externa ou mudança fora de `docs/design/`. Nenhuma restauração implementada ou validada visualmente por UX nesta etapa. Próximo responsável: frontend alinha os valores históricos concretos com supervisor/backend, implementa apenas sua área e devolve evidência quando disponível.

## Complemento — markup restaurado no repositório

Em 18/10/2026, frontend encaminhou estado backend estável e pediu parecer estático para repasse ao supervisor. Lidos novamente `widgets/cpu-ram-widget.py` e `docs/audits/2026-10-18-backend-hardware-markup.md`.

Inspeção própria confirmou correspondência com o contrato de apresentação recebido:

- Span literal com `font_family="monospace" size="7680" line_height="1.5"`.
- Barra de oito células, preenchimento limitado a 0–8 com `int(percent * 8 / 100 + 0.5)`; complemento até oito células.
- Todas as linhas são construídas com duas posições iniciais, label de largura quatro, três espaços antes da barra e dois antes do percentual com largura três. Isso mantém as mesmas colunas para CPU/RAM/SSD/EXT.
- `rows` recebe CPU/RAM/SSD e EXT apenas quando disponível; `\n`.join(rows) fica dentro do span, sem vazios ou quebras iniciais/finais internas. O newline final emitido por print fica fora do span.
- Não há novo indicador de alerta nas linhas restauradas. SSD usa o mesmo prefixo de dois espaços. Nenhuma exigência deste parecer cria algoritmo de alerta, múltiplos dispositivos ou mudança semântica de BUG02. O cenário de alerta citado inicialmente nos critérios só se aplica a variante já existente e autorizada, não à adição nesta entrega.

**Parecer: markup atual corresponde estaticamente à referência confirmada de fonte, barras e distribuição de linhas.** Não foi identificada necessidade de mudança frontend ou redesign para cumprir esse contrato. A inspeção não certifica equivalência de pixels, tamanho efetivo, alocação, sobreposição ou foco na instalação. Não houve nova captura, execução gráfica, instalação ou teste funcional por UX.

Evidências atribuídas aos responsáveis: backend reporta 9/9 testes específicos aprovados, incluindo limites/arredondamento/XML/colunas; frontend reporta reconhecimento de RAM por GJS/Pango sem janela. Esses resultados não foram repetidos por UX e não demonstram abertura interativa da RAM. Falha real continua pendente e separada; não se infere causa ou resolução pelo markup.

Próximo responsável: frontend repassa este parecer restrito ao supervisor, que coordena auditoria/atualização dentro da autorização aplicável. Verificação visual/interativa fica pendente até evidência permitida; nenhuma nova tentativa gráfica bloqueada é solicitada neste parecer.
