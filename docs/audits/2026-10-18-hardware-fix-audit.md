# BUG-01 — auditoria dirigida CPU/RAM/SSD — 18/10/2026

Estado: **correção backend e contratos locais aprovados nas verificações dirigidas; teste manual instalado/abertura RAM pendente**. Não é aprovação gráfica nem confirmação de instalação.

## Alvo e origem

HEAD `2a24e0d6875063cfee9412b1c9545181f999d3ad` mais checkout local; backend/frontend declarados estáveis pelo supervisor. Fontes: `2026-10-18-backend-cli-routing.md`, `2026-10-18-hardware-frontend-regression.md` e código/testes pertinentes. Backend altera CPU e teste de entrada; frontend acrescenta somente teste de fluxo, sem alteração de produção frontend nesta correção.

Supervisor reproduziu CPU/RAM instalados retornando span de métricas (exit 0) em vez de AZCLOCK_HARDWARE. Comparação histórica reportada por supervisor/backend mostrou flags no coletor histórico e ausência no HEAD. **A auditoria RF-01 comparou equivalência com HEAD; isso não comprovava paridade com execução histórica instalada.** Esta lacuna de cobertura explica por que aprovações locais anteriores não provaram a preservação desse contrato operacional. O auditor não repetiu consulta à configuração pessoal ou instalação ativa.

