<p align="center">
  <img src="extension/media/orbitz-logo.svg" alt="Logo Orbitz" width="112">
</p>

# Orbitz Widgets for GNOME

**Seu dia, seu trabalho e seu computador em um só lugar.**

Monte um desktop que acompanha sua rotina. Com o Orbitz, você vê o que acontece no computador, organiza compromissos e tarefas, registra horas e prepara faturas sem perder o contexto do trabalho.

Os widgets trazem as informações para a área de trabalho. O **Orbitz Workspace** conecta o planejamento à entrega: da agenda ao registro de horas, até o PDF enviado ao cliente.

[Explore os widgets](#seu-desktop-do-seu-jeito) · [Conheça o Workspace](#do-planejamento-à-fatura) · [Primeiros passos](#comece-por-aqui)

![Widgets Orbitz na área de trabalho](docs/images/desktop-widgets.png)

## Seu desktop, do seu jeito

Escolha o que acompanhar, ajuste a aparência e organize os widgets em posições e grupos que fazem sentido para você.

| Na sua rotina | No Orbitz |
|---|---|
| Planejar o dia | Relógio, data, clima e alertas de compromissos e tarefas. |
| Acompanhar o computador | CPU, memória, armazenamento, processos, temperaturas e serviços. |
| Entender a conexão | Tráfego, qualidade da rede, conexões e portas em escuta. |
| Cuidar do sistema | Atualizações de pacotes, informações do firewall e contêineres Docker. |
| Ter suas ferramentas por perto | Notas adesivas, controles de mídia, player do YouTube e lançadores. |

Ao entrar na sessão, os widgets começam pausados. Use o controlador branco para abrir ou fechar o conjunto, preservando seus dados salvos. Ações iniciadas em terminais continuam com seu próprio ciclo de execução.

## Do planejamento à fatura

O **Orbitz Workspace** reúne cinco áreas para organizar o trabalho com continuidade.

| Área | Para você |
|---|---|
| **Hoje** | Um resumo de tarefas pendentes e atrasadas, cronômetros e compromissos sincronizados da fonte selecionada. |
| **Agenda** | Seus calendários conectados, com a opção de transformar eventos em tarefas. |
| **Tarefas** | Entregas por data, lembretes e registro de horas ao concluir uma atividade. |
| **Horas** | Timesheets por empresa ou projeto, registros manuais, cronômetros e totais por período. |
| **Invoices** | Faturas em PDF, histórico de emissões, versões e acompanhamento manual de pagamentos. |

### Traga seus calendários

Consulte **Apple/iCloud**, **Google Calendar**, **Calendly** e assinaturas **ICS** no Workspace. Você decide quando um compromisso vira tarefa. As integrações consultam eventos, e desconectar uma conta preserva suas tarefas e horas locais.

**Brasil · Datas comemorativas** é uma fonte pública padrão, sem login. Ela permanece em Gerenciar conexões: você pode desativá-la e reativá-la quando quiser. Desativada, ela deixa de atualizar e marcar o calendário, preservando suas tarefas e horas.

No Google, use **Entrar com Google** e autorize o acesso pelo navegador; a conexão está pronta quando o calendário aparece no seletor. O iCloud exige senha específica de aplicativo, e o Calendly usa token pessoal. As credenciais ficam no cofre do sistema. Consulte o [guia de integrações](docs/operations/calendar-integrations.md) para os requisitos de cada serviço.

Ao escolher um dia, a Agenda explica as marcações do calendário: eventos da fonte selecionada, feriados conhecidos de outras fontes e atividades locais. Tarefas e horas continuam em suas áreas próprias, com atalhos para consulta. A data destacada é a seleção atual; o sublinhado dourado identifica feriado.

A sincronização ocorre com o Workspace aberto, automaticamente em intervalos ou por atualização manual. Com a extensão ativa, os lembretes podem usar eventos já sincronizados mesmo após fechar a janela. Eventos de dia inteiro não geram esses alertas.

### Transforme atividade em horas organizadas

Separe o trabalho por empresa ou projeto, dê um nome a cada timesheet e acrescente referências de cliente, contrato e departamento. Registre horas manualmente ou use o cronômetro, acompanhe totais diários, semanais e mensais e exporte CSV.

Rascunhos recuperáveis e avisos de sobreposição ajudam a revisar os registros. Ao concluir uma tarefa, você pode lançar as horas na timesheet escolhida. Projetos encerrados podem ser arquivados para consulta posterior.

### Prepare faturas para seus clientes

Escolha uma timesheet e o período — mês, histórico completo ou intervalo no calendário. Informe emitente, destinatário, valor por hora e moeda, revise a prévia e salve o PDF em **português ou inglês**.

O Orbitz calcula o total a partir dos minutos concluídos, com arredondamento no valor final. Cronômetros em andamento e registros na lixeira ficam fora da cobrança. Seus dados de emissão são lembrados após salvar; cliente, taxa e moeda ficam separados por timesheet.

O histórico guarda cópias das faturas e organiza as emissões por timesheet, cliente e mês de emissão. Avisos ajudam a reconhecer horas possivelmente faturadas antes. Você também pode registrar pagamentos manualmente, sem alterar o PDF; esse registro não representa confirmação bancária.

As faturas são **documentos de serviços**. O Orbitz não emite NFS-e, não calcula impostos e não oferece integração fiscal oficial.

### Continue a assinatura pelo gov.br

Salve uma cópia da fatura, abra o assinador gov.br e conclua a assinatura pelo navegador. Depois, importe o documento como uma versão vinculada à invoice, preservando o original e as versões anteriores.

A assinatura e o acesso ao portal VALIDAR são manuais. Versões importadas ficam com **validação pendente**: o Orbitz não verifica criptograficamente a assinatura nem a correspondência do arquivo, e abrir o portal não altera esse status. Senhas gov.br e envio automático de documentos não fazem parte desse fluxo.

## Espaço para ideias e pausas

Anote ideias com **Sticky Notes**, que salvam localmente e têm backups próprios. Controle players compatíveis pelo painel de mídia e abra vídeos em uma janela dedicada do YouTube. Pesquisa e comentários no player exigem uma chave própria da YouTube Data API.

Lançadores para ferramentas como btop e Gemini completam o ambiente, conforme os aplicativos disponíveis no computador.

## Seus dados ficam com você

Tarefas, horas, perfis de faturamento e histórico de invoices são armazenados localmente. Serviços externos são usados nos recursos que você escolhe conectar; as credenciais dos calendários ficam no cofre do sistema.

O **backup completo do Workspace** reúne tarefas, horas, contextos, perfis, invoices, versões, pagamentos manuais e preferências da interface. A restauração apresenta uma prévia, pede confirmação e cria uma cópia do estado anterior. Antes de restaurar, encerre os cronômetros e feche outros editores; depois, reabra o Workspace.

O arquivo contém dados privados e **não é criptografado por senha**: guarde-o em local seguro. Credenciais, calendários externos, Sticky Notes e configurações dos widgets ficam fora desse backup. As notas têm backup próprio.

Excluir uma invoice do histórico remove seu registro e as versões gerenciadas, preservando os PDFs exportados e as horas trabalhadas.

## Comece por aqui

O ambiente de referência é **Ubuntu 22.04 com GNOME 42.9**. A extensão declara compatibilidade com **GNOME 42, 43 e 44**; versões posteriores não têm suporte declarado.

- **Já usa o Orbitz?** Siga o [guia de atualização local](docs/operations/local-update.md). Baixar as fontes não atualiza os aplicativos instalados.
- **Usa uma instalação antiga do Desktop Clock/azclock personalizada como Orbitz?** Consulte o [guia de migração](docs/operations/identity-migration.md) para preservar configurações e dados. Mantenha somente uma identidade ativa.
- **Vai instalar pela primeira vez?** Confira a [plataforma e as dependências](stack.md). As ferramentas atuais atendem instalações existentes; ainda não há um instalador completo validado para máquina nova.

Os requisitos principais são Python 3, PyGObject, GTK, bibliotecas do GNOME e **Tilix**. Ações que pedem confirmação ou autorização em terminal — como manutenção, leitura de módulos de RAM e inspeção de processos — abrem no Tilix. Faturas usam `python3-reportlab` e `fonts-dejavu-core`; o player do YouTube precisa de WebKitGTK. Docker, sensores, firewall e consultas de pacotes dependem das ferramentas e permissões disponíveis no computador.

Com a extensão instalada, abra as preferências:

```bash
gnome-extensions prefs orbitz-widgets@orbitzone.github.io
```

Após atualizar o Workspace, feche e reabra o aplicativo. Para atualizar a coleta dos resumos, pare e abra os widgets pelo controlador.

### Antes de adotar

O Orbitz está em evolução. A instalação em máquina limpa e a experiência em todas as versões declaradas ainda precisam de validação. A conexão inicial com Google Calendar foi confirmada em uso; a validação abrangente de contas e fluxos continua em andamento. Calendly ainda aguarda validação com conta real. A abertura do painel de RAM e o comportamento de dispositivos externos têm pendências conhecidas.

Informações de sensores variam conforme o hardware e as permissões. A análise do firewall auxilia a consulta dos registros, sem determinar por si só a ocorrência de um ataque. Comandos personalizados usam as permissões do usuário; ações de manutenção são iniciadas manualmente.

## Faça parte

Desenvolvido e mantido por **Felipe Santiago / orbitzone**.

Tem uma ideia ou encontrou um problema? [Abra uma issue](https://github.com/orbitzone/orbitz-widgets-for-gnome/issues) com a versão do GNOME, os passos e o resultado esperado. Remova dados pessoais, tokens e senhas de capturas ou logs antes de compartilhar.

O Orbitz tem origem no Desktop Clock/azclock, de Andrew Zaech, e preserva as atribuições de código, recursos e dependências. Conheça os [créditos e licenças](docs/credits.md) e o [LICENSE](LICENSE).
