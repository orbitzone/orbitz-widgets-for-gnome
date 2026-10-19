# INV-04 — versões PDF apresentadas como assinadas

Data: 19/10/2026. Estado: backend estável, testes específicos aprovados; integração frontend e auditoria independente pendentes. Sem instalação, arquivos reais de usuário ou testes de render PDF.

## Escopo e limite funcional

Novo `extension/planner/invoice_signatures.py`, alteração compatível em `invoice_history.py` e novo `tests/test_invoice_signatures.py`. Nenhuma alteração em renderer, cálculo, perfis, ferramentas, UI ou dados pessoais. Histórico versão 1, metadata e bytes do PDF original permanecem iguais. A única extensão de layout é uma pasta opcional `versions/` dentro de cada registro.

**Todas** as versões têm estado `imported_pending_validation` e rótulo `Importada, validação pendente`. Não há detecção de assinatura, validação criptográfica, confirmação de correspondência com o original, certificado/credencial, OAuth, upload automático ou chamada de API gov.br. Prefixo `%PDF-`/hash são verificações de armazenamento, não provas de assinatura ou autenticidade. Associação ao original é a seleção confirmada pelo usuário na UI; o hash do original registra essa referência, sem estabelecer vínculo criptográfico de assinatura.

Frontend aceitou o contrato e implementa assistência manual por URLs fixas, seleção externa e confirmação do vínculo. Clicar em serviço externo/VALIDAR não altera status no backend, que não oferece API de marcar uma versão como validada.

## API fixada

Todas as funções aceitam `root=None` como keyword opcional para testes; padrão é a mesma raiz privada do histórico.

- `import_version(invoice_id, pdf_path) -> metadata`, alias `add_version`.
- `list_versions(invoice_id) -> {'versions': [...], 'errors': [{'id','message'}]}`.
- `get(invoice_id, version_id) -> metadata`.
- `resolve_pdf(invoice_id, version_id) -> Path`, aliases `resolve_version` e `get_path`.
- `export_copy(invoice_id, version_id, target, overwrite=False) -> Path`, alias `export_version`.
- `delete(invoice_id, version_id) -> None` após confirmação UI. Disponível, mas frontend informou que não expõe exclusão individual nesta etapa.

Metadata de versão: `version=1`, `id`, `invoice_id`, `original_pdf_sha256`, `pdf_sha256`, `pdf_size`, `created_at` UTC, `status`, `status_label`. IDs são UUID hex de 32 posições gerados internamente, sem nome/CPF/path externo. Cada importação recebe novo ID mesmo se os bytes se repetem. Não há sobrescrita de versão existente nem modificação posterior do status.

## Persistência e operações

Cópia exata dos bytes apresentados em `<invoice_id>/versions/<version_id>/invoice.pdf` e metadata correspondente. Pasta `versions/` e pasta de versão `0700`, PDF/metadata `0600`. Limite PDF 128 MiB, mesma leitura regular/no-follow/limite/estabilidade do histórico. Fonte dentro da raiz gerenciada é recusada, inclusive por caminho resolvido; PDF externo ou sua symlink não viram aliases do arquivo gerenciado.

Usa o lock global já existente do histórico para serializar importação/consulta/exportação/exclusão cooperantes, incluindo exclusão da fatura inteira. Importação verifica o original, escreve dois arquivos em staging privado, fsync e publicação por rename, sem tocar o metadata/PDF original. Falha antes da publicação preserva originais/versões anteriores e fonte externa. Sem índice global nem nova dependência.

Listagem usa metadata e tipo/tamanho de PDF; não carrega bytes de todos os PDFs. Metadados corrompidos/estado falso/pasta inesperada geram erros isolados. Consultar/abrir/exportar/excluir versão verifica hash completo e vínculo de IDs/hash armazenado do original. Corrupção de mesmo tamanho pode aparecer apenas nessa verificação completa, sem alegação de ganho de desempenho medido.

Original histórico aceita `versions` opcional sem inspecionar seu conteúdo ao listar/consultar/exportar o PDF original. Portanto versão ou pasta de versões inválida não inutiliza o original. A listagem específica de versões relata o problema sem descartar arquivos.

