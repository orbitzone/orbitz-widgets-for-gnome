# Migração da identidade Orbitz — ID-01

## Contrato

Identidade nova: `orbitz-widgets@orbitzone.github.io`, schema `org.gnome.shell.extensions.orbitz-widgets`, URL GitHub Orbitz. Legado: `azclock@azclock.gitlab.com`, schema `org.gnome.shell.extensions.azclock`. A identidade GitHub é representada pelo UUID e URL; não é login/token ou prova de publicação de um site GitHub Pages.

Preparar e ativar são operações separadas. O agente não recarrega/desativa/ativa GNOME automaticamente. A instalação antiga e seu schema continuam disponíveis para retorno. JSON da agenda, banco SQLite e cofre não mudam de caminho nem são copiados ao repositório. O migrador trata a extensão existente; não é um instalador completo em máquina limpa para os demais aplicativos.

## Antes de preparar

Salvar trabalho, fechar preferências/agenda/YouTube e evitar alterar widgets ou configurações durante a preparação. Confirmar que a identidade nova não esteja habilitada. O migrador preserva binários/recursos da instalação antiga e aplica fontes novas em uma árvore separada; recusa links inesperados, destino já existente ou configuração nova conflitante. Não apagar/renomear manualmente diretórios para contornar recusa.

## Plano e preparo

```bash
/usr/bin/python3 /home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome/tools/migrate-identity.py
# Só o plano: deve indicar state=plan; não ativa nem instala.
/usr/bin/python3 /home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome/tools/migrate-identity.py --prepare
```

A revisão dirigida foi concluída em `docs/audits/2026-10-18-identity-audit.md`, inclusive correção/rechecagem do rollback após remoção parcial; não restam impeditivos reproduzidos no escopo auditado. O preparo real continua pendente. Sucesso de preparo (`state=prepared`) deve incluir caminho privado de backup e destino. Não equivale à ativação/validação visual. Erro MIGRACAO_NAO_CONFIRMADA não libera ativação. Backup privado fica em `${XDG_STATE_HOME:-~/.local/state}/orbitz-widgets/identity-backups/`; contém configuração local e manifesto, não deve ser publicado nem copiado para o Git.

## Ativação manual

1. Após confirmar preparo/hashes, verificar se GNOME descobriu a nova identidade: `gnome-extensions info orbitz-widgets@orbitzone.github.io`. Se não encontrou, manter a antiga habilitada e sair/entrar manualmente na sessão para descoberta; consultar novamente antes de desativar a antiga.
2. Com a nova identidade reconhecida, usar o aplicativo Extensões: desativar Desktop Clock/azclock, confirmar que está inativa e então ativar Orbitz Widgets for GNOME. Nunca habilitar ambas. Se a nova não ativar, mantê-la desativada e voltar à antiga, que não foi removida.
3. Conferir apenas Orbitz ativa, preferências/página Sobre com nome/GitHub/autor novos, posições/fontes/comandos preservados, controlador e dados existentes. Reabrir aplicativos fechados. Fazer roteiro de teste afetado e informar resultado; nova identidade não corrige automaticamente bugs já pendentes de RAM/dispositivos externos.

A necessidade de logout para descoberta e o carregamento real da nova extensão precisam ser conferidos no ambiente do usuário. Não afirmar que somente trocar arquivos já mudou o código carregado na sessão atual.

## Voltar ao legado

Desativar Orbitz e confirmar nova identidade inativa. Reativar o legado manualmente se necessário. Para desfazer o preparo, com o UUID novo desativado e sem alterações posteriores conflitantes:

```bash
/usr/bin/python3 /home/felipe/Documents/Codex/projects/orbitz-widgets-for-gnome/tools/migrate-identity.py --rollback /caminho/privado/da/execucao
```

Rollback do preparo restaura somente o estado de configuração anterior do schema novo e remove a árvore nova intacta, sem alterar dados de aplicativos nem a instalação/configuração legadas. Se houver edição posterior ou estado pendente, não forçar/apagar: informar erro e preservar manifesto para análise. Os backups operacionais DEP-01 anteriores continuam associados ao schema legado, nunca ao Orbitz por inferência.

## Estado de validação

Implementação e revisão dirigida concluídas; nenhuma aplicação/ativação real efetuada pelo agente. Suíte integrada auditada: 83 Python,18 arquivos Node,2 GJS e110 sintaxes; após ajuste pontual de retomada de rollback, 11 testes do migrador foram reexecutados/aprovados no alvo final, sem apresentar isso como nova suíte global. Legado/schema/licenças preservados e nenhum impeditivo restante no escopo revisado. Há limites de concorrência/ambiente e nenhuma comprovação visual nativa. Preparar no terminal do usuário e conferir state=prepared/destino/hashes antes de orientar descoberta/ativação/reinício. Não houve commit/push desta identidade nesta etapa.

## Ativação real confirmada — 18/10/2026

Usuário reiniciou sessão para descoberta, obteve INITIALIZED e executou disable legado seguido de enable Orbitz. Saída GNOME fornecida: State:ENABLED, UUID/nome/GitHub/autor/versão1 corretos. Supervisor conferiu enabled-extensions com somente Orbitz entre ambas. A etapa de ativação está concluída; testes visuais/funcionais ainda não equivalem a essa confirmação. Não há necessidade de novo reinício para começar teste. Manter legado/backup para retorno enquanto a validação estiver pendente.
