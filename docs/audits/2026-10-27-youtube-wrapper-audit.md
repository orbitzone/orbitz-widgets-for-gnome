# Revisão focada — autenticação dos bridges WebKit

Data: 27/10/2026. Alvo: `/home/felipe/Documents/Codex/projects/orbitz-youtube-wrapper`.

## Conclusão

Revisei a validação ASCII e o limite de 4096 caracteres por mensagem. Prefixos não ASCII são rejeitados antes de `secrets.compare_digest`; mensagens longas, sem separador, com token ausente ou incorreto também retornam `None`. O novo caso de 4097 caracteres passou. O token de 192 bits permanece isolado do iframe cross-origin pelo path e lexical scope do documento principal, SOP e `strict-origin-when-cross-origin` no servidor e no iframe. Não encontrei bypass para qualquer dos três handlers.

Validações executadas no alvo atual: 19 testes Python, quatro testes Node, `git diff --check`, `desktop-file-validate`, AppStream e parse do manifesto — todos passaram. O antigo erro Unicode e o cenário de payload acima do limite estão cobertos no teste.

## Risco residual

O limite de tamanho remove o vetor prático de payload enorme. Um iframe ainda pode enviar mensagens inválidas pequenas repetidamente e causar chamadas limitadas de validação/comparação; não há rate limit, mas não observei efeito além desse trabalho curto. Risco baixo de disponibilidade, sem ação nativa ou bypass de autenticação. Playback/GUI real e compatibilidade visual continuam fora desta revisão.

## Acompanhamento do supervisor

Após esta revisão, o [CI 40608208765](https://github.com/orbitzone/orbitz-youtube-wrapper/actions/runs/40608208765), no commit de código `2f2f108`, passou com a autenticação por token, testes, importação WebKitGTK 4.1 e exportação do bundle x86_64. A prévia v0.1.0 foi publicada e seu SHA-256 conferido após download. Um commit posterior altera somente README/registro de validação. Este resultado fecha a pendência de build desta revisão; não valida GUI, reprodução com conta real ou compatibilidade visual de várias distribuições.
