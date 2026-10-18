# Hardware — restauração do padrão visual histórico

Data: 18/10/2026. Estado: código estável e testes específicos aprovados; revisão visual e auditoria pendentes antes de atualizar instalação.

## Mudança

Em `widgets/cpu-ram-widget.py`, restaurado somente o padrão visual solicitado pelo supervisor, com referência ao coletor histórico em `2026-10-08/quan/outputs`:

- Span `font_family="monospace" size="7680" line_height="1.5"` (7680 unidades Pango = 7,5 pt).
- Barra exatamente com oito células; preenchimento `min(8, max(0, int(percent * 8 / 100 + 0.5)))`.
- Linhas compactas sem linhas vazias nem newline inicial/final dentro do span; uma quebra entre linhas.
- Duas posições iniciais, rótulo com largura quatro, três espaços antes da barra e duas posições antes do percentual de largura três. CPU/RAM/SSD/EXT compartilham as mesmas colunas. SSD usa prefixo de dois espaços, pois não foi acrescentado algoritmo/indicador de alerta.

Cálculo e cache SSD atuais, amostragem CPU/RAM, externo agregado e tratamento de falhas foram mantidos. Nenhuma restauração de múltiplos dispositivos/identidades ou lógica de alertas; essas diferenças semânticas continuam separadas em BUG02. Preservados importação inerte, execução pelo worker e roteamento CLI de hardware/detalhes/ejeção corrigido anteriormente. Nenhuma edição de GSettings, frontend, configuração ou instalação ativa.

## Verificação

`python3 -m unittest discover -s tests -p test_collector_entrypoints.py -v`: **9/9 aprovados**, em 18/10/2026.

Dois novos testes verificam arredondamento nas fronteiras 6,25% e 93,75%, limites inferior/superior e oito células; parse XML do markup confirma atributos, ausência de linhas vazias, quatro linhas com externo agregado e colunas estáveis para percentuais 0/25/50/100. A expectativa literal do teste `exec`/worker foi atualizada para o novo padrão explicitamente solicitado, mantendo a verificação completa da saída. Sete testes anteriores de importação, CLI por subprocessos com helpers sintéticos, identidade de ejeção e demais coletores continuam aprovados.

## Limites e próximos responsáveis

A evidência é funcional/estrutural do markup, sem captura GNOME ou alegação de aprovação visual. Frontend foi informado do contrato; supervisor encaminha ao auditor e ao fluxo visual antes de instalar a correção. Sem alteração dos cálculos/semânticas de BUG02, operação de dispositivos, rede real, dados pessoais ou cofre. Sem suíte global, commit ou push.
