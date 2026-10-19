# INV-02 — período de invoice em um calendário — 19/10/2026

Estado: **implementado com testes específicos aprovados; revisão UX estática realizada e ajuste solicitado aplicado; auditoria/GTK pendentes**. Área exclusiva: invoice_ui.py, novo invoice_period_ui.py e teste test_invoice_period.py. Sem alteração de instalação, histórico, perfis ou domínio/PDF backend.

## Mudança

Substituídos o checkbox de histórico e os dois campos ISO de intervalo por três opções: Período de 1 mês, Todo o histórico (default compatível), Período específico. A data de emissão do documento continua independente; não faz parte do intervalo de serviços.

- Todo o histórico: calendário oculto, contrato start/end=None preservado.
- Mês: calendário inicia no mês de window.day (data ISO da agenda) ou hoje; navegação mês/ano escolhe mês **civil**, primeiro ao último dia, incluindo fevereiro/bissextos. Dias desse mês destacados e resumo explícito.
- Específico: primeiro clique guarda primeira data; segundo clique completa intervalo inclusivo. Cliques invertidos são ordenados, conforme instrução visível. Terceiro clique recomeça seleção; botão Limpar/recomeçar também limpa. Resumo informa extremo faltante e início/fim finais. Navegar meses/anos não escolhe dias nem muda extremos já selecionados.

O calendário é específico da invoice. MonthCalendar da agenda permanece intocado, pois sua navegação emite seleção de dia. O novo componente mantém 42 botões nativos estáveis e atualiza conteúdo/classes em vez de destruir/recriar; setas movem foco, PageUp/Down navegam mês, Enter/Espaço selecionam via Gtk.Button. Dias fora do mês ficam desabilitados. Nomes acessíveis e tooltips incluem data, seleção e início/fim, sem depender só de cor. CSS usa cores selecionadas do tema, com destaque adicional de extremos.

`PeriodSelection` é controlador puro date/calendar, independente de GTK. `InvoicePeriodPicker` importa GTK apenas ao construir a interface. Faixa suportada é anos1–9999, com navegação fora dos limites ignorada/desabilitada.

Invoice UI converte somente o resultado validado para ISO ao chamar a API backend. Mudança semântica do período invalida prévia/PDF; navegação/foco sem alteração de seleção preservam a revisão; revisão fica desabilitada enquanto o intervalo específico estiver incompleto. O controlador também recusa bounds incompletos, impedindo bypass da validação via resposta programática. Sessão, valores monetários, perfis, PDF e callbacks do menu permanecem como INV-01.

## Evidências

`python3 -m unittest discover -s tests -p test_invoice_period.py -v`: **10/10 aprovados**:

1. Default histórico e mês da data da agenda.
2. Meses28/29/30/31 e anos1900/2000/2100.
3. Dois cliques obrigatórios e intervalo de um só dia.
4. Cliques invertidos, mudança de ano, limites inclusivos, terceiro clique recomeça.
5. Navegação não muda extremos de range; modo mês acompanha mês civil.
6. Limpar, trocar modo, limites dos anos e modo inválido.
7. Eventos do picker notificam edição/navegação sem selecionar implicitamente.
8. Intervalo escolhido alimenta InvoiceSession/backend e inclui exatamente os dois dias selecionados através da virada do ano, excluindo os adjacentes.
9. Assinatura semântica preserva revisão ao navegar range ou clicar no mesmo mês já selecionado; mudança de mês civil notifica.
10. Setas de foco dentro do mês não notificam; cruzar mês no modo mês notifica; PageDown/setas através de mês no modo range não alteram bounds/revisão.

`python3 -m unittest discover -s tests -p test_invoice_frontend.py -v`: **6/6 aprovados**, incluindo sessão→PDF real PT/EN/perfis privados temporários. Essa regressão foi executada uma vez após integrar o componente ao formulário; nenhum PDF visual foi reavaliado pelo frontend.

Sintaxe AST dos dois módulos frontend aprovada; diff-check de invoice_ui.py sem erros. Nenhuma nova dependência, GSettings ou escrita em perfil real. DeprecationWarning existente de load_module na dependência ReportLab apareceu no teste de PDF, sem falha; dependência não editada.

## UX e limites

Brief/implementação enviados ao UX pelo canal exclusivo. Revisão solicitada sobre três modos, clareza do mês civil, duas escolhas e ordem inversa, indicação de incompleto, destaque visível, teclado/foco e rolagem do formulário. Parecer final será encaminhado ao supervisor/auditor.

Sem execução gráfica GTK, captura ou nova tentativa de ambiente Broadway bloqueado. Testes puros comprovam datas/contrato, não pixels, tema, foco real, AT ou modalidade. Sem alteração do calendário da agenda, emissão PDF/backend, dados históricos, instalação, sessão ativa, commit/push. RAM/EXT e outras tarefas permanecem separadas.

Próximos responsáveis: UX parecer restrito; frontend encaminha estado estável diretamente ao auditor; supervisor atualiza requisitos/docs e coordena auditoria/ativação autorizada.

## Ajuste INV02-UX-A e estabilidade

Revisão em `docs/design/2026-10-19-invoice-period-review.md` identificou descarte de prévia ao navegar/focar sem editar seleção. Corrigido com `selection_key`: all depende só do modo; month depende de modo/ano/mês; range depende de modo/extremos (incluindo incompleto). Picker atualiza viewport/foco normalmente, porém chama invalidação só se essa assinatura mudar. A navegação de mês civil altera a seleção e invalida; navegar um range pronto/incompleto preserva extremos e revisão. Choose/clear/troca de modo notificam quando mudam seleção. Dois testes adicionais, incluindo handlers reais de teclado com foco sintético, passaram; total10/10 período. Supervisor autorizou encaminhar diretamente à auditoria sem aguardar outra rodada UX. Nenhuma correção gráfica especulativa ou dependência foi adicionada. Estado estável para auditoria dirigida, preservando limites GTK.
