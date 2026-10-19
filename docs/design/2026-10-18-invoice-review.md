# INV-01 — revisão estática de menu, formulário e rótulos PDF

Data: 18/10/2026. Destinatário exclusivo: frontend. Escopo: menu superior na linha da data, invoice local PT/EN com revisão antes de exportar, sem redesign do restante da agenda. Fontes lidas: `extension/planner/planner_menu.py`, `invoice_ui.py`, trechos de `calendar-app.py`, `invoice.py` e `invoice_pdf.py`. Checkout compartilhado em desenvolvimento; achados referem-se aos trechos lidos nesta execução.

Método: inspeção estática. Não houve execução GTK, dados reais, exportação, captura ou tentativa gráfica. Nenhum PDF foi aberto/renderizado por UX; QA dos artefatos PDF fica com supervisor conforme coordenação recebida. Não é parecer de segurança independente nem de validade fiscal.

## Correspondência com o escopo

- Menu nativo Gtk.MenuButton à direita de heading expansível; nome acessível/tooltip “Mais ações da agenda”. Três ações presentes; arquivadas/backup chamam responsáveis existentes. Contagem das arquivadas atualiza texto/nome acessível do item. Status permanece no footer.
- Modal transitório, Cancelar/Revisar prévia/Salvar PDF, exportação inicialmente desabilitada; tamanho inicial limitado pela área de trabalho, mínimo solicitado 360 × 280. Formulário em rolagem vertical, endereço com quebra por palavra/caractere, scroll próprio e Tab liberado para próximo campo. Isso não comprova que o mínimo real dos filhos caiba em 360 px.
- Rótulos dos campos ligados por mnemonic_widget e nomes acessíveis explícitos. Timesheets ativas/arquivadas listadas e aba atual pré-selecionada quando disponível. Datas opcionais inicialmente desabilitadas por histórico completo; idioma do PDF e moeda são controles independentes. Formulário e prévia ficam em PT inclusive quando PDF escolhido em EN.
- Prévia informa período, horas HH:MM, minutos, taxa e total com código de moeda. Aviso explícito de serviço sem emissão de nota fiscal eletrônica, cronômetro em andamento excluído e perfis lembrados após salvar PDF.
- Edição invalida snapshot/prévia e desabilita exportação. Perfil salvo somente após write bem-sucedido; cancelamento não chama save de perfil. FileChooser usa confirmação nativa de substituição, valida extensão e nome padrão sem nome do cliente. Erros de carregamento iniciais evitam expor detalhes de dados; erros posteriores usam mensagens da camada correspondente. Esses são comportamentos declarados, não auditoria de integridade da gravação.

## Achados para frontend

### INV-UX-A — largura mínima e nomes longos (P2, risco a reproduzir)

Labels de caption são criados sem wrap e ComboBoxText usa nomes integrais de timesheets. Com scroll horizontal NEVER, moeda/endereço fiscal e nome longo de empresa podem aumentar a largura mínima efetiva do diálogo. FileChooser e botões também dependem das métricas do tema. A rolagem vertical não resolve largura excedente.

Aceite: em ambiente permitido, formulário com nome sintético longo, janela pequena e escala ampliada mantém controles/ações alcançáveis, rótulos legíveis e sem corte. Frontend pode usar wrap/limites de largura/ellipsize com acesso ao nome completo se confirmar necessidade, dentro deste formulário, sem compactar a agenda inteira. Inspeção estática não comprova falha dimensional atual.

### INV-UX-B — mnemonics repetidos (P2, observado no código)

`_Timesheet` e `_Taxa por hora` compartilham Alt+T; `_emitente` e `_emissão` compartilham Alt+E. GTK pode alternar entre alvos em vez de oferecer atalho único; não foi testado interativamente. Ordem de tabulação e foco inicial explícito em emitente existem, mas não substituem revisar duplicações.

