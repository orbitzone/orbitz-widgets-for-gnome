# INV-01 — inspeção visual dos PDFs pelo supervisor

18/10/2026. Duas amostras exclusivamente sintéticas geradas pela API real `invoice.build_snapshot` → `invoice_pdf.write`, em PT e EN, no diretório ignorado `work/invoice-qa`. Nenhum dado pessoal ou arquivo da instalação foi usado. Skill PDF aplicada; marcador da operação registrado antes de gerar as amostras.

Caso: 14 atividades de 30 minutos, descrição longa com acentos, travessão, `<segura>` e `&`, endereço multilinha, nomes acentuados. Total esperado: 420 minutos = 07:00; taxa BRL 125,50; total BRL 878,50 (EN 878.50). Os snapshots retornaram esses valores.

Renderização por `/usr/bin/pdftoppm -scale-to 950 -png`; a distribuição empacotada do Poppler requer GLIBC_2.38 ausente e não foi usada após a falha inicial. Foram inspecionadas visualmente todas as quatro páginas (duas por idioma): título/partes/endereço legíveis, texto literal e acentos preservados, tabela dentro da página, colunas de horas/valores legíveis, cabeçalho repetido na página seguinte e rodapé separado do conteúdo. Nenhuma sobreposição, corte ou página vazia observados nessas amostras.

A tradução cobre os rótulos do documento; nomes e descrições digitados pelo usuário são preservados, sem tradução automática. Datas ISO e horas HH:MM são apresentadas consistentemente. Fonte DejaVu incorporada; extração de texto, limites/extremos e falhas de escrita são cobertos pelos testes do backend, com evidência independente na auditoria.

Este resultado aprova a aparência das amostras inspecionadas. Não comprova a janela GTK real, acessibilidade, impressão em todos os dispositivos ou todos os possíveis conteúdos. A validação interativa continua a cargo do teste após aplicação local, sem exigir logout GNOME.
