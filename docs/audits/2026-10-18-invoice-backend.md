# INV-01 — domínio, perfis privados e PDF de fatura

Data: 18/10/2026. Estado: backend estável com validação específica; integração frontend, auditoria independente e QA visual supervisor são etapas distintas. Sem instalação, dados reais, publicação ou commit/push.

## Área e contrato alinhado

Criados exclusivamente `extension/planner/invoice.py`, `invoice_profiles.py`, `invoice_pdf.py` e `tests/test_invoice_backend.py`. Não foram editados UI/calendar-app, timesheet/store, ferramentas operacionais ou dependências. Frontend aceitou as APIs abaixo e já implementou sessão de prévia/chooser; salva perfil apenas depois de PDF bem-sucedido, com erro de perfil separado do resultado do PDF.

- `invoice.prepare(data, sheet_id, *, issuer, client, rate, currency='BRL', language='pt', reference, issued_on, start=None, end=None)` retorna snapshot revisável. `build_snapshot(sheet, **mesmos_argumentos)` recebe diretamente uma timesheet. `validate_snapshot(snapshot)` recalcula/valida antes de exportar; `format_money(value, language='pt')` formata duas casas sem símbolo/moeda.
- `issuer={'name','tax_id'}`; `client={'name','tax_id','address'}`. Referência editável e data ISO explícitas. Identidade de timesheet é usada somente para seleção/persistência, sem consulta fiscal.
- Snapshot JSON-safe: `version=1`, `sheet_id`, `sheet_name`, `reference`, `issued_on`, `issuer`, `client`, `currency`, `language`, `rate` e `total` como strings decimais canônicas, `minutes` inteiro, `hours` no formato `HH:MM`, `period={'start','end','all_history'}`, `entries=[{'description','date','start','end','minutes'}]`, `warnings` com aviso PT quando cronômetro ativo foi ignorado.
- `invoice_profiles.load(sheet_id, path=None)` retorna `issuer/client/rate/currency/language`, com campos vazios/BRL/PT se ainda não salvos; nenhuma escrita. `save(sheet_id, profile, path=None)` valida e persiste perfil completo. `path` opcional serve aos testes; padrão fora do repo.
- `invoice_pdf.write(snapshot, path, *, overwrite=False)` retorna `Path`; `render_pdf` é alias da mesma função. `FileExistsError` exige confirmação explícita da UI antes de passar `overwrite=True`; demais erros de domínio são `ValueError` em PT sem reproduzir identificadores pessoais nas mensagens.

## Cálculo e seleção

Aceita timesheet ativa ou arquivada. Default é todo o histórico concluído, inclusive datas distintas do mês exibido. Período opcional exige início e fim ISO inclusivos e ordenados. Usa somente `sheet['timesheet']`; lixeira e cronômetro ativo ficam fora. Snapshot não muta dados de entrada nem acessa arquivos de notas, tarefas ou calendários. Sem registros concluídos, recusa a geração.

Valida entradas pelas regras atuais de timesheet, soma minutos inteiros e calcula `Decimal(minutes) * Decimal(rate) / Decimal(60)` em contexto de precisão 50. Apenas o total final recebe `quantize(.01, ROUND_HALF_UP)`; nenhuma soma de valores arredondados por atividade. Taxa é texto positivo/finito com até 12 posições inteiras e duas casas decimais, vírgula ou ponto. Recusa floats, notação exponencial, agrupamentos/múltiplos separadores e três casas (`1,234` não vira milhares nem taxa ambígua). Taxa canônica tem duas casas; `0.1` é aceita como `0.10`.

Moeda de três letras, BRL default, persistida por sheet e independente do idioma. Idiomas PT/EN. Não há conversão cambial nem inferência de impostos, número fiscal ou integração oficial.

CPF aceita 11 dígitos, cru ou pontuação completa. CNPJ aceita primeiras 12 posições alfanuméricas A-Z/0-9 e duas finais numéricas, cru ou pontuação completa; letras normalizadas em maiúsculas. Formato/comprimento não comprovam autenticidade cadastral nem verificam dígitos de controle. Suporte alfanumérico foi confirmado pelo supervisor a partir da [Receita Federal](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cnpj-alfanumerico); nenhum serviço foi consultado com identificadores.

## Persistência privada

Padrão `~/.local/share/orbitz-widgets/invoice-profiles.json` (respeita XDG_DATA_HOME), arquivo `0600` via `atomic_json`; lock separado `0600`, `flock` e leitura dentro da seção exclusiva. Formato versionado: emitente global, idioma global lembrado, cliente/taxa/moeda por identidade da timesheet. Trocar perfil de uma empresa não reatribui cliente de outra; atualizar emitente global vale para as demais. Não inclui dados bancários ou pagamentos.

