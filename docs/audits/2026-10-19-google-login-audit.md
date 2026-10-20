# CAL-03/RC-25 — login Google padrão — 19/10/2026

**Parecer:** sem impeditivo reproduzido no recorte. Diff contra CAL-01 limitado ao ID público/configdefault, remoção do chooserJSON e testes; state/PKCE/Host/ACKcancel e Calendly mantidos.

`PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p 'test_calendar*.py' -v`:32casos,**30aprovados/2skips**(0,631s). Skips são os sockets reais bloqueados anteriormente; handlerproduçãoemmemória passou. AST4arquivos aprovada; hashes antes/depois iguais. Logs completos `/tmp/orbitz-google-login-audit/tests.log`. Sem suíte global/reintegração completa/redeauthreal/instalação.

Default retorna cópia nova contendo somente o clientID público fornecido; teste proíbe os.open nesse caminho. TokenPOST/refresh default não incluem client_secret inventado; mantêm verifier e grant anterior quando refresh_token omitido. ConfigDesktop customizada e grants antigos com secret fornecido permanecem compatíveis. UI Google passa None, usa nomeopcional/default e EntrarcomGoogle, sem chooser/leituraJSON; PATCalendly/limpeza e handshakecancel intactos.

[Documentação oficial Google](https://developers.google.com/identity/protocols/oauth2/native-app), consultada19/10/2026: client_secret opcional na trocaStep5 e refresh. Isso **não valida o tipoDesktop do ID fornecido, consentimento, APIhabilitada ou tokenreal**. Loopback/SecretService/GTK/contareais pendentes; nenhuma credencialprivada solicitada/lida. Supervisor mantém documentação pública e coordena aplicação/teste manual, sem alteração pelo auditor.

## Hashes

| Arquivo | SHA-256 |
|---|---|
| `extension/planner/google_oauth.py` | `2e2b13265d75ad0a8862c234c0472231cb3d3cabc6ab4ef82c6d97b38fe3a5e1` |
| `extension/planner/provider_connection_ui.py` | `a6dfe02174e78f5baaf7703f062d389dd6b2eb09514f8b2c82cb717e2c5878a7` |
| `tests/test_calendar_providers.py` | `22d2e8bafc2d9d8f949bf6ad3c706ada4656002f428546f9c60205dc796790c1` |
| `tests/test_calendar_frontend.py` | `d8fca9de7ed14a25602ac34f1e14ab6d9f184c1931ed3e30394f74d3dd5c4232` |
