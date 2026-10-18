# RAM sem modal — investigação frontend — 18/10/2026

Estado: **diagnóstico aberto; falha real não reproduzida isoladamente**. CPU e SSD foram confirmados normais pelo usuário após correção CLI; essa correção não encerra o sintoma RAM. O usuário confirmou que nenhuma parte da linha RAM abre, mesmo com os outros modais fechados. Não se repetiram essas perguntas.

## Evidências

- Dependências de storage.js e montagem de métodos permanecem completas. Revisão de `_checkNetworkClick` cobre inside/paint visibility, bloqueio desktop/modal, captura press/release, distância, igualdade dos targets e caminho até `_openNetworkDialog`; não foi identificada condição exclusiva de RAM que justifique correção de produção.
- Supervisor confirmou hash instalado igual ao repositório e ausência de erro pertinente no journal consultado por ele.
- Ensaio temporário GJS/PangoCairo sem janela com texto CLI exato (newlines inicial/final, linhas vazias, monospace sobre Cantarell8, alinhamento CENTER) identificou RAM nas larguras natural, 120, 220 e 440. Wrap estreito conservou a associação das linhas. Nenhuma afirmação de validação Clutter/entrada real decorre desse ensaio.
- Novo teste persistente `tests/test_stats_pango.gjs` usa PangoCairo real e o método `_storageTarget` extraído do arquivo atual. Reproduz padrão histórico confirmado pelo supervisor/usuário: span monospace size7680, line_height1.5, barra8, prefixo/colunas exatos restaurados pelo backend e linhas compactas com/sem EXT. Verifica CPU/RAM/SSD/EXT em três pontos de cada linha (início, meio, fim), nas larguras natural/220/440. **Passou** com `gjs tests/test_stats_pango.gjs "$PWD"`.
- Testes Node prévios usam atores sintéticos e não substituem esta geometria Pango; esta geometria tampouco substitui layout offsets/transformações/oclusão do Clutter real.

## Separação da regressão visual

Supervisor comprovou divergência do markup histórico e acionou backend para restauração mínima, sem redesign ou alteração de GSettings. UX recebeu captura do usuário e valores históricos/configuração enviados pelo supervisor. Esse reparo visual é confirmado; **não se afirma que ele explique ou resolva a falha RAM**.

## Próximo passo coordenado

Por orientação do supervisor, não preparar instrumentação agora. Restaurar apresentação, aplicar somente por atualização verificada sob responsabilidade dele e retestar RAM. Se persistir, há proposta de diagnóstico temporário restrito a transições press/release, estados de bloqueio, coordenadas/offsets e targets permitidos, sem conteúdo do widget/janelas/credenciais; isso depende de tarefa explícita e não foi implementado.

Frontend não alterou código de produção, GSettings, backend ou instalação nesta investigação. O único novo teste mantido é GJS direto; não aumenta a lista de entrypoints Node. Nenhuma sessão ativa, janela ou socket gráfico foi acessado. Sem novas tentativas Broadway, suíte global, commit ou push. Pendente: confirmação RAM no ambiente do usuário após restauração e, se necessário, evidência Clutter direcionada.

## Marco de restauração recebido

Backend informou apresentação estável e 9 testes de entrypoints aprovados (evidência própria em `2026-10-18-backend-hardware-markup.md`). UX entregou `docs/design/2026-10-18-hardware-restoration.md`; parecer encaminhado ao supervisor. Destaca override de fonte 10px no CPU agrupado: Text_Size8 sozinho não define a fonte efetiva; o markup size7680 confirmado é o critério concreto de restauração. A captura atual não comprova antes/depois. Cruzamento dos contornos Hardware/Sistema foi observado sem atribuir causa/novidade ou propor mover widgets. Teste GJS foi atualizado à fixture exata com/sem EXT e passou. Sem nova alteração de produção frontend. Reteste RAM real e revisão visual continuam pendentes.
