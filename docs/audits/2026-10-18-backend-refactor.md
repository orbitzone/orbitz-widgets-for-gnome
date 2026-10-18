# RF-01 — revisão estrutural backend

Data: 18/10/2026. Responsável: backend (`01a14cfe-1021-73b2-b031-b1ae67f7687e`).
Estado: implementado com validação funcional específica; integração e auditoria independente pendentes. A documentação de produto e o aceite integrado pertencem ao supervisor.

## Escopo e resultado

Revisados os 27 arquivos próprios da área exclusiva inicial: 19 em `widgets/`, seis de domínio/persistência/integração da agenda, persistência SQLite das notas e encerramento dos coletores. Onze receberam refatoração; dezesseis foram mantidos. Quatro módulos novos concentram responsabilidades antes misturadas. Não foram alterados código frontend, testes JS, vendor, credenciais, dados pessoais, instalação ativa, configurações históricas ou licenças. Sem commit, push ou recarga GNOME.

A revisão tomou como referência o checkout compartilhado sobre `2a24e0d`, contratos vigentes e baseline do auditor. Alterações anteriores do supervisor e alterações concorrentes do frontend foram preservadas. Nenhuma pesquisa externa foi necessária.

## Inventário por arquivo original

| Arquivo | Decisão | Justificativa e fronteira |
|---|---|---|
| `widgets/armazenamento-widget.py` | Manter | Inventário de montagens/SMART e seleção do dispositivo compõem a mesma consulta; validações e limites permanecem locais. Não unificar com `external_storage`: inventários têm colunas, cache e semânticas de montagem distintos. |
| `widgets/atualizacoes-widget.py` | Manter | Consulta limitada por provedor, composição de resultados e ações explícitas; subprocessos/cache/terminal já delegados ao runtime. Dividir 91 linhas não traz responsabilidade reutilizável adicional. |
| `widgets/clima-widget.py` | Manter | Cliente, validação, cache e saída de um único provedor. Cache aceita previsão antiga em falha e tem caminho histórico próprio; não substituir pelo cache com expiração rígida do runtime. |
| `widgets/conexoes-inspect.py` | Manter | Inspeção sob demanda independente do firewall, com validação de destinos e execução limitada. |
| `widgets/cpu-ram-widget.py` | Refatorar | Amostragem e apresentação agora em `main()`; importar definições não dorme, lê métricas ou imprime. Execução direta e `exec` do worker preservadas. |
| `widgets/docker-widget.py` | Manter | Consulta/links de contêineres em módulo de 66 linhas; limites e contexto remoto já explícitos. |
| `widgets/external_storage.py` | Manter | Inventário, identidade e ejeção verificável constituem serviço de dispositivos; ejeção já isolada em função própria. Preservar revalidação de identidade, ordem de desmontagem e proteção de montagens do sistema. |
| `widgets/firewall-widget.py` | Refatorar | Mantém journal incremental, cache/lock, inspeção e CLI. Regras de validação/agregação/classificação/apresentação transferidas para `firewall_patterns.py`, com reexports compatíveis. |
| `widgets/hardware-details.py` | Manter | Inventário CPU/RAM e importação explícita de firmware; execução já em `main()`, runtime compartilhado para consultas/cache/terminal. |
| `widgets/limpeza-linux.py` | Manter | Varredura segura por descritores e execução interativa já separadas; extrair componentes agora ampliaria fronteiras delicadas sem reuso concreto. Nenhuma limpeza executada. |
| `widgets/metrics-worker.py` | Manter | Agendador compacto de três coletores. Continua compilando scripts e executando com `__name__='__main__'`, capturando texto e emitindo envelopes JSON. |
| `widgets/network_quality.py` | Manter | Sondas ativas limitadas já separadas da amostragem passiva; parsing, probe e composição coesos. |
| `widgets/pressure_metrics.py` | Manter | Serviço pequeno somente leitura, sem UI, com parsing e heurísticas PSI explícitos. |
| `widgets/processos-widget.py` | Refatorar | Flags, amostragem e saída agora em `main()`. Definições de inventário, detalhes e ações podem ser importadas sem coleta. Não unificar leitura CPU com widget CPU/RAM: tratamento de campos e uso das amostras não são idênticos. |
| `widgets/rede-widget.py` | Refatorar | Flags e amostragem em `main()`; helpers de interface/contadores/taxas importáveis. Rotas IPv4/IPv6, janela de amostragem e saída preservadas. |
| `widgets/seguranca-widget.py` | Refatorar | Orquestração em `main()`, preservando resumo sem DNS e detalhes com cache/DNS limitado. Importação não chama `ss`/`getent` nem imprime. |
| `widgets/servicos-widget.py` | Manter | Coletor de serviços já tem função/entrada isoladas e chamadas limitadas; não há segunda responsabilidade independente relevante. |
| `widgets/temperaturas-widget.py` | Refatorar | Coleta resumida/cache/flags em `main()`; `display` fica importável junto a descrição/detalhes. Sensores, limites, fallback e limiar visual de 80 °C preservados. |
| `widgets/widget_runtime.py` | Manter | Infraestrutura compartilhada já reúne operações reutilizáveis de processo/cache/terminal; não misturar caches descartáveis com persistência histórica durável. |
| `extension/planner/store.py` | Refatorar | Delega somente substituição JSON durável a `atomic_json`; mantém lock, validação, migração, backup anterior, restauração, retenção e comandos locais. |
| `extension/planner/timesheet.py` | Manter | Modelo independente de UI já separa validação/cálculos/exportação, mutação de registros e gestão/migração de timesheets em funções; nenhuma dependência de calendário externo. |
| `extension/planner/external_store.py` | Refatorar | Delega escrita durável comum; acesso libsecret transferido a `credential_vault.py`, reexportando `Vault`. Mantém políticas de contas e cache separadas dos registros locais. |
| `extension/planner/apple_client.py` | Refatorar | Mantém transporte/descoberta/REPORT CalDAV; normalização comum deixa de residir no cliente de um provedor. Reexporta os helpers anteriores. |
| `extension/planner/ics_client.py` | Refatorar | Usa normalização e fuso diretamente de `calendar_events`; mantém validação HTTPS/webcal, DNS público, redirecionamentos e limites de gzip/tamanho. `apple.NoRedirect` e erro compatível continuam reutilizados. |
| `extension/planner/ui_state.py` | Refatorar | Delega a mesma substituição durável, mantendo lock, política de excluir valor `None`, tolerância de leitura e falha explícita de gravação em arquivo danificado. |
| `sticky-notes/storage.py` | Manter | Serviço SQLite compacto; WAL, transações, revisão otimista, importação legada e backups de 14 dias têm semântica própria. Não unificar com persistência JSON. |
| `extension/stop-collectors.py` | Manter | Operação restrita por UID/identidade de nascimento, congela árvore antes de enumerar e libera em `finally`. Uma responsabilidade coesa; nenhuma alteração de sinais/cancelamento. |

