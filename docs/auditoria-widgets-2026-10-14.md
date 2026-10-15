# Auditoria dos widgets — 14/10/2026

A revisão individual dos nove widgets e de suas dependências resultou em correções instaladas nos scripts ativos e na extensão. Foram preservados os intervalos existentes, os quatro grupos de colunas das temperaturas, o refresh manual e as funcionalidades anteriores.

## Resultado por componente

| Componente | Revisão e resultado |
|---|---|
| CPU/RAM/SSD | Amostragem de um segundo preservada; utilização de CPU limitada a 0–100% para evitar valores inconsistentes. Cache do disco mantido. |
| Processos | Consultas auxiliares usam limite de tempo e saída; RSS vem do mesmo arquivo stat já lido, eliminando uma leitura extra por processo. Os rankings usam seleção dos sete maiores, sem ordenar toda a lista duas vezes. |
| Tráfego de rede | Rotas truncadas são ignoradas antes de acessar campos; medição pelo tempo efetivamente transcorrido e tratamento de contadores negativos mantidos. |
| Temperaturas | Leituras inválidas são descartadas antes do estado e dos componentes. Quatro colunas fixas, separação críticos/auxiliares e ajuda preservadas. Descrições desconhecidas permanecem explícitas. Sem mudança de intervalo. |
| Conexões externas | DNS reverso limitado aos destinos que efetivamente serão exibidos; limite de 16 resoluções por consulta, quatro trabalhadores e cache mantidos. Nomes reversos não são usados como identidade confirmada. |
| Docker | Inspeção limitada aos primeiros 100 contêineres, em dois lotes; demais contêineres são informados. O contador continua incluindo todos os IDs da consulta ps. Falhas de inspeção não são apresentadas como ausência de contêineres. Corrigida a grafia Containers. |
| Firewall | Cursor e janela de 24 horas preservados. Leitura bruta agora tem orçamento adicional de 4 MiB por rodada, além do limite de registros e tempo. Cache validado por estrutura, tipos e limites antes do uso; arquivo de lock não segue links simbólicos. |
| Atualizações | Confirmação centralizada: EOF cancela a execução, assim como a ausência de entrada válida. IDs inexistentes são rejeitados. Cache anterior é validado, inclusive timestamps; desaparecimento de arquivos do índice APT é tratado. |
| Clima | Além de valores finitos, valida umidade, chuva, dia/noite e consistência mínima/máxima. Exceções esperadas de comunicação e dados são tratadas sem ocultar genericamente todo erro de programação. |
| Armazenamento externo | Removida importação redundante; flags de dispositivos são validadas; children=null não interrompe a travessia. Inventário em cache e deduplicação por dispositivo mantidos. |
| Coletor persistente | Scripts são compilados uma vez ao iniciar o coletor, evitando releitura e recompilação a cada atualização. CPU, processos e rede continuam compartilhando um processo. |
| Runtime compartilhado | Validação de nomes e timestamps de cache; recusa NaN/Infinity. Execução com limite de saída, timeout e watchdog nativo independente do processo principal. Ações no terminal compartilham uma implementação. |
| Extensão, relógios e mídia | Revisão estática de criação/destruição, timers, cancelamento, escape de texto e importação de configurações. Sintaxe de todos os arquivos JS verificada. Não há certificação visual nem medição da memória do GNOME nesta revisão. |

## Correções de maior impacto

1. **Confirmação das ações:** anteriormente a sequência continuava após EOF no terminal; agora read precisa completar antes da execução. Testado com um comando inofensivo e entrada vazia.
2. **Sobrevivência de subprocessos:** processos em sessão separada podiam sobreviver à morte do coletor. Um watchdog timeout do coreutils impõe o prazo mesmo após o encerramento abrupto do pai. Verificado com um filho que tentava criar um arquivo depois do prazo.
3. **Memória do firewall:** o limite de dez mil linhas não limitava suficientemente os bytes acumulados. Acrescentado teto de 4 MiB por rodada, com retomada pelo cursor.
4. **Cache corrompido:** estruturas inesperadas do firewall e das atualizações são rejeitadas antes de indexações internas.
5. **Trabalho desnecessário:** menos leituras de /proc, seleção parcial de rankings, compilação única dos scripts, DNS restrito à lista visível e inspeção Docker limitada.

