# INV03 — revisão estática do histórico de invoices

Data: 19/10/2026. Destinatário exclusivo: frontend. Fontes lidas: `extension/planner/invoice_history_ui.py`, menu em `planner_menu.py` e hook/avisos de exportação em `invoice_ui.py`. Sem GUI, dados pessoais, abertura de PDF, geração/renderização nova, instalação ou testes repetidos por UX. Os 6 testes de histórico e 6 frontend aprovados são evidência informada pelo frontend.

## Parecer e cobertura estática

**Fluxo e salvaguardas de interação declarados correspondem ao escopo INV03, sem impedimento estático identificado nesta revisão.** Validação gráfica e auditoria independente continuam distintas.

| Critério | Evidência lida |
|---|---|
| Ponto de entrada | Histórico inserido imediatamente após Gerar invoice no menu superior, preservando arquivadas/backup. |
| Agrupamento e múltiplas invoices | `group_records` usa sheet_id e client_key, não só nomes. Emissão agrupada por ano/mês e meses em ordem inversa; cada registro permanece folha distinta. Folha inclui referência, moeda/total e ID abreviado. Cliente inclui CPF/CNPJ para distinguir nomes iguais no contexto local autorizado. Não houve leitura de identidades reais. |
| Seleção/ações | Cabeçalhos armazenam ID vazio; select retorna None para não-registros e desabilita Consultar/Copiar/Excluir. Ativação de linha abre somente folha. Reload limpa seleção/ações e mantém backend responsável pela leitura dos registros válidos. |
| Detalhes | Referência, timesheet, cliente/identificador, emissão explicitamente diferenciada do período de serviços, horas, total/moeda, idioma e data de arquivamento. Resumo selecionável com quebra e rolagem. |
| Consultar/cópia | URI construída por Gio.File, abertura com AppInfo e sem comando shell nos trechos lidos. FileChooser exige PDF e confirmação nativa de sobrescrita; cancelamento não chama export. Erro de cópia orienta conferir destino, sem prometer rollback não demonstrado. Isso não substitui auditoria do backend/arquivo. |
| Exclusão | Confirma referência, cliente, emissão, ID abreviado e created_at; Cancelar é default. Mensagem delimita registro/cópia do histórico e preservação de PDF externo/horas. Cancelar não chama delete; confirmado exclui por identidade selecionada e recarrega lista. |
| Vazio/erro/parcial | Ausência de registros, falha geral e contagem de registros ilegíveis têm textos próprios. Registros bons são mantidos no modelo; UI não tenta reparar/remover corrompidos na leitura. Abrir/cópia falhos preservam seleção e mostram feedback; comportamento real dos arquivos é responsabilidade backend. |
| Arquivamento pós-exportação | `invoice_pdf.write` precede history.record; falha ao arquivar gera aviso explícito de PDF salvo sem cópia histórica. Salvar perfil é tentativa independente com aviso próprio. Não há importação automática antiga e isso é explicado na janela. |
| Layout/acessibilidade | Modal limitado à workarea, mínimo solicitado 420 × 300; árvore com nome acessível, renderer WORD_CHAR ajustado à largura; lista/detalhes com scroll; ações em FlowBox adaptável, botões com nomes explícitos. Não comprova mínimo efetivo nem leitura por AT. |

## Observações pontuais para frontend

1. Quando todos os registros são ilegíveis, a mensagem concatena “Nenhuma invoice guardada” com “Registros válidos continuam disponíveis”, embora não haja registros válidos nesse resultado. Não compromete a preservação dos arquivos, mas pode sugerir disponibilidade inexistente. Sugestão textual local: sem válidos e com errors, usar “Nenhum registro pôde ser exibido; N registros não puderam ser lidos; arquivos preservados”; com válidos, manter a disponibilidade dos bons. Não confundir histórico vazio com histórico totalmente ilegível.
2. Árvore e detalhes exibem `snapshot['total']` literal, enquanto a prévia PT usa formatação decimal localizada. Valor/moeda ficam inequívocos, mas formato com ponto difere da UI PT. Sugestão opcional: reutilizar format_money(..., 'pt') no histórico PT, sem mudar snapshot/PDF ou arredondamento. Não é exigência de redesign.
3. Empresas homônimas continuam em nós separados por sheet_id, porém com mesmo rótulo visual. Referência/ID de folha e contexto de cliente ajudam na escolha; verificar fixture com duas sheets de mesmo nome antes de afirmar distinção totalmente clara. Não expor IDs completos ou novos dados privados só por hipótese; se houver ambiguidade real, frontend pode adicionar discriminador mínimo dentro do escopo.

Observações 1–3 não foram reproduzidas em janela. A primeira decorre diretamente da montagem de texto; as demais são consistência/clareza para triagem. Nenhuma implica exclusão errada demonstrada ou falha de segurança confirmada.

## Aceite interativo pendente

- Expandir/recolher árvore e selecionar folha com teclado; ações desabilitadas em todos os níveis intermediários, foco visível e referência suficiente no anúncio acessível.
- Testar nomes longos, duas empresas/clientes homônimos, várias invoices da mesma emissão, emissão diferente de mês de serviços, janela mínima/escala ampliada e múltiplas páginas de lista. Nenhuma ação fica cortada e detalhes permanecem alcançáveis.
- Selecionar folha, abrir/cancelar salvar cópia e excluir; cancelar mantém seleção/arquivos, confirmar exclusão remove só registro alvo, foco retorna a alvo previsível após reload. Erro/sucesso perceptíveis; grab_focus no feedback não é prova de anúncio AT.
- Exercitar vazio, todos ilegíveis, misto válido/ilegível, PDF ausente e falha de aplicativo padrão com fixtures privadas sintéticas; feedback não promete recuperação automática ou disponibilidade inexistente.
- Exportação salva com falha de arquivamento/perfil informa sucesso do PDF e cada falha separadamente, sem afirmar histórico salvo. Não repetir QA de renderização PDF nesta tarefa UX.

Sem nova tentativa gráfica bloqueada solicitada. Somente este relatório em `docs/design/` criado por UX. Próximo responsável: frontend considera os ajustes textuais, encaminha parecer/limites ao supervisor e handoff técnico ao auditor conforme coordenação autorizada; validação GTK fica pendente até ambiente permitido.
