# INV-03 — histórico privado de invoices

Data: 19/10/2026. Estado: backend estável com testes específicos; integração frontend, verificação independente e interface gráfica ainda separadas.

## Entrega e API alinhada

Criados `extension/planner/invoice_history.py` e `tests/test_invoice_history.py`. Não alterados cálculo, renderer INV-02, perfis, UI, menu, ferramentas ou dados reais. Frontend alinhou chamadas e warnings: depois de PDF externo bem-sucedido, arquivar independentemente de salvar perfil; falha no arquivo histórico é aviso de sucesso parcial, sem afirmar que o PDF externo falhou.

APIs (todas com `root=None` keyword opcional para fixtures):

- `record(snapshot, pdf_path) -> metadata`: cópia exata dos bytes lidos do PDF exportado e snapshot canônico validado, em registro novo independente. Não sobrescreve registros/referências repetidas.
- `list_records() -> {'records': [...], 'errors': [{'id','message'}]}`: ordena por data de emissão/criação/id decrescentes; corrupção de um registro não apaga/esconde os demais válidos. Mensagens genéricas, sem conteúdo pessoal/caminho externo.
- `get(id) -> metadata`; `resolve_pdf(id) -> Path` e alias `get_path`: verificam integridade antes de retornar. Retorno do path não fixa o arquivo contra exclusões posteriores; abertura posterior ainda pode falhar e deve ser tratada na UI.
- `export_copy(id, target, overwrite=False) -> Path`: cópia local exata, privada e atômica; não cria destino dentro do acervo gerenciado. UI confirma overwrite antes de autorizar.
- `delete(id) -> None`: após confirmação UI, exclui somente registro/cópia gerenciados. Nunca conhece nem exclui o PDF externo ou cópias baixadas.

Metadata contém `version`, `id`, `created_at` UTC, `snapshot` canônico completo, `sheet_id/sheet_name`, `client_name`, `client_key` (alias `client_id`), `issued_on`, `issued_year/issued_month` inteiros, `reference`, `period`, `hours/minutes`, `rate/total/currency/language`, `pdf_sha256`, `pdf_size`. Não contém path do PDF externo.

## Armazenamento e agrupamento

Padrão `${XDG_DATA_HOME:-~/.local/share}/orbitz-widgets/invoices`, raiz e pasta de cada registro `0700`; `invoice.pdf`, `metadata.json` e lock `0600`. Diretórios usam somente UUID hexadecimal de 32 posições gerado internamente, sem nomes/documentos. Cliente é agrupado por SHA-256 do CPF/CNPJ normalizado (sem pontuação, maiúsculas), portanto cru/pontuado coincide e homônimos com documentos diferentes ficam separados. Hash é chave interna de agrupamento, não anonimização do documento contido no snapshot privado.

Empresa é identidade da timesheet preservada no snapshot; mês/ano derivam de **emissão**, não do período de serviços. Alterações futuras no cliente/perfil/timesheet/PDF externo não mudam o registro emitido. IDs e timestamps distinguem duplicatas intencionais de referência; não há deduplicação silenciosa.

Sem índice global: cada diretório publicado contém exatamente os dois arquivos. Snapshot é revalidado pelo domínio; metadados derivados são validados em todas as operações. List lê somente metadata e confere tipo/tamanho do PDF; get/export/resolve/delete leem os bytes e conferem hash completo. Corrupção de mesmo tamanho será detectada na consulta/abertura/exportação, não na listagem. Leituras limitadas a PDF 128 MiB e metadata 4 MiB, arquivos regulares com `O_NOFOLLOW|O_NONBLOCK`, rejeição de caminhos raiz vinculados e de IDs/path traversal. Não renderiza/reinterpreta PDFs antigos nem faz varredura externa. Assinatura `%PDF-` mais hash verifica bytes armazenados, não validade estrutural completa de um PDF arbitrário; origem normal é o renderer já validado pelo fluxo de exportação.

## Concorrência, publicação, exclusão e falhas

Lock privado por raiz com flock serializa operações cooperantes. Record escreve em staging privado com fsync de ambos arquivos/diretório, depois publica diretório por rename e fsync da raiz. Falha anterior à publicação não altera registros anteriores/PDF externo, nem deixa staging normal. Processo interrompido pode deixar `.record-*`; list mostra aviso genérico e preserva esses arquivos para recuperação, sem limpeza silenciosa.