## Validação

- 18 testes Python passaram: cancelamento por EOF, execução após Enter, timeout, saída excessiva, morte do processo pai, cache/link simbólico, estrutura de firewall, mais de 2.000 eventos, ruído, expiração, teto de bytes, consultas de processos, IDs de ações, limite de inspeção Docker, URLs inseguras, clima inválido, montagem inválida, rotas truncadas e sensores ausentes.
- Teste Node passou: quatro colunas, críticos à esquerda, auxiliares à direita e ausência de perda/duplicação de sensores.
- Todos os módulos Python compilam e todos os arquivos JavaScript passam na verificação de sintaxe.
- O coletor persistente entregou amostras válidas dos três modos.
- Os nove widgets tiveram execução real; cinco modais tiveram consulta de dados. Todas as execuções terminaram com código zero. Atualizações informou consulta indisponível do Flatpak, enquanto APT e Snap responderam; isso foi tratado como resultado parcial.
- Correções copiadas para os nove scripts ativos e suas dependências em três diretórios. Backups locais anteriores à instalação foram preservados.

## Medições pontuais

Uma execução por modo, sem benchmark comparativo antes/depois. Os tempos abaixo incluem a espera intencional das amostras; não representam consumo contínuo de CPU. RSS é o pico relatado por GNU time para a execução, podendo refletir um subprocesso, e não o consumo residente do GNOME.

| Widget / modo | Tempo total (s) | CPU usuário+sistema (s) | Pico RSS (MiB) |
| cpu-ram-widget.py / summary | 1.08 | 0.08 | 11.8 |
| processos-widget.py / summary | 1.07 | 0.06 | 12.5 |
| rede-widget.py / summary | 1.05 | 0.04 | 9.8 |
| temperaturas-widget.py / summary | 0.09 | 0.07 | 12.1 |
| seguranca-widget.py / summary | 0.23 | 0.09 | 13.0 |
| docker-widget.py / summary | 0.09 | 0.08 | 30.8 |
| firewall-widget.py / summary | 0.24 | 0.25 | 39.3 |
| atualizacoes-widget.py / summary | 1.96 | 0.92 | 100.2 |
| clima-widget.py / summary | 0.07 | 0.05 | 17.6 |
| processos-widget.py / details | 0.82 | 0.21 | 19.8 |
| temperaturas-widget.py / details | 0.08 | 0.06 | 11.8 |
| seguranca-widget.py / details | 0.59 | 0.09 | 13.4 |
| docker-widget.py / details | 0.14 | 0.13 | 31.1 |
| firewall-widget.py / details | 0.25 | 0.26 | 39.3 |

O pico de Atualizações inclui as ferramentas de pacotes, consultadas na abertura/refresh, e não indica um daemon de 100 MiB permanentemente residente.

## Limites e manutenção

Esta revisão não garante ausência absoluta de bugs ou vulnerabilidades. Não inclui auditoria do kernel, drivers, Docker daemon, serviços remotos ou dependências de terceiros. O ambiente restringe a visibilidade dos processos; os rankings devem também ser verificados na sessão real do usuário. Falhas de filesystem/rede, corrida de atualização de arquivos e cargas extremas continuam dependendo do sistema operacional.

As amostras de CPU/processos/rede continuam sequenciais no coletor. Em intervalos muito curtos ou com mounts lentos, a cadência pode atrasar; o watchdog limita subprocessos, mas não certifica o tempo de chamadas de filesystem em estado ininterruptível. Não foi feita medição prolongada de vazamento de memória, ciclos de login/logout nem validação visual das modais no GNOME.

Comandos configurados pelo usuário e ações personalizadas continuam podendo executar código com os privilégios da conta. Isso é uma funcionalidade explícita e exige configurações de confiança; não é uma sandbox de comandos. Nenhuma regra do firewall ou privilégio administrativo foi alterado.

Para alterações futuras, executar no repositório:

```bash
python3 -m unittest discover -s tests -v
node tests/test_temperature_layout.js
```

Também verificar sintaxe dos módulos, consultar os widgets afetados e revisar a interface na sessão GNOME antes de publicar alterações. Os testes cobrem regressões específicas; não substituem revisão de segurança nem garantem desempenho em qualquer máquina.