Leitura limitada a 2 MiB, arquivo regular sem seguir symlink, validação de estrutura/tipos/perfis. Arquivo danificado falha explicitamente e não é substituído por defaults. Falha de gravação atômica preserva o original. Nenhum load/cancel escreve; concorrência de seis processos foi verificada. Nenhuma cópia desses dados ao repo, logs ou PDF fora do local escolhido pelo usuário.

## PDF e segurança de saída

Dependências nativas: ReportLab **3.6.8**, disponível em `/usr/lib/python3/dist-packages/reportlab`, e fontes `fonts-dejavu-core` em `/usr/share/fonts/truetype/dejavu`. Imports de ReportLab são tardios na geração. DejaVu Sans normal/bold embutidas com mapeamento de família preservam acentos de João/Ação/Clínica e extração Unicode. Caracteres ausentes na fonte são recusados com orientação em vez de quadrados silenciosos; suporte a todas as escritas mundiais não é alegado.

Título Fatura de serviços/Service invoice, referência/data, período efetivo ou explícito, emitente/cliente/CPF-CNPJ/endereço fiscal, timesheet, horas, taxa/moeda, total e atividades. Rodapé afirma que não é documento fiscal eletrônico, com número da página. Strings são escapadas antes de Paragraph XML; tags e `&` de usuário aparecem literalmente. Tabela LongTable repete cabeçalhos. ReportLab 3.6.8 não oferece `splitInRow`; descrições são divididas por `Paragraph.split` em fragmentos completos de até 280 pt, como linhas de continuação, sem cortar texto. Partes/endereço são Paragraphs independentes que podem quebrar de página.

PDF é produzido em temporário no diretório escolhido, modo `0600`, flush/fsync e publicação atômica. Sem confirmação, `os.link` publica sem clobber mesmo se destino aparecer durante render. Com confirmação, exige arquivo regular sem symlink e revalida inode/tamanho/mtime antes de substituir; falha de geração preserva o anterior. Exige sufixo `.pdf`. Temporários limpos em `finally`; fsync do diretório. Não é transação global contra ações externas simultâneas após última checagem e não se promete rollback após falha de fsync posterior à publicação.

## Verificação específica

`/usr/bin/python3 -m unittest discover -s tests -p test_invoice_backend.py -v`: **11/11 aprovados**.

Cobertura:

- Taxa 0.1, um minuto, total de três minutos a 0.10 arredondado uma vez, fronteira HALF_UP e vírgula/ponto.
- Fevereiro bissexto, datas inclusivas, histórico completo, sheet arquivada, timer/lixeira excluídos e dados de entrada inalterados.
- Campos obrigatórios, CPF/CNPJ numérico/alfanumérico, pontuação/tamanho, moeda independente de idioma e taxa ambígua/negativa/não finita recusadas.
- Snapshot adulterado e controle XML inválido recusados.
- Clientes por empresa, emitente/idioma global, arquivo privado, cancel/load sem arquivo e arquivo de notas sentinela inalterado.
- Arquivo de perfil danificado, falha atômica sem perda, seis processos salvando sheets diferentes sem perder perfis.
- PDFs PT/EN com textos longos em várias páginas, extração `pdftotext` preservando acentos/tags literais/última descrição e total; `pdffonts` confirma DejaVu Sans embutida com Unicode.
- Overwrite recusado sem confirmação, erro de render mantendo original, symlink recusado e destino surgindo durante geração preservado.

A execução em ReportLab emite DeprecationWarning de `load_module` da própria dependência Python, sem falha funcional; vendor não alterado. Não foi rodada suíte global enquanto frontend estava mudando.

Skill PDF lida e marker executado antes de gerar testes/amostras. Backend gerou duas amostras sintéticas em `/tmp/orbitz-invoice-qa` e renderizou via **`/usr/bin/pdftoppm`**; o Poppler empacotado falhou por exigir GLIBC_2.38. A inspeção visual final está centralizada no supervisor, que já gerou/renderizou as amostras em `work/invoice-qa` e pediu não duplicar QA. Extração/fontes/paginação testadas não equivalem a aprovação visual. Nenhuma amostra contém dados reais.

## Estado e próximos responsáveis

Frontend pode executar sessão→PDF/perfil temporário sobre API estável. Supervisor conclui QA visual das amostras e atualiza README/stack/requisitos/backlog/decisões; auditor realiza verificação independente do domínio, integridade e integração estável. Não foram tocadas instalação ativa, GSettings real, notas/tarefas/horas, credenciais, calendários, UI ou ferramentas. Sem alegação de emissão fiscal oficial ou validação cadastral. Validação gráfica da agenda, instalação e publicação continuam fora desta entrega.
