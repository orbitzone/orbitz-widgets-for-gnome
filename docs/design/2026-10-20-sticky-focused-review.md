# STICKY-01 — revisão focada

Captura fornecida e `sticky-notes/card.py` inspecionados em 20/10/2026. A imagem mostra linhas inferior/direita no editor e scrollbar cinza; não comprova qual tentativa local estava instalada. Código atual já usa shadow NONE, scrollbar com opacidade zero e overlay desativado. Sem edição de código, GUI ou instalação.

1. **Neutralizar só a decoração do editor.** Conferir nós CSS `undershoot`/`overshoot` do ScrolledWindow nomeado, além de viewport/textview: podem desenhar linhas mesmo sem border do widget principal. Aplicar seletores restritos ao cartão, sem retirar contorno/foco dos botões. A origem exata das linhas não foi reproduzida.
2. **Invisibilidade sem remoção.** Manter scrollbar criada, overlay desativado e opacidade zero, inclusive hover/arraste. Não usar hide, largura zero ou política NEVER vertical. AUTOMATIC reserva espaço quando necessária; se a reserva precisar existir também com texto curto, confirmar esse detalhe antes de adotar ALWAYS.
3. **Conter o conteúdo.** Manter scroll expansível dentro do cartão, sem propagação da altura natural; comparar altura antes/depois de texto longo. Aceite: roda/teclado alcançam primeira/última linha, scrollbar invisível, espaço lateral preservado e cartão não cresce; testar foco/sem foco e hover. Caret permanece visível.

São recomendações delimitadas; pixels, causa das linhas e comportamento GTK continuam sem validação própria. Frontend implementa/verifica e reporta pelo fluxo vigente, sem nova rodada UX automática.