## Módulos novos e compatibilidade

- `extension/planner/calendar_events.py`: seis funções de recorrência, identidade, datas, dias e VALARM, mais `CalendarError` e `ZONE`. Nenhuma dependência GTK/libsecret/transporte. `apple_client` mantém `CalendarError`, `ZONE`, `normalize_events`, `json_identity`, `canonical`, `local_value`, `on_day` e `alarm_minutes` disponíveis; consumidores atuais foram conferidos.
- `extension/planner/credential_vault.py`: classe `Vault` sem alterações no corpo; importação de `gi` permanece tardia em `_service`, sem acessar o cofre durante importação/testes. `external_store.Vault` continua a mesma classe reexportada.
- `extension/planner/atomic_json.py`: temporário no diretório de destino, modo `0600`, JSON `ensure_ascii=False`, flush/fsync, `os.replace`, fsync do diretório e limpeza no `finally`. Prefixos/formatação/encoding originais preservados por argumentos. Locks, criação de diretório e política de backup ficam nos chamadores. Falha de serialização/substituição preserva o original. Falha de fsync posterior ao replace continua propagada, como antes; não se promete rollback após substituir.
- `widgets/firewall_patterns.py`: oito funções e constantes do modelo UFW. Não executa journal, rede, disco ou subprocessos; `payload` continua usando o relógio quando `now` não é informado. `firewall-widget` mantém reexports das funções/constantes do modelo, cache versão 2, TTL de 24 h e limites existentes.

