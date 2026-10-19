<p align="center">
  <img src="extension/media/orbitz-logo.svg" alt="Logo Orbitz" width="112">
</p>

# Orbitz Widgets for GNOME

**Seu desktop conectado ao seu trabalho.**

Acompanhe o computador, organize compromissos e transforme horas trabalhadas em faturas — em um ambiente integrado ao GNOME. O Orbitz combina widgets na área de trabalho com o **Orbitz Workspace**, um espaço para agenda, tarefas, horas e faturamento.

[Conheça o Workspace](#do-compromisso-à-fatura) · [Explore os widgets](#um-desktop-que-trabalha-com-você) · [Comece por aqui](#comece-por-aqui)

![Visão dos widgets Orbitz na área de trabalho](docs/images/desktop-widgets.png)

## Um desktop que trabalha com você

Informações à vista, sem precisar abrir uma janela para cada consulta. Personalize posições, aparência e agrupamentos para montar o seu painel de trabalho.

| Para acompanhar | O que você encontra |
|---|---|
| Seu dia | Relógio, data, clima e alertas de compromissos e tarefas. |
| O computador | CPU, memória, armazenamento, processos, temperaturas e serviços. |
| A conexão | Tráfego, qualidade da rede, conexões e portas em escuta. |
| A manutenção | Atualizações de pacotes, informações do firewall e contêineres Docker. |
| Suas ferramentas | Controles de mídia, Sticky Notes, player do YouTube e lançadores. |

Os widgets começam pausados ao entrar na sessão. Use o controlador branco para abrir ou fechar o conjunto. Fechar os widgets preserva os dados salvos; ações que você iniciou em terminais continuam com seu próprio ciclo de execução.

## Do compromisso à fatura

O **Orbitz Workspace** reúne cinco áreas para acompanhar o trabalho do início ao fim:

| Área | O que você faz |
|---|---|
| **Hoje** | Veja tarefas pendentes, atrasadas, cronômetros e compromissos já sincronizados da fonte selecionada. |
| **Agenda** | Consulte calendários conectados e transforme eventos em tarefas quando desejar. |
| **Tarefas** | Organize entregas por data, configure lembretes e registre horas ao concluir uma atividade. |
| **Horas** | Separe timesheets por empresa ou projeto, registre atividades e acompanhe totais. |
| **Invoices** | Gere faturas em PDF, consulte emissões anteriores e organize versões dos documentos. |

### Planeje com seus calendários

Conecte **Apple/iCloud**, **Google Calendar**, **Calendly** ou assinaturas **ICS**. A integração consulta os eventos; criar uma tarefa a partir de um compromisso é uma ação sua. Desconectar um calendário preserva as tarefas e as horas locais.

A sincronização acontece com o Workspace aberto, com atualização periódica e consulta manual. Os lembretes da extensão podem usar eventos já sincronizados mesmo com a janela fechada; eventos de dia inteiro não geram esses alertas.

Cada conexão tem seus requisitos: senha específica de aplicativo no iCloud, configuração OAuth desktop própria no Google e token pessoal no Calendly. Credenciais ficam no cofre do sistema. Veja os [passos e requisitos das integrações](docs/operations/calendar-integrations.md).

### Dê contexto às horas trabalhadas

Cada timesheet tem um nome e referências opcionais de cliente, contrato ou projeto e departamento ou centro de custo. Registre manualmente ou use o cronômetro; acompanhe totais por dia, semana e mês, recupere rascunhos e exporte CSV.

Ao concluir uma tarefa, você pode registrar o trabalho na timesheet escolhida. Avisos de sobreposição ajudam na revisão dos horários. Timesheets antigas podem ser arquivadas e consultadas, sem misturar seus registros com os projetos ativos.

### Emita e acompanhe suas faturas

Escolha a timesheet e o período: um mês civil, todo o histórico ou um intervalo selecionado no calendário. Preencha emitente, destinatário, valor por hora e moeda; revise a prévia e salve o PDF em **português ou inglês**.

Após salvar o PDF, emitente e idioma são lembrados para as próximas emissões; cliente, taxa e moeda ficam separados por timesheet. Cancelar não grava essas alterações.

O cálculo usa os minutos dos registros concluídos e arredonda o valor apenas no total. Cronômetros em andamento e registros na lixeira ficam de fora. A moeda é independente do idioma. Referências de projeto e departamento aparecem separadas dos dados fiscais do cliente.

O histórico organiza as emissões por timesheet, cliente e mês de emissão, mantendo cópias independentes dos arquivos exportados. Avisos ajudam a identificar horas possivelmente faturadas antes, com confirmação para reemissões intencionais. O pagamento pode ser informado manualmente, sem alterar o PDF ou representar confirmação bancária.

As faturas são **documentos de serviços**, sem emissão de NFS-e, cálculo de impostos ou integração fiscal oficial.

### Assine com um fluxo assistido

Salve uma cópia e continue no assinador gov.br pelo navegador. Depois de assinar e baixar o documento manualmente, importe uma versão vinculada à invoice: o original e as versões anteriores permanecem preservados.

As versões importadas ficam com **validação pendente**. O acesso ao portal VALIDAR também é manual; abrir o portal não altera o status. O Orbitz não faz login por você, não guarda senha gov.br, não envia documentos automaticamente e não verifica criptograficamente a assinatura ou a correspondência do arquivo importado.

## Notas, mídia e atalhos por perto

Use **Sticky Notes** para ideias e lembretes soltos, com salvamento local e backups próprios. Controle players compatíveis pelo painel de mídia e abra vídeos em uma janela dedicada do YouTube. Pesquisa e comentários do player exigem uma chave própria da YouTube Data API.

Lançadores para ferramentas como btop e Gemini complementam o desktop, conforme os aplicativos disponíveis no computador.

## Seus dados e seus backups

Tarefas, horas, perfis de faturamento e histórico de invoices são armazenados localmente. Conexões externas são usadas para os serviços que você escolhe integrar; as credenciais desses calendários ficam no Secret Service do sistema.

O **backup completo do Workspace** inclui tarefas, horas, contextos, perfis, invoices, versões, pagamentos manuais e estado da interface. A restauração oferece prévia, confirmação e uma cópia do estado anterior. Encerre os cronômetros e feche outros editores antes de restaurar; depois, reabra o Workspace.

O backup contém dados privados e **não é criptografado por senha**. Guarde-o em local seguro. Credenciais, calendários externos, Sticky Notes e configurações dos widgets ficam fora desse arquivo; as notas têm seu próprio armazenamento e backup. Excluir uma invoice do histórico remove o registro e suas versões gerenciadas, preservando os PDFs exportados e as horas trabalhadas.

## Comece por aqui

O Orbitz está em evolução. O ambiente de referência é **Ubuntu 22.04 com GNOME 42.9**; o manifesto declara GNOME **42, 43 e 44**. Não há suporte declarado a GNOME 45 ou posterior, e a instalação completa em máquina limpa ainda não foi validada.

- **Já utiliza o Orbitz?** Consulte o [guia de atualização local](docs/operations/local-update.md). Alterar ou baixar as fontes não atualiza automaticamente os aplicativos instalados.
- **Utiliza uma instalação antiga do Desktop Clock/azclock personalizada como Orbitz?** Siga o [guia de migração de identidade](docs/operations/identity-migration.md), preservando configuração e dados. Mantenha somente uma identidade ativa.
- **É sua primeira instalação?** Consulte a [plataforma e as dependências](stack.md) antes de preparar o ambiente. As ferramentas atuais atendem à atualização e à migração de instalações existentes; ainda não há um instalador completo validado para uma máquina nova.

Os principais requisitos são Python 3, PyGObject, GTK e as bibliotecas do GNOME. A exportação de faturas usa `python3-reportlab` e `fonts-dejavu-core`; o player do YouTube precisa de WebKitGTK. Recursos como Docker, sensores, firewall e consultas de pacotes dependem das ferramentas e permissões disponíveis na máquina.

Com a extensão instalada, abra suas preferências com:

```bash
gnome-extensions prefs orbitz-widgets@orbitzone.github.io
```

Após atualizar módulos do Workspace, feche e reabra o aplicativo. Atualizações dos coletores do resumo exigem parar e abrir os widgets pelo controlador para iniciar a nova coleta.

### O que considerar nesta versão

As funcionalidades passaram por verificações locais de lógica e integridade, mas a validação interativa de todas as telas, provedores e configurações de hardware ainda está em andamento. A abertura do painel de RAM e o comportamento de dispositivos externos têm pendências conhecidas. Google Calendar e Calendly ainda precisam de validação completa com contas e cofre reais.

Sensores e consultas do sistema podem estar indisponíveis por suporte do hardware ou permissões. A análise do firewall auxilia a inspeção dos registros; não determina, por si só, que houve um ataque. Comandos personalizados executam com as permissões do usuário, e ações de manutenção são iniciadas manualmente.

## Projeto e comunidade

Desenvolvido e mantido por **Felipe Santiago / orbitzone**.

Encontrou um problema ou tem uma sugestão? [Abra uma issue](https://github.com/orbitzone/orbitz-widgets-for-gnome/issues), informando a versão do GNOME, os passos e o resultado esperado. Remova documentos pessoais, tokens e senhas de capturas ou logs antes de compartilhá-los.

O projeto tem origem no Desktop Clock/azclock, de Andrew Zaech, e preserva as atribuições de código, recursos e dependências. Consulte os [créditos e licenças](docs/credits.md) e o [LICENSE](LICENSE).
