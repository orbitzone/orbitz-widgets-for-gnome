# CAL-05 / RC-27 — configuração privada do cliente Google

Revisão focada em 19/10/2026, sem impeditivo reproduzido no alvo abaixo. Nenhum JSON ou segredo real foi lido.

Configuração opcional privada exige cliente Desktop correspondente, secret, endpoints permitidos, proprietário e permissões restritas; arquivo presente inválido não produz fallback silencioso. Importador recusa origem/destino no repositório, links e sobrescrita diferente sem `--replace`; grava temporário 0600 em diretório 0700, publica atomicamente e limpa temporários. Refresh permanece usando configuração do grant existente, sem substituir por configuração local nova.

Diagnóstico HTTP mostra etapa/status e mensagens fixas; somente duas descrições exatas de parâmetro ausente recebem orientação específica. Nenhum corpo arbitrário ou segredo foi exposto nos testes. `.gitignore` cobre nomes previstos, mas não substitui a exigência de manter credenciais fora do repositório.

**Verificações:** suíte de configuração 8/8; providers 29 casos, 27 aprovados e 2 skips ambientais de socket. Seis cenários independentes sintéticos: proprietário incorreto, fsync anterior ao commit, arquivo acima de 32 KiB, FIFO e CLI check/falha sem valores. Arquivo anterior preservado e temporários removidos na falha simulada. AST, diff check e hashes estáveis aprovados. Evidências em `/tmp/orbitz-google-client-config-audit/`.

**Limites:** sem rede, login, tokens, cofre real, configuração privada real ou instalação; sem suíte global/GUI. O fluxo revisado atende configuração local do mantenedor; não comprova login real nem distribuição pública universal pronta. Falha de fsync após publicação não equivale a rollback garantido; o cenário verificado foi anterior ao commit.

## SHA-256

- `extension/planner/google_oauth.py`: `1aebf01e275711e2e42c72791344107597d7edebb203450d9da96124e2479ca6`
- `extension/planner/calendar_http.py`: `6e3e61483122fb5cd1c7c71264b30710e57178701a65230c113121221b92ea90`
- `tools/configure-google-client.py`: `374910ec383926a9f290b3db2883ccf1627cc910eb9ac21e6ccec92143f365ef`
- `tests/test_google_client_config.py`: `6bd26d90c75199b1e06b05b87c8e40dcd80ef04b054220128f66d3dcfe815c46`
- `tests/test_calendar_providers.py`: `14491ebf65568cb3daa43ba946c57bea37dc756b016cddf47a3ae3efe6356015`
- `.gitignore`: `64791ad2aefbca26f2c1320e26e4a45ad6f10a2ea8f48ef87ebc71e4d5f1e4af`