Exportações originais e versões reutilizam helper privado `_export_bytes` em `invoice_history`: temporário `0600`, fsync, publicação no-clobber com hardlink, overwrite explícito com revalidação inode/tamanho/mtime, recusa de destino dentro da raiz gerenciada. A API pública de histórico não mudou.

## Exclusão confirmada e limites de recuperação

`invoice_history.delete(invoice_id)` agora inclui todas as versões gerenciadas da fatura. Antes de retirar a pasta original da lista, verifica que `versions` é diretório real, filhos são IDs reconhecidos (ou tombstones `.deleted-ID`) e arquivos remanescentes são apenas PDF/metadata regulares. Não segue symlinks nem remove conteúdo inesperado silenciosamente. Metadata de versão corrompido não impede a exclusão da fatura inteira quando o layout é gerenciado e a pessoa confirmou; original precisa continuar válido segundo as regras do histórico.

Exclusão individual verifica a versão e renomeia somente sua pasta para `.deleted-ID` antes da limpeza. Não altera original nem outras versões. Como no INV-03, falha de limpeza deixa tombstone privado e mensagem explícita de pendência; a lista específica aponta erro e não há retomada automática prometida. Exclusão da fatura inteira confirmada pode remover os tombstones gerenciados remanescentes. PDFs externos, cópias exportadas, horas, tarefas e perfis nunca são alvos da exclusão.

Proteções não constituem transação global contra escritores externos não cooperantes; resolve_pdf libera o lock antes da abertura posterior e uma exclusão legítima pode invalidar o caminho. Falha de fsync após publicação não promete desfazer bytes já publicados. Nenhuma retenção/exclusão automática foi criada.

## Verificação específica

- `/usr/bin/python3 -m unittest discover -s tests -p test_invoice_signatures.py -v`: **10/10 aprovados**.
- `/usr/bin/python3 -m unittest discover -s tests -p test_invoice_history.py -v`: **11/11 aprovados**, sem alterar/enfraquecer seus testes.

Cenários novos:

1. Múltiplas cópias exatas privadas com IDs diferentes; arquivo externo alterado depois não muda versão; hash de origem/versão e estado pendente, mesmo quando fixture explicitamente não é assinada.
2. Invoice histórica v1 sem pasta de versões mantém API e não cria pasta em leitura.
3. Metadata de versão forjado para status verificado é recusado/isolado; versão boa e original permanecem acessíveis, bytes corrompidos preservados.
4. List não lê PDFs; alteração de bytes com mesmo tamanho é recusada ao abrir pelo hash completo.
5. Fonte interna, IDs inválidos/traversal, fonte symlink/pasta versions symlink recusados; original permanece consultável, alvo externo preservado e exclusão inteira recusa layout vinculado.
6. Falha no metadata de importação mantém versão prévia, original, ambas fontes externas e limpa staging normal.
7. Exportação exata `0600`, recusa de overwrite não confirmado, overwrite confirmado e proteção contra destino do original dentro do acervo.
8. Exclusão individual preserva original/outra versão; exclusão inteira remove somente originais/versões gerenciados e mantém ambos PDFs externos.
9. Prefixo/tamanho e hash de referência original inválidos recusados; nenhuma inferência de assinatura é feita.
10. Seis subprocessos importam em paralelo com seis IDs/cópias, original e metadata intactos.

Fixtures `%PDF-...` sintéticas e diretórios temporários. Sem render, PDF QA novo, banco/cofre, rede, documentos reais, GSettings ou scan de acervo existente. Não foi repetida suíte global durante edição frontend.

## Próximos responsáveis

Frontend integra assistente/manual de vínculo, diálogos/status fixo e exportações selecionadas; supervisor atualiza requisitos/documentação e combina integração; auditor verifica integridade/isolamento independentemente no alvo estável. Validação de UI e execução de serviços externos pelo usuário são distintas da validação de armazenamento. Backend notificado como estável sem alegar autenticação/assinatura validada ou instalação concluída.