Cinco coletores ganharam função `main` e guarda de execução. O worker continua executando os mesmos caminhos e código com namespace `__main__`; nenhum caminho/flag/prefixo/JSON/unidade foi renomeado. O efeito intencional é que importar esses módulos passa a disponibilizar definições sem iniciar coleta. Os scripts não produziam `EXTERNAL_DEVICES` antes, e o envelope opcional do worker não foi alterado.

## Testes e evidências desta entrega

Execuções específicas, sem suíte integrada durante mutações concorrentes:

| Comando/verificação | Resultado |
|---|---|
| `python3 -m unittest discover -s tests -p test_audit.py -v` | 19/19 aprovados: limites/timeout/watchdog/cache, ações, firewall, sensores, rede e contratos existentes. Arquivo de testes mantido. |
| `python3 -m unittest discover -s tests -p test_planner_backend.py -v` | 8/8 aprovados. |
| `python3 -m unittest discover -s tests -p test_collector_entrypoints.py -v` | 5/5 aprovados. |
| `compile(source, path, 'exec')` nos 27 originais + quatro módulos novos + dois testes novos | 33 sintaxes aprovadas, sem executar arquivos como aplicativos. |
| Comparação AST entre `git show HEAD:<original>` e módulo extraído | Corpos idênticos das seis funções iCalendar, oito funções UFW e classe Vault. |
| Comparação AST do corpo original de entrada e corpo `main` dos cinco coletores | Cinco corpos preservados; em temperaturas, helper `display` apenas mudou de posição. |
| `git diff --check` | Aprovado no checkout compartilhado naquele momento. |

Novos testes de agenda verificam: original preservado/temporários limpos em falha; permissão `0600`; ordem arquivo fsync→replace→diretório fsync; restauração com fingerprint e snapshot do estado anterior; retenção de 60 backups; oito processos CLI editando sem perder tarefas; independência de rascunhos/conexões e preservação de arquivo danificado; vínculo tarefa/horas sem duplicidade, divisão de cronômetro à meia-noite e proteção CSV; recorrência com EXDATE, identidade estável, horário local, VALARM e fim exclusivo de eventos de dia inteiro; classe de erro/URLs compatíveis.

Novos testes de coletores verificam: importação dos cinco módulos sem leitura/amostragem/subprocesso/saída; texto de taxa de rede; prefixos de detalhes; resumo de conexões sem DNS; fallback de temperaturas; execução de CPU pelo mesmo contrato `exec`/`__main__` usado pelo worker. Fixtures, domínios reservados e diretórios temporários; sem consultas reais de rede/cofre/calendários.

Os oito arquivos de testes Python anteriores (`test_audit`, `test_eject`, `test_external_devices`, `test_network_quality`, `test_pressure`, `test_services`, `test_stop_collectors`, `test_storage`) foram mantidos sem enfraquecer expectativas. Eles somam os 44 testes da baseline; não houve alteração desses arquivos. Somente o arquivo afetado `test_audit.py` foi reexecutado nesta entrega. Os dois novos arquivos somam 13 testes. Total esperado da próxima suíte Python integrada: 57, a confirmar pelo auditor.

## Validações separadas e próximo responsável

- **Funcional específica:** 32 testes aprovados nesta etapa (19 existentes + 13 novos), sintaxe e equivalência estrutural descritas acima. Não equivale a execução gráfica completa.
- **Visual:** não realizada/não aplicável à extração backend que preserva texto e contratos; testes de saída confirmam exemplos. Validação integrada GNOME/GTK permanece independente.
- **Segurança/integridade:** regressões locais cobrem atomicidade/permissões/locks/backups e limites existentes. Revisão independente final ainda pendente com auditor. Sem alegação de ganho de desempenho; nenhuma medição comparativa foi feita.
- **Integração:** supervisor deve atualizar mapa/documentação de produto dos quatro módulos e encaminhar estado estável ao auditor quando frontend também estabilizar. Auditor executa suíte Python/JS e verifica imports/ciclos e integridade de forma independente. Três falhas históricas JS da baseline não foram executadas, corrigidas ou classificadas novamente pelo backend.
- **Limites:** sem instalação ativa, rede real, Secret Service real, leitura de notas pessoais, teste gráfico ou publicação. Não há mudança de esquema/migração nova. Toda cópia futura para instalação precisa incluir os módulos novos junto aos chamadores; editar o repositório não instala nada.