Aceite: mnemonics distintos para os campos expostos, ou comportamento duplicado documentado/testado se deliberado; Tab/Shift+Tab percorrem campos e saem do endereço; Cancelar/Escape fecham sem gravar e retorno de foco vai ao menu/acionador. Sem execução, último critério permanece pendente.

### INV-UX-C — falha ao refazer prévia pode manter botão habilitado (P2, caminho estático)

No caminho APPLY, prepare invalida a sessão antes de validar dados; catch exibe erro, mas não desabilita explicitamente a resposta OK. Após uma prévia válida, se dados externos mudarem sem edição dos campos e uma nova revisão falhar, o estado visual pode continuar oferecendo Salvar PDF, embora export recuse snapshot ausente. A guarda evita exportar sem snapshot; não é evidência de exportação indevida.

Aceite: qualquer falha de prepare deixa Salvar PDF desabilitado e prévia claramente inválida, preservando os valores digitados para correção. Reproduzir por sessão sintética que retorna dados válidos e depois timesheet indisponível/sem registros.

### INV-UX-D — perfil por timesheet e campos compartilhados (P2, alinhamento de contrato)

change_sheet troca cliente, taxa e moeda, mas emitente e idioma são inicializados uma vez e permanecem durante a troca. Profile salvo inclui emitente/idioma por sheet. Esse comportamento pode ser deliberado para emitente compartilhado, mas não está explicado no formulário: ao gerar para outra sheet, o perfil anterior de emitente/idioma daquela sheet não é carregado, e o sucesso poderá substituí-lo pelos valores correntes. Rascunhos por sheet também guardam somente cliente/taxa/moeda.

Aceite a confirmar com contrato frontend/supervisor: se emitente/idioma são globais do diálogo, informar essa regra e garantir revisão consciente; se perfis completos são por sheet, carregar/restaurar os campos correspondentes e rascunhos coerentemente. Não escolher regra de produto silenciosamente nesta revisão. Cancelamento continua sem salvar conforme código lido.

### INV-UX-E — localização de prévia/erros e ações de revisão (P2, risco a reproduzir)

Prévia e aviso ficam no fim do conteúdo rolável, erro fora do scroll. Atualizar preview/error não desloca explicitamente foco nem assegura visibilidade/anúncio. Revisar via botão com foco fora da região pode deixar resultado fora da tela; erro longo fora do scroll pode competir com área útil.

Aceite: revisão e erro ficam perceptíveis sem procurar manualmente no formulário, inclusive com leitor de tela; erro não apaga dados; escolher Cancelar no FileChooser retorna à prévia válida sem persistir perfil; editar qualquer campo exige nova revisão. Solução de foco/anúncio deve evitar roubo de foco em cada tecla digitada. Validação GTK/AT permanece pendente.

## Rótulos PDF PT/EN e QA a alinhar

Leitura de LABELS confirma pares coerentes: Fatura de serviços/Service invoice; Referência/Reference; Data de emissão/Issue date; Emitente/Issuer; Cliente/Client; Endereço fiscal/Billing address; Valor por hora/Hourly rate; Atividades concluídas/Completed activities; Página/Page. CPF/CNPJ fica como identificador brasileiro em ambos, sem tradução enganosa. Datas ISO e horas HH:MM são consistentes entre snapshot e tabela; sugerir QA para que Hours não seja interpretado como horas decimais. Código de moeda acompanha os valores e independe do idioma; format_money usa vírgula PT e ponto EN.

Fonte declara A4, fontes Unicode incorporadas, escape de conteúdo, descrição com quebra de palavras, cabeçalho de tabela repetido e rodapé com página/aviso de documento não fiscal eletrônico. Isso não demonstra ausência de linhas cortadas, órfãs, página vazia ou sobreposição. Rodapé de 7 pt e corpo de 9 pt precisam de inspeção real de legibilidade, especialmente em impressão.

