# CAL-01/RC-22 — auditoria focada — 19/10/2026

**Parecer:** sem impeditivo reproduzido no escopo local. Nenhuma instalação, recarga, autenticação externa, navegador, Secret Service ou dado pessoal acessado.

**Alvo:** arquivos estáveis; manifesto SHA-256 `ef57d64113eb9ff8344fa37c5b57c3a9312a716e1b15cf928c9e0d75052e12e9` (sem mudanças antes/depois). Manifesto e logs completos em `/tmp/orbitz-calendar-audit/`.

**Testes:** `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p 'test_calendar*.py' -v`:29casos,**27aprovados/2skips**(0,555s). Skips: sockets reais recusados pelo sandbox; handlers de produção foram exercitados em memória, sem enfraquecer expectativas. `test_planner_backend.py`:8/8(1,320s); `node tests/test_identity.js`, ASTplanner/testes e diff-check aprovados. Nenhuma suíte global/QA PDF repetida.

**Integração independente:** clientesGoogle/Calendly reais com HTTP/OAuth/cofre mocks→cache realtemporário→duastarefas locais→backupWorkspace→disconnect. Backup exclui external-calendars/segredos; desconexão limpa cache/cofreRAM e cache tardio não recria conta; tarefas/horas preservadas byte a byte. Somente fixtures privadas temporárias.

**Revisão:** state/Host/path/PKCES256/limites/cancel/fechamento do loopback; configuração Desktop fornecida pelo usuário; endpointsHTTPSfixos e redirects recusados; paginação limitada sem trocar host/escopo; erros sem corpo/credenciais. Access somenteRAM, refresh/PAT/configsensível no cofre separado. Refresh serializado/rotação salva antes do cancel; omissão conserva grant. ACK UI/cancel desfaz conexão não aceita. Cache só recebe resposta completa e revalida conta; desconectar cancela sync e usa lock/cofre-aware. Sem escrita de calendário remoto ou exclusão de tarefas. Desconexão remove autorização local, não comprova revogação no provedor.

**Limites:** loopback real, GTK/foco/ACKruntime,cofre e OAuth/PAT reais pendentes; mocks não comprovam consentimento/API habilitada ou comportamento de serviço externo. Locks não garantem transação global contra storage/cofre falhando ou encerramento abrupto. Sem benchmark/garantia absoluta. About/identidade fonte passou; diagnóstico instalado pertence aos relatóriosfrontend, não repetido. Captura legado não prova causa de acionamento/cache; nenhuma edição especulativa da instalação legada.

Supervisor integra aceite/documentação/comando de atualização autorizado. Teste humano posterior com configuração própria deve validar cancelamento/conexão/sync/desconexão em ambiente permitido. Auditor não aplicou; reabrir Workspace após atualização verificada.
