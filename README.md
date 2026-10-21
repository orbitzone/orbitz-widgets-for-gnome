<p align="center">
  <img src="extension/media/orbitz-logo.svg" alt="Orbitz Widgets" width="112">
</p>

<h1 align="center">Orbitz Widgets for GNOME</h1>

<p align="center"><strong>Seu desktop. Seu trabalho. Seu ritmo.</strong></p>

O Orbitz reúne informações do computador e ferramentas de organização em um desktop GNOME que você adapta à sua rotina. Acompanhe o sistema sem perder de vista seus compromissos, tarefas e horas de trabalho.

<p align="center">
  <img src="docs/images/desktop-widgets.png" alt="Widgets Orbitz organizados na área de trabalho GNOME">
</p>

## Um desktop que trabalha com você

Escolha os widgets, organize posições e grupos e ajuste a aparência. Use o controlador na área de trabalho para mostrar ou pausar o conjunto. De um relance, acompanhe relógio, clima e agenda; recursos do computador, como processador, memória, armazenamento e rede; e informações de sistema, como atualizações, serviços e contêineres.

O **Currency Converter** mostra a conversão de BRL para a moeda fiduciária escolhida em duas casas decimais, permite inverter o sentido e atualizar a cotação manualmente pela modal do widget. A consulta automática ocorre a cada quatro horas. A fonte publica referências diárias em dias úteis, não cotações em tempo real; várias consultas podem retornar o mesmo valor.

Notas adesivas, controles de mídia, um player dedicado do YouTube e lançadores deixam suas ferramentas à mão. A busca e os comentários do YouTube precisam de uma chave própria da API. As informações de hardware variam conforme o computador, os sensores e as permissões disponíveis.

## Do compromisso à entrega

O **Orbitz Workspace** conecta planejamento e registro do trabalho em cinco áreas:

- **Hoje e Agenda:** consulte compromissos, tarefas e lembretes em uma visão organizada. Conecte Google Calendar, iCloud, Calendly ou uma assinatura ICS; o calendário público **Brasil · Datas comemorativas** está disponível sem login.
- **Tarefas:** transforme compromissos em tarefas quando fizer sentido, acompanhe prazos e registre o trabalho concluído.
- **Horas:** organize timesheets por empresa ou projeto, use cronômetros ou lance horas manualmente, acompanhe totais e exporte CSV.
- **Invoices:** prepare faturas de serviços em PDF, em português ou inglês, usando os períodos e as horas da timesheet.

Tarefas e horas são mantidas localmente e continuam sob seu controle ao conectar ou desconectar calendários. Os calendários externos fornecem compromissos; não substituem seus registros de trabalho.

## Seus dados, suas escolhas

Tarefas, horas, perfis de faturamento e histórico de invoices ficam no computador. As credenciais dos calendários são guardadas no cofre de senhas do sistema. Conecte apenas os serviços que quiser usar.

O Workspace permite criar um backup de tarefas, horas, perfis e histórico de faturas. O arquivo não é criptografado por senha; guarde-o em um local privado. Credenciais, calendários externos, configurações dos widgets e Sticky Notes não fazem parte desse backup. As notas têm cópias de segurança próprias.

## Transparência no faturamento

As invoices do Orbitz são documentos de serviços. O aplicativo não emite NFS-e, calcula impostos nem confirma pagamentos em bancos; pagamentos são anotações manuais. O fluxo de assinatura gov.br é assistido: você assina no portal e importa a versão. A conferência criptográfica da assinatura e do documento deve ser feita por você no serviço oficial VALIDAR.

## Comece

O Orbitz é uma extensão para Linux com GNOME Shell. A compatibilidade declarada é **GNOME 42–44**; o ambiente de referência é **Ubuntu 22.04 com GNOME 42.9**. Os recursos dependem das bibliotecas e ferramentas disponíveis na distribuição.

- [Veja a plataforma e os pré-requisitos](stack.md).
- [Conecte calendários](docs/operations/calendar-integrations.md).
- [Atualize uma instalação existente](docs/operations/local-update.md).
- [Migre uma instalação antiga do Desktop Clock/azclock](docs/operations/identity-migration.md).

O projeto ainda não oferece um instalador validado para uma máquina nova. A compatibilidade declarada também não substitui a validação em cada versão do GNOME.

## Comunidade e créditos

O Orbitz é desenvolvido por **Felipe Santiago / orbitzone**. Encontrou um problema ou quer sugerir uma melhoria? [Abra uma conversa no GitHub](https://github.com/orbitzone/orbitz-widgets-for-gnome/issues).

O projeto tem origem no Desktop Clock/azclock, de Andrew Zaech, e preserva as atribuições de seus componentes. Consulte os [créditos e licenças](docs/credits.md) e o [LICENSE](LICENSE).
