# VIS-01 — auditoria dirigida do markup Hardware — 18/10/2026

Estado: **formato e contratos locais aprovados; aparência renderizada e clique RAM real pendentes**. Não houve instalação, reload GNOME, operação em dispositivo, uso de dados pessoais ou alteração de código pelo auditor.

## Alvo e referências

Checkout sobre HEAD `2a24e0d6875063cfee9412b1c9545181f999d3ad`, backend/frontend declarados estáveis. Lidos `2026-10-18-backend-hardware-markup.md`, `docs/design/2026-10-18-hardware-restoration.md` e `2026-10-18-ram-hit-test.md`. Valores históricos (monospace/7680/1.5/barra8/colunas compactas) confirmados pelo usuário/supervisor; o auditor não reinspecionou configurações pessoais ou arquivos históricos ativos. Essa origem é evidência recebida, separada da verificação independente do formato atual.

## Execuções independentes

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_collector_entrypoints.py -v
node tests/test_hardware_panel_flow.js
node tests/test_stats_storage_click.js
gjs tests/test_stats_pango.gjs "$PWD"
git diff --check -- widgets/cpu-ram-widget.py tests/test_collector_entrypoints.py
```

**9/9 testes Python aprovados** (0,229 s), **2/2 entrypoints Node aprovados**, **1/1 teste GJS/PangoCairo aprovado**. ast.parse dos dois Python e diff --check aprovados. Não se repetiu suíte global: alteração delimitada à apresentação CPU e expectativas correspondentes. Primeira chamada GJS sem argumento de raiz falhou ao tentar undefined/extension/extension.js; corrigida invocação conforme relatório frontend, sem editar teste ou código. A falha de invocação não é regressão do produto. Comando correto está acima; não recomendar execução sem "$PWD".

Além da suíte, teste independente importou o coletor sem executar main e chamou main com leituras CPU/RAM/cache e externo sintéticos, stdout capturado e sleep neutralizado. `Pango.parse_markup(markup,-1,'\x00')`, com Pango real e sem janela, aprovou com EXT ausente e EXT=25. Atributos observados em toda extensão UTF-8:

```text
family monospace
size 7680
line-height 1.500000
```

Texto resultante contém três ou quatro linhas, sem newline inicial/final interno nem linhas vazias. CPU=100/RAM=0/SSD=50/EXT=25 preservaram nomes e colunas; barras têm oito células. Saída externa do print possui newline normal de protocolo, que não é linha vazia dentro do span. Os testes verificam limites/arredondamento 6,25% e 93,75%, clamp 0/8 e formato completo por linha.

Teste GJS persistente usa método _storageTarget atual e geometria real PangoCairo: CENTER, natural/220/440, início/meio/fim de CPU/RAM/SSD, com/sem EXT; passou. Atores Clutter, transformações, oclusão, sequência real de entrada e modalidade continuam fora dessa prova. Node confirma sequência CPU→RAM→SSD→RAM→CPU e reset de modo em atores simulados.

## Contratos e diagnóstico

Formato implementado corresponde à referência histórica reportada: `<span font_family="monospace" size="7680" line_height="1.5">`, oito células, labels largura quatro, espaços/percentuais alinhados e linhas compactas. A atualização literal do teste worker decorre da mudança visual explicitamente solicitada: continua comparando a saída completa, sem remover assertivas ou aceitar qualquer markup. Não é enfraquecimento de teste para ocultar falha.

Os sete testes de entrada existentes permanecem, incluindo subprocessos reais em diretório temporário com helpers sintéticos CPU/RAM/SSD/externo, precedência/argv/protocolos, importação inerte, exec pelo contrato __main__/__file__ do worker e ejeção exclusivamente mock. Nenhuma ejeção real foi executada. A revisão do coletor confirma que despacho CLI permanece antes da amostragem; cálculos CPU/RAM, cache SSD e external_usage agregado não receberam mudança semântica nesta entrega. Alteração limita bar/rows/span e suas expectativas.

**Nenhum impeditivo novo reproduzido neste escopo.** Não declarar RAM corrigida: o usuário relatou ausência de modal real e os ensaios locais não a reproduziram; manter pendência manual conforme investigação frontend. Não atribuir o problema à fonte sem evidência. Deriva de múltiplos externos/devices=[]/cálculos históricos segue BUG02 separado; não foi reintroduzida nesta apresentação. Sem ganho de desempenho medido.

## Aplicação e validação posterior

Plano esperado informado pelo supervisor: **1 arquivo/0 comandos**, somente coletor. Não foi executado plano pessoal/instalação pelo auditor e não há confirmação de aplicação neste relatório.

**Após instalar/verificar o arquivo correto, parar e abrir os widgets pelo controlador** para reiniciar o worker, que compila os coletores ao iniciar. Reabrir somente o modal lança nova consulta de detalhes, mas não atualiza o código já compilado do resumo persistente. Shell JS não mudou: não há necessidade demonstrada de logout/reload GNOME para esta correção. A recomendação anterior de somente fechar/reabrir modal aplicava-se ao despacho BUG01, não ao resumo visual VIS01.

Supervisor conduz aplicação autorizada e teste manual do usuário; frontend/UX avaliam aparência e RAM no ambiente real. Persistindo RAM, manter investigação direcionada, sem correção especulativa ou ampliação de escopo automática. Não contornar permissões do sandbox ou os bloqueios gráficos.

## Validações separadas

- Funcional/estrutural: formato, Pango, CLI e worker aprovados nas verificações acima.
- Visual/interativa: pendente; sem captura antes/depois, prova de pixels, offsets Clutter, foco ou abertura real RAM.
- Segurança/integridade: nenhuma regressão impeditiva encontrada na alteração de apresentação; sem operação destrutiva, instalação ou certificação integral.
- Desempenho: não medido.

## Identidade do alvo

| Arquivo | SHA-256 |
|---|---|
| `widgets/cpu-ram-widget.py` | `d7ef2800fd61c4663ad2cc859602190cb41337329d0b55b62dfe29ebeb0ab39e` |
| `tests/test_collector_entrypoints.py` | `baf976fe261ab03a423d92d759c4cfd253d5cec9133ca97b7c67306c11e82851` |
| `tests/test_stats_pango.gjs` | `93503dffd63789ca127c589011c98daea5821af39ff304ed82a9a12e419e1338` |
| `tests/test_hardware_panel_flow.js` | `c738a9c4ca2e18fc1a27069fe14cb84805063815ee607a4cae3ff9a5de6a57b4` |
| `tests/test_stats_storage_click.js` | `843529da37f68556ac4f27dade94f651482d02fdbcc31ef03e17bdce10414d48` |

Hashes do coletor/teste Python iguais no início e encerramento; teste GJS acrescentado pelo frontend foi recebido estável e identificado acima.