## Execuções independentes

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_collector_entrypoints.py -v
node tests/test_hardware_panel_flow.js
node tests/test_stats_storage_click.js
node tests/test_storage_ui.js
node --check tests/test_hardware_panel_flow.js
git diff --check -- widgets/cpu-ram-widget.py tests/test_collector_entrypoints.py tests/test_hardware_panel_flow.js
```

**7/7 Python aprovados**, 0,224 s; **3/3 arquivos JS dirigidos aprovados**; sintaxe JS e ast.parse dos dois Python aprovados; diff --check aprovado. Sem suíte global durante mutações frontend; nenhuma mudança adicional ou falha justificou repetir a suíte global após estabilização.

Os sete testes Python incluem subprocessos reais do coletor copiado em tempdir, helpers sintéticos irmãos para CPU/RAM/SSD/externo, protocolos, passagem de argv e __main__; despacho de ejeção exclusivamente mock; importação inerte; exec do CPU com namespace usado pelo worker e métricas sintéticas. Teste adicional independente copiou o coletor atual para tempdir, criou helpers com saída JSON e stubs que falham se amostragem/ejeção ocorrerem. subprocess.run com timeout 5 s:

| argv | Saída esperada e observada | Resultado |
|---|---|---|
| --hardware cpu --details | AZCLOCK_HARDWARE: + argv integral | Aprovado; precedência hardware |
| --hardware ram | AZCLOCK_HARDWARE: + argv integral | Aprovado |
| --details | AZCLOCK_STORAGE: + argv integral | Aprovado |

Não se executaram eject_device real, sondas de hardware, ferramentas privilegiadas, limpeza, rede, credenciais, instalação, GSettings, recarga GNOME ou sessão gráfica. Testar auxiliares sintéticos comprova a fronteira CLI/argv, não informações físicas do hardware. Teste de eixo ejeção não autorizou operação real em dispositivo.

## Revisão de contrato e achados

`main()` agora despacha --hardware para hardware-details.py, --eject para serviço de ejeção com identidade e --details para armazenamento-widget.py, antes de cpu()/sleep/coleta. runpy.run_path(...,run_name='__main__') mantém argv, aceita --hardware cpu/ram --details produzido pelo frontend e resolve helper por Path(__file__).with_name. Flags normais/worker mantêm amostragem anterior. Helpers reais foram lidos para confirmar que consomem --hardware e --details e emitem os mesmos protocolos usados pelo frontend; sua instalação conjunta continua necessária.

Fluxo frontend carrega métodos reais de hit-test/press-release/refresh e renderizações reais das fábricas. Atores/Pango/modalidade/subprocesso são simulados. Sequência CPU→RAM→SSD→RAM→CPU passou, preservando o diálogo entre aberturas; CPU/RAM selecionam modo, enviam --hardware cpu/ram --details, SSD envia --details e limpa _hardwareMode. Assertivas de texto, estado, protocolo e associação de tooltip/cartão permanecem; não houve relaxamento de testes para suprimir o sintoma.

**Nenhum impeditivo adicional reproduzido no alvo desta correção.** Sintoma RAM não abrir no GNOME não foi reproduzido nem descartado por esses mocks: manter pendência manual; não criar correção frontend especulativa. Caso persista, coletar cenário/erro e investigar hit-test/modalidade real.

**Pendência separada:** external_usage agregado e namespace sem EXTERNAL_DEVICES levam a devices=[] no worker, divergindo do mapa/linhas de dispositivos externos históricos. Já informado pelos responsáveis; não corrigido aqui, não confundido com CPU/RAM e não aprovado como paridade histórica. Não importar cálculos/apresentação históricos inteiros para esta correção mínima.

## Atualização e verificação posterior

Supervisor informa plano de instalação **1 arquivo/0 comandos**, somente cpu-ram-widget.py. Essa contagem é evidência reportada pelo supervisor, não nova execução deste auditor sobre instalação/configuração pessoal. Antes de aplicar, conferir plano/hash no fluxo autorizado de atualização; nenhum apply foi executado pelo auditor.

Como esta entrega não muda JavaScript do Shell e a consulta de detalhes lança um novo subprocesso Python, **depois de aplicar e verificar o coletor correto, basta fechar/reabrir o painel ou solicitar nova consulta** para testar a correção de detalhes. Não há necessidade técnica demonstrada de reiniciar/recarregar GNOME para este despacho CLI. Isso não afirma que a correção já está instalada nem que o clique RAM real foi aprovado. Worker persistente pode conservar código compilado de métricas, mas o caminho de consulta de detalhes é novo processo independente; métricas/deriva externa não foram alteradas aqui.

## Conclusão por dimensão

- Funcional local: roteamento CLI/contrato worker e fluxo sintético CPU/RAM/SSD aprovados no escopo executado.
- Visual/interativa instalada: pendente, incluindo abertura real RAM e ausência do erro CPU/SSD após atualização verificada.
- Segurança/integridade: nenhum impeditivo novo encontrado no despacho mínimo; identidade de ejeção passada e mockada, sem operação destrutiva. Não é certificação geral de dispositivos/instalador.
- Desempenho: sem benchmark ou alegação de ganho.

Supervisor recebe relatório para plano e aplicação autorizados; usuário/frontend fornecem teste manual posterior sem reload. Nenhuma alteração de código pelo auditor, commit/push ou mudança de escopo.

## Hashes do alvo

| Arquivo | SHA-256 |
|---|---|
| `widgets/cpu-ram-widget.py` | `774c5df6031b868630a01cd924548c78720ef6a46b14937349cea645b8ed2416` |
| `tests/test_collector_entrypoints.py` | `d0d4d5c96c3547edb6a7abf78cddd9017853e6c03c5fa089f4649c1715b0c323` |
| `tests/test_hardware_panel_flow.js` | `c738a9c4ca2e18fc1a27069fe14cb84805063815ee607a4cae3ff9a5de6a57b4` |
| `extension/extension.js` | `242c2b9be7116b946fda3814d4dcc4ad13156048afcb1d128c1bd28620ff0525` |
| `extension/panels/storage.js` | `53e0cfcfacf7b5bebbc8faf55da986a4650d4585ece59e5f83dacfb5fe24e9f0` |

Hashes CPU/teste Python conferidos antes/depois dos testes backend e na revisão integrada, inalterados; hashes frontend acima identificam o alvo lido/executado. Logs em stdout desta execução; números de testes não substituem o registro de limites.