Export usa temporário `0600`, fsync e hardlink no-clobber quando não existe destino. Overwrite autorizado exige arquivo regular sem symlink e valida inode/tamanho/mtime antes de replace. Destino surgindo durante cópia é preservado. Temporários limpos em `finally`. Falha de fsync após publicação não promete rollback de arquivo já publicado; UI trata aviso conforme resultado/erro, sem apagar existentes.

Exclusão valida o registro, renomeia somente sua pasta para `.deleted-ID` sob o mesmo lock e limpa essa pasta privada. Se limpeza falha, informa explicitamente que o registro saiu da lista e a limpeza está pendente; list acusa operação interrompida. Não há limpeza automática/retomada silenciosa dessa pasta, nem exclusão de registro corrompido sem validação: conteúdos inválidos são preservados para diagnóstico. Essa limitação não implica risco ao PDF externo, às horas ou aos perfis. Corrupção/inconsistência não é consertada descartando dados.

Permissões/lock e checagens protegem operações normais e casos testados, sem alegar transação global com processos externos não cooperantes ou tolerância integral a corte de energia. O arquivo retornado por resolve_pdf pode ser removido legitimamente por outra operação após liberar o lock.

## Evidência específica

`/usr/bin/python3 -m unittest discover -s tests -p test_invoice_history.py -v`: **10/10 aprovados**.

Fixtures: bytes `%PDF-...` sintéticos, diretórios temporários e seis subprocessos com XDG_DATA_HOME temporário. Nenhum novo render PDF, nenhuma consulta ao acervo pessoal.

1. Lista vazia não cria armazenamento.
2. Bytes/snapshot preservados, permissões, IDs distintos com referência repetida e ausência de path externo no metadata; mudar PDF externo/perfil não muda registro.
3. Documento cru/pontuado/alfanumérico normaliza, homônimos permanecem separados, agrupamento por emissão difere de período de serviços.
4. Registro corrompido isolado; lista mantém válido e export/get/delete recusam corrompido sem mutação.
5. Falha na gravação de metadata mantém PDF externo/registro anterior e limpa staging normal.
6. IDs inválidos/path traversal, symlink no PDF/raiz/origem recusados e alvo externo preservado.
7. Download exato `0600`, overwrite explícito, no-clobber com criação concorrente de destino e recusa de export para dentro do acervo.
8. Delete remove apenas registro escolhido, mantendo PDF externo, download, outra invoice e arquivos sentinela de notas/perfil.
9. Seis processos arquivam a mesma emissão com seis IDs distintos, sem perder registro.
10. List não lê bytes de PDFs; corrupção de mesmo tamanho é detectada no resolve_pdf (hash completo). Sem alegação de benchmark/ganho medido.

## Próximos responsáveis e limites

Frontend integra histórico/menu/agrupamento/ações e warnings independentes de archive/perfil. Supervisor atualiza documentação de produto e coordena integração/auditoria. Auditor verifica segurança/integridade de forma independente após estado estável. Validação de UI/visual não foi feita pelo backend. Sem suíte global durante mutações concorrentes, instalação, GSettings, arquivos reais de usuário, migração/importação de PDFs antigos, commit/push ou publicação. Renderer/cálculos/estado INV-02 dos colegas preservados.

## Correção após auditoria — atividade malformada em metadata

Auditor reproduziu P2: `snapshot.entries=[null]` em um metadata fazia o domínio esperar dict e lançar AttributeError, derrubando a lista inteira. Registro válido e bytes não eram perdidos, mas faltava isolamento da corrupção estrutural.

Adicionada validação explícita da fronteira JSON no histórico (`_validated_snapshot`): snapshot deve ser dict, entries deve ser lista e cada atividade deve ser dict antes de chamar o validador de domínio. Registro estruturalmente inválido produz ValueError esperado, isolado na listagem. Não foi acrescentado catch genérico nem captura indiscriminada de bugs; domínio/render e arquivo corrompido não foram alterados.

Teste reproduz dois registros, altera somente um para entries=[None], confirma bom+errors e bytes corrompidos intactos; get do bom funciona, get/record de estrutura inválida recusam explicitamente. `/usr/bin/python3 -m unittest discover -s tests -p test_invoice_history.py -v`: **11/11 aprovados**. Alvo estável enviado ao auditor para nova verificação independente, com supervisor informado. Sem acesso a dados reais/instalação ou mudança na API.
