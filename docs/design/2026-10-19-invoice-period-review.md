# INV-02 — revisão estática do período

Data: 19/10/2026. Destinatário: frontend. Fontes: `extension/planner/invoice_period_ui.py` e integração em `invoice_ui.py`. Sem execução GTK, dados pessoais, instalação ou captura. Resultados de 7 testes de período e 6 frontend são informados pelo frontend, não repetidos por UX.

## Correspondência observada

- Três modos declarados, Todo histórico inicialmente ativo, calendário oculto nesse modo. Modelo recebe data da agenda ou hoje quando inválida/ausente.
- Mês civil usa primeiro dia/monthrange, incluindo ano bissexto; mês escolhido é o mês exibido. Intervalo exige dois cliques, ordena extremos e admite mesmo dia; terceiro clique reinicia. Limpar remove extremos e bloqueia readiness no modo específico.
- Um calendário com 42 botões estáveis e navegação mês/ano, sem destruir atores. Atualização calcula dias reais e desabilita espaços fora do mês; range visível e extremos recebem classes próprias; nomes acessíveis incluem data/selecionado/início/fim. Resumo textual e instruções explicitam extremos, inversão e reinício.
- Setas movem foco por dia/semana, inclusive cruzando mês; PageUp/PageDown navegam sem escolher data e buscam dia correspondente com clamp. Enter/Espaço dependem do comportamento nativo Gtk.Button. Estados de foco/renderização não foram observados.
- CSS usa cores de seleção do tema, mantém estilo de foco herdado; legibilidade/contraste nos temas e foco real ainda pendentes. Ênfase em negrito nos extremos e texto acessível complementam cor do range.
- Integração invalida snapshot/Salvar PDF e usa ready para habilitar Revisar prévia; bounds envia somente ISO ou None, preservando fronteira backend.

## Achado INV02-UX-A — navegar/focar invalida prévia sem editar o intervalo

Observado no código: `_navigate` sempre chama `self.changed()` e `_key` nas setas também chama esse callback. Em `invoice_ui`, changed é invalidate: apaga snapshot e desabilita Salvar PDF. Em modo range, navegar não muda start/end; mover foco dentro do mesmo mês também não muda bounds em modo month. Logo uma prévia válida é descartada por simples exploração/foco, embora o período selecionado permaneça igual. Não é corrupção do range nem seleção acidental, mas invalidação desnecessária de revisão.

Solicitação ao frontend, prioridade P2: distinguir mudança de valor do período de mudança de viewport/foco. Notificar edição somente quando mudar o estado semântico relevante (modo, extremos/readiness ou bounds de mês). Preservar atualização visual/foco da navegação. No modo month, atravessar mês altera o período e deve invalidar; no modo range, navegar deve preservar extremos e prévia; escolher/limpar/trocar modo deve invalidar. Aplicar sem mudar contrato backend.

Aceite sintético proposto: após prévia válida de range, ±mês/ano, PageUp/Down e setas não mudam bounds/snapshot/export disponível; selecionar novo extremo/limpar/trocar modo invalida e bloqueia enquanto incompleto. Em mês civil, setas no mesmo mês não invalidam, atravessar mês e navegar mês/ano invalidam. Testar mesmo dia, ordem inversa, fevereiro bissexto e limite de ano. Este achado é estático; não houve reprodução em janela.

## Ajustes opcionais e limites

A lista de opções começa com mês, embora all seja o default confirmado; não contradiz o requisito de default e não exige reordenar nesta tarefa. Ajuda de dois cliques fica visível também no modo month, com texto explicitamente condicionado ao período específico; pode ser contextualizada futuramente, sem bloquear o fluxo. Botões estáveis evitam destruição do foco, mas o dia associado a um mesmo ator muda ao navegar: retorno/foco e anúncio do mês precisam de teste nativo quando permitido.

Aceite visual pendente: seleção e extremos reconhecíveis em claro/escuro; calendário cabe no scroll do modal com escala ampliada; Tab/Shift+Tab/Enter/Espaço/setas e navegação por mês/ano com nome/foco visível; resumo alcançável/anunciável e nenhuma exportação disponível com range incompleto. Não solicitar nova tentativa gráfica bloqueada agora.

Parecer: estrutura e critérios principais representados no código, com INV02-UX-A encaminhado para ajuste antes de tratar a invalidação como equivalente ao requisito. Nenhuma alteração de produção por UX; somente este relatório. Frontend corrige/verifica e comunica ao supervisor/auditor; UX pode reler o marco ajustado.

## Complemento — INV02-UX-A tratado estaticamente

Em 19/10/2026, frontend informou estado estável encaminhado ao auditor e 10/10 testes de período mais 6 regressões frontend aprovados, conforme `docs/audits/2026-10-19-invoice-period-frontend.md`. Testes não repetidos por UX.

Releitura própria de `selection_key`, `_notify` e handlers confirma: assinatura all contém somente modo; month contém modo/ano/mês; range contém modo/extremos inclusive None. Os handlers comparam assinatura antes/depois e só notificam mudança quando ela difere. Navegação e foco em range não descartam revisão; foco dentro do mês não altera seleção month, mas atravessar/navegar mês altera e notifica. Escolher extremos, limpar seleção e trocar modo notificam quando alteram estado semântico/readiness. PageUp/Down usa a mesma navegação com guarda.

**Achado INV02-UX-A tratado na evidência estática relida; nenhum impedimento estático remanescente identificado nesse caminho.** Não é aprovação de interação nativa, contraste, pixels ou auditoria independente. Limites gráficos e critérios da seção anterior permanecem. Nenhuma nova execução gráfica ou alteração de produção por UX.