Ao supervisor/QA PDF, via frontend: gerar somente fixtures sintéticas PT/EN com acentos, endereço longo multiline, descrição de 1000 caracteres inclusive token sem espaços, referência longa, muitas atividades/múltiplas páginas, nome longo de timesheet, valores elevados/taxa fracionária e moedas BRL/USD independentes do idioma. Renderizar/inspecionar todas as páginas conforme workflow PDF; conferir glyphs, rodapé, repetição de cabeçalho, totais, período histórico/filtrado, limites de tabela e correspondência com prévia. Cronômetro ativo deve ser excluído com explicação na UI; não inferir que rótulo “concluídas” sozinho comunica exclusão de registro ainda em andamento.

## Resultado e próximos responsáveis

Base do fluxo corresponde ao escopo no código. A–E são achados/questões encaminhados, não validação gráfica nem aprovação integral de INV-01. C tem caminho estático concreto; A/E dependem de execução para impacto; D exige alinhamento de comportamento esperado. Testes sintéticos aprovados informados pelo frontend não foram repetidos por UX e não substituem navegação nativa/QA PDF. Nenhuma nova tentativa gráfica bloqueada solicitada. Somente `docs/design/` alterado por UX. Frontend trata achados próprios e leva contrato/QA ao supervisor; UX revisa novas evidências quando acionado.

## Complemento — releitura restrita dos ajustes A–E

Em 18/10/2026, após resposta frontend, relidos os trechos alterados de `invoice_ui.py` e o contrato efetivo de `invoice_profiles.py`, sem importar/executar aplicativos ou acessar arquivo pessoal de perfis.

| Achado | Resultado da releitura |
|---|---|
| A — largura | Captions agora quebram WORD_CHAR com máximo de 58 caracteres; renderer do seletor usa ellipsize END/máximo 36 e tooltip do nome completo da sheet. Mitigações presentes estaticamente; largura mínima efetiva e popup do seletor continuam sem medição GTK. |
| B — atalhos | Timesheet T, referência R, data D, emitente E, cliente C, endereço F, valor V, moeda M e idioma I não repetem as letras declaradas; datas opcionais sem mnemonic. Duplicações anteriores retiradas. Percurso real Tab/Shift+Tab/Escape e retorno de foco permanecem pendentes. |
| C — falha de revisão | APPLY desabilita OK antes de prepare; catch invalida sessão, mantém OK desabilitado, troca texto da prévia e foca erro selecionável. Caminho estático apontado foi tratado; nenhuma exportação sem revisão habilitada foi identificada nessa releitura. Não equivale a teste do diálogo real. |
| D — perfil | Contrato backend lido confirma emitente/idioma globais no documento, sheets contendo somente cliente/taxa/moeda; load combina ambos e save mantém essa divisão. Aviso da UI explica explicitamente o alcance e persistência só após PDF salvo. Manter globais durante troca é coerente com esse contrato. A formulação inicial de possível perfil completo por sheet era hipótese baseada na interface de save, não no armazenamento, e fica superada por esta verificação. Nenhuma mudança de backend necessária por este parecer. |
| E — percepção | Sucesso foca prévia selecionável e inclui warnings do snapshot; falha APPLY foca erro selecionável. Mitigação identificada no código. Rolagem automática para foco/anúncio por acessibilidade não foram observados. Erros de exportação ainda atualizam o label fora do scroll sem foco explícito; verificação perceptiva desse caminho permanece no aceite gráfico, sem inferir falha reproduzida. |

**Parecer atualizado: ajustes solicitados estão presentes e contrato de perfis esclarecido; sem impedimento estático remanescente identificado nos caminhos revistos.** A conformidade dimensional/de interação nativa e a inspeção dos PDFs continuam pendentes. Não se exige tentativa gráfica bloqueada nem redesign do restante da agenda. O checklist PDF da seção anterior permanece válido para supervisor/QA, via relatório frontend; UX não executou nova geração ou renderização nesta etapa.
