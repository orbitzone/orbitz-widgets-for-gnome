# Sticky Notes independente — evidência consolidada

Data: 27/10/2026. Pedido RC-57: repositório próprio no GitHub e instalação entre distribuições Linux. Repositório: https://github.com/orbitzone/orbitz-sticky-notes. Prévia: v0.1.0. Código do pacote: `b2db81a1497ff4a16dfce7101c43c294789fe466`.

## Revisões independentes

Auditor existente da equipe revisou Makefile/DESTDIR, launcher, manifesto Flatpak, CI e independência de traduções/schema/importação. Dois testes de staging/catálogos e validadores desktop/AppStream passaram. Sem acesso geral à home/rede; X11 explícito e armazenamento no sandbox. Parecer: fontes aptas à publicação, bundle condicionado ao CI.

Rodadas de CI expuseram espera insuficiente no teste GTK (corrigida mantendo todos os asserts) e disputa real em PRAGMA journal_mode=WAL entre inicializadores. Backend acrescentou lock antes de sqlite.connect, timeout monotônico de 3s para adquirir lock, fechamento do cursor PRAGMA e da conexão em erro. Não há deadline global de inicialização; demais limites anteriores permanecem. Auditor revisou o delta e executou quatro testes novos de startup, cinco de storage/i18n e a regressão de concorrência original sem falha. Recomendação de confirmar que o segundo processo realmente encontrou flock ocupado foi incorporada; quatro testes novos repetidos com sucesso. O lock coordena versões novas; clientes antigos/outros escritores permanecem sujeitos aos limites SQLite existentes.

## Resultado de integração

[CI 40580644944](https://github.com/orbitzone/orbitz-sticky-notes/actions/runs/40580644944): **90 testes aprovados sem skips**, Ubuntu 24.04/Python 3.12/Xvfb. Desktop/AppStream válidos; runtime/SDK GNOME 49 instalados no runner; build/export/bundle x86_64 e importação de storage/card/tradução no sandbox passaram. Localmente, 37 testes de armazenamento e testes de staging passaram em Python 3.10/SQLite 3.37.

Bundle `orbitz-sticky-notes-x86_64.flatpak`: SHA-256 `59718f8bf32e8f2515e3570487fcd2e158d6d00e554e3b73ddcece941677201e`. Release inclui SHA256SUMS; checksum não é assinatura de identidade.

## Limites e instalação

Nenhuma instalação ativa ou dado pessoal foi alterado. Não há migração automática, publicação Flathub ou atualização automática por repositório Flatpak. O app integrado e suas pastas históricas foram preservados. Correção de startup permanece somente no repo independente; eventual backport exige validação própria.

CI com display virtual e importação do sandbox não homologam a experiência integral instalada, portais de links, GNOME/KDE/Xfce reais, escalas/monitores ou ARM64. Wayland requer XWayland nesta prévia; não há suporte declarado a qualquer Linux, Windows ou macOS. O PIN continua sendo bloqueio visual, sem criptografia de SQLite/backups. O novo README explica caminhos de dados, download, instalação, reabertura e limites. Neste repositório apenas documentação mudou; não executar update-local para esta entrega e não reiniciar a sessão.
