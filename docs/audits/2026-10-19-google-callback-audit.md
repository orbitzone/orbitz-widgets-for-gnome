# CAL-04 / RC-26 — callback Google

Revisão focada em 19/10/2026: quatro fontes e dois testes listados abaixo. Sem impeditivo reproduzido neste alvo.

O resultado validado agora é registrado antes da resposta HTTP; BrokenPipe/ConnectionReset não deixam o fluxo aguardando por perda da escrita. Validações de state, Host, endereço e caminho permanecem. Callbacks inválidos não sobrescreveram resultado aceito. No fluxo normal, `wait()` encerrou após o primeiro resultado, sem processar o callback repetido enfileirado; isso não é uma garantia geral de idempotência do Handler chamado isoladamente.

Erros OAuth usam somente códigos permitidos, corpo limitado a 4 KiB e endpoint POST exato; mensagens não expõem descrição, tokens ou códigos de autorização. Progresso usa quatro chaves fixas, guardas de tentativa/vida e preserva cancelamento/ACK. Falhas reabilitam login nos testes.

**Verificações:** `python3 -m unittest discover -s tests -p 'test_calendar*.py' -v`: 38 casos, 36 aprovados e 2 skips ambientais de socket. Oito cenários independentes sintéticos: ConnectionReset em cabeçalhos/corpo, sucesso/negação, callbacks inválidos/repetidos e HTTP 400/401/403. AST dos seis arquivos, hashes estáveis e diff check aprovados. Logs e script: `/tmp/orbitz-google-callback-audit/`.

**Limites:** sem suíte global, GUI, autenticação, cofre, contas reais ou aplicação instalada. Não comprova causa exclusiva do sintoma nem configuração Google válida. Revisão funcional e de segurança; sem aprovação visual ou medição de desempenho.

## SHA-256

- `extension/planner/calendar_http.py`: `ed6b7e1bf4c17e8260e997e469d29c590ce5c8bf9af13c0aef0ce5873c62ab29`
- `extension/planner/google_oauth.py`: `e3024164a02c671cdf2ddbdf798346302cacf40bd825ec242d3e240267e09ee1`
- `extension/planner/calendar_accounts.py`: `60569bbdbdc51014df3fff3bce53d0fb8136270be758a657ac7498979f80e98b`
- `extension/planner/provider_connection_ui.py`: `62a2475d1cd64191a187d4dc00d159cbb431c0e3d820bbcb46e75ef2ed50094c`
- `tests/test_calendar_providers.py`: `44f4f8faf4308224ab741b087284f4d013bde0750d54d7bf097d2dd2df4d4cae`
- `tests/test_calendar_frontend.py`: `325ebcc6854ca4d09c687ab62f6a83e97ac19c95c907a3609bd7a855f9f02997`
