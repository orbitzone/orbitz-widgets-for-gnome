# Revisão geral do YouTube Wrapper e Orbitz Runner — 28/10/2026

## Alvo e escopo

Repositório local `../orbitz-youtube-wrapper`, commit `cb35043`, checkout limpo no início da revisão. Escopo: app GTK/WebKit, servidor loopback, chave e chamadas da YouTube Data API, permissões Flatpak e mini game Orbitz Runner. Revisão de código e testes sintéticos; sem alterações de implementação.

## Achados

### YT-AUD-01 — recomendações obsoletas podem aparecer em outra aba (P2, reproduzido)

Em `app/index.html`, `loadRecommendations()` compara apenas `sequence` após a resposta. Trocar de Videos para Shorts, Live ou Podcasts com a busca vazia não incrementa essa sequência; a resposta pendente preenche a aba selecionada com recomendações genéricas. Reproduzido com VM Node: iniciar recomendações pendentes, abrir Shorts vazio, resolver a resposta; `renderResults()` recebe os resultados e o status muda para `youtube.recommendations`. A revisão independente confirmou.

Aceite sugerido: invalidar a sequência em toda mudança de aba ou conferir aba `videos` e busca vazia antes de renderizar (inclusive no caminho de erro). Teste deve cobrir resposta pendente para cada aba vazia.

### YT-AUD-02 — formato inesperado da configuração interrompe leitura e fallback (P2, reproduzido)

Em `app/youtube_api.py`, `read_key()` chama `.get()` diretamente no resultado de `json.loads()`. JSON válido como `[]` ou `null` lança `AttributeError`, que não é capturada. Se o arquivo atual estiver assim, a função não tenta a configuração legada válida; chamadas de API podem falhar sem erro tratado. Reproduzido com arquivos sintéticos temporários, sem acessar credenciais. A revisão independente confirmou.

Aceite sugerido: aceitar somente objeto JSON com campo de chave em formato válido; tratar tipo/forma inválida como configuração inválida e continuar para o próximo caminho. Adicionar testes para lista, `null`, objeto sem chave, JSON inválido e fallback legado.

### YT-AUD-03 — limite do bridge ocorre depois de converter mensagem WebKit (P2, risco inferido)

Em `app/youtube-wrapper.py`, os handlers chamam `result.get_js_value().to_string()` antes de passar o texto a `bridge_payload()`, onde o limite de 4096 caracteres é aplicado. Uma mensagem grande originada numa frame pode exigir conversão/alocação no processo GTK antes de ser rejeitada; mensagens repetidas também podem acumular trabalho. Não há bypass de autenticação reproduzido. A revisão independente não testou WebKitGTK real, portanto o impacto é inferido.

Aceite sugerido: limitar a conversão/custo no limite WebKit quando a API permitir, ou redesenhar o bridge para mensagens pequenas e de formato fixo; confirmar com teste adversarial no WebKitGTK e medição de CPU/memória.

### YT-AUD-04 — trocas rápidas de filtro podem manter consultas API obsoletas (P3, risco de quota/desempenho)

O frontend invalida a renderização por sequência, mas não cancela as requisições `fetch`; o servidor aguarda cada chamada de rede por até 10 segundos. Ao trocar rapidamente entre filtros com uma consulta preenchida, respostas obsoletas são ignoradas pela interface, mas as solicitações continuam consumindo tempo e possivelmente quota da API. Não medi o impacto nem reproduzi quota excedida; é um risco de uso acelerado, não uma causa confirmada da baixa performance.

Possível melhoria: debounce/deduplicação por consulta e modo, limitar chamadas simultâneas e descartar trabalho obsoleto onde o transporte permitir.

## Resultados positivos e desempenho observado no código

- `make test`: 25 testes Python e seis scripts JavaScript passaram. `python3 -m py_compile app/*.py i18n/*.py` e `git diff --check` passaram; checkout do wrapper permaneceu limpo.
- Auditoria independente: 11 testes Python de fronteira, 14 de dimensionamento e testes JavaScript direcionados de runner/links passaram. Não repetiu a suíte ampla.
- Consultas e comentários validam os parâmetros, têm timeout de rede de 10 s e limitam respostas a 256 KiB e 1 MiB. As caches em memória de busca/comentários têm limites. A chave local é gravada com modo 0600; o Flatpak não pede acesso geral à pasta pessoal.
- O Runner não inicia animação automaticamente. O loop começa após ação do usuário, limita quadros a 60 fps, usa escala de canvas limitada a DPR 2 e para quando o documento fica oculto ou o player aparece. Não há loop contínuo enquanto o jogo está parado.
- Renderização textual de título, canal e comentários usa `textContent`; IDs, filtros e URLs de clipboard/links nativos têm validação.

## Limites

Não foi feita inspeção visual, execução de vídeo com chave/conta real, teste adversarial dentro de WebKitGTK, build/execução de Flatpak nem medição de FPS, CPU, memória ou latência numa sessão gráfica. O bundle v0.1.0 instalado não foi atualizado e esta revisão cobre somente as fontes em `cb35043`. Assim, não confirma nem descarta a causa de um problema de desempenho relatado em uma máquina específica.

Nenhum código, instalação, credencial ou publicação foi alterado nesta revisão.

## Resposta aos achados (28/10/2026)

Após a revisão, as fontes em `../orbitz-youtube-wrapper` foram corrigidas. YT-AUD-01 agora invalida requisições e confere aba/consulta antes de renderizar recomendações; há regressão assíncrona. YT-AUD-02 aceita só objeto JSON com chave válida e mantém o fallback legado; há casos para array, null e string. Para YT-AUD-03, o bridge WebKit foi removido em favor de três ações no servidor loopback: o token da sessão e Origin exato são verificados, o corpo é limitado a 4096 bytes antes do parse e o JSON precisa ser objeto; links externos e de clipboard seguem validação explícita. Para YT-AUD-04, troca rápida de filtro agrupa a busca por 180 ms e aborta o fetch anterior na UI. Uma chamada já iniciada no worker Python pode continuar até completar ou expirar; cancelamento do cliente não garante cancelamento da consulta ao Google.

Validação local em `orbitz-youtube-wrapper`: 27 testes Python e sete JavaScript passaram via `make test`; `py_compile`, verificação dos scripts, manifesto Flatpak e diff-check passaram. Ações GTK/WebKit e mitigação do bridge ainda aguardam revisão independente. Não há teste gráfico, chamada real à API, medição de CPU/memória/FPS ou build novo do Flatpak, portanto nenhum ganho de desempenho em execução real foi medido. O README do wrapper foi inteiramente reescrito para apresentar o app, orientar primeiro uso e explicar privacidade/limites. A release v0.1.0 e a instalação local continuam sem estas alterações.

A revisão do fechamento também reproduziu que o botão Buscar ficava desativado ao sair para Comentários enquanto uma requisição estava pendente. `setTab()` agora reativa o botão após abortar o fetch e `tests/test_youtube_search_abort.js` cobre o estado pendente/abortado; a suíte passou com 27 Python e oito JS. A revisão independente confirmou a correção e não encontrou bypass óbvio ou deadlock no fluxo normal do novo endpoint. A integração GTK/WebKit real e todos os caminhos temporais do debounce/dispatcher não foram exercitados. Se a thread GTK não atender em cinco segundos, uma ação já enfileirada pode executar após a resposta de timeout; o revisor não classificou isso como bloqueador.
