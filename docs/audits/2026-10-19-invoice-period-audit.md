# INV-02 — auditoria dirigida do período de fatura — 19/10/2026

Estado: **funcional local e revisão estrutural aprovadas, sem impeditivo reproduzido; GTK real pendente**. Alvo frontend declarado estável por coordenação, sobre checkout compartilhado; nenhuma alteração de produção pelo auditor, instalação, dados reais ou acesso à sessão.

## Escopo e execução

Lidos invoice_period_ui.py, integração invoice_ui.py, testes e relatório `2026-10-19-invoice-period-frontend.md`. Mudança exclusivamente no seletor/ponte UI de período; não altera cálculos, perfis, PDF, MonthCalendar da agenda ou timesheets. Ajuste semântico solicitado pelo UX está incluído no alvo auditado; nenhuma comunicação direta UX foi feita pelo auditor.

```bash
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p 'test_invoice_*.py' -v
git diff --check -- extension/planner/invoice_ui.py extension/planner/invoice_period_ui.py tests/test_invoice_period.py
```

**27/27 testes aprovados**,1,084s:10período+17regressões INV-01 (11backend/6frontend). AST dos3arquivos aprovadas e diff-check sem erros. Não houve suíte global. PDFs das regressões foram somente temporários, conforme workflow PDF já estabelecido; nenhum render visual foi duplicado, dependência alterada ou documento real emitido. DeprecationWarning load_module permanece da dependência ReportLab e não causou falha.

## Revisão dos requisitos

- Três modos: all por padrão preserva contrato start/end=None; month calcula mês civil completo; range exige dois cliques ordenados. Removidos dois campos digitados de intervalo; data de emissão segue campo independente, não é data do serviço.
- Mês usa date/calendar.monthrange; testes confirmam28/29/30/31dias e séculos1900/2000/2100. Navegação mês/ano suporta1–9999 e ignora ultrapassagem. Nenhuma aproximação por30dias.
- Específico preserva primeira data ao navegar, ordena cliques invertidos, aceita mesmo dia e inclui ambos extremos. Terceiro clique/limpar recomeça; bounds incompleto levanta ValueError e ready=False. Contrato para backend ISO permanece inalterado; teste através da virada do ano inclui31dez/1jan e exclui dias adjacentes, total120min.
- Assinatura semântica all depende só do modo; month de ano/mês; range dos extremos. Navegar viewport/foco sem editar range não invalida prévia nem escolhe implicitamente dia. Setas dentro do mesmo mês civil não notificam; cruzar mês no modo mês notifica porque altera limites. PageUp/Down de range conserva seleção. Handlers reais testados com foco/atores sintéticos, sem alegar teclado nativo real.
- UI invalidate limpa snapshot, desabilita Salvar e ajusta APPLY à prontidão; mudança semântica chama invalidate. values chama bounds antes de session.prepare, portanto resposta APPLY programática de range incompleto também falha sem gerar prévia/PDF. Troca de sheet/campos/idioma continua invalidando revisão como antes.
- Quarenta e dois botões estáveis, dias fora do mês desabilitados, resumo explica primeiro/segundo clique e ordenação. Nomes acessíveis/tooltips incluem data/seleção/início/fim; classes visuais diferenciam faixa/extremos. Esses mecanismos foram lidos, mas não certificam anúncio AT ou contraste/foco/pixels em tema real.

## Achados e limites

Nenhum defeito impeditivo reproduzido. A correção do descarte de prévia por navegação é sustentada pelas comparações semânticas e dois testes de handlers, sem relaxar validação do período. Navegação em month altera seleção deliberadamente; navegar em range não altera seus extremos. Todos os testes anteriores de domínio/perfil/exportação continuam aprovados, inclusive cancel/invalidação/privacidade/overwrite.

**Funcional local:** aprovado no escopo27testes/ponte ISO. **Visual/interação:** pendente; não executados GTK/GDK/chooser/foco real, calendário renderizado, captura ou nova tentativa Broadway. **Segurança/integridade:** nenhuma regressão impeditiva encontrada nesta alteração sem persistência própria; sem dados reais ou instalação. **Desempenho:** não medido. Parecer não resolve RAM/EXT ou outras pendências do produto.

Supervisor recebe resultado para integrar requisitos/limites e eventual aplicação autorizada. Após atualização, a agenda precisa ser encerrada/reaberta para carregar módulos novos; não há necessidade demonstrada de logout GNOME por este seletor Python. Teste manual deve conferir modos/destaque/teclado/prévia no ambiente permitido, sem inferir aprovação gráfica dos testes puros.

## Hashes do alvo

| Arquivo | SHA-256 |
|---|---|
| `extension/planner/invoice_ui.py` | `442eb333637480c1cd48544cf9d3a89a169025585ce1d4ebbab29ed367552a2b` |
| `extension/planner/invoice_period_ui.py` | `980ce61aa4fdc592c0e86db47037bb78ffa8e227e2eec5705f28c8856c0bfbf9` |
| `tests/test_invoice_period.py` | `122204f448bb85c959655977e1f6e67aea927054c528fee2b2e2ff72088bbd3e` |
