# INV-03 — auditoria do histórico de faturas — 19/10/2026

Estado intermediário: backend inicial10/10 aprovados, integração adicional real em temporários aprovada; achado IH-A01 pendente de correção/rechecagem antes de concluir. Não é aceite integrado ou instalação executada.

## Escopo e evidências iniciais

Lidos invoice_history.py/teste e frontend historyUI/hook/session. `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p test_invoice_history.py -v`:10/10 aprovados,0,482s. Sem suíte global durante alterações; sem dados reais, instalação, PDFs pessoais, envio externo ou render adicional.

### IH-A01 — corrupção estrutural interrompe listagem completa — P2, reproduzido

Dois registros temporários via record com snapshot sintético/PDFbytes sintéticos. Em metadata.json de um, substituir snapshot.entries por [None]. list_records aborta AttributeError: NoneType object has no attribute get, enquanto get do bom continua funcionando. _get→invoice.validate_snapshot→build_snapshot→timesheet.validate_activity não valida elemento antes de raw.get; list_records não normaliza/isola esse erro estrutural. Nenhum byte perdido, legado/externos preservados. Requisito corrupção isolada não atendido nesse cenário. Comunicado ao supervisor/backend; não corrigido pelo auditor. Critério: bom disponível e erro privado no registro danificado sem apagar/regravar acervo, com validação de estrutura na fronteira adequada.

## Integração adicional solicitada pelo supervisor

Script independente com InvoiceSession.prepare/export e mocks apenas do writerPDF (grava bytes %PDF sintéticos), ROOT history e PATH profiles temporários. Funções record/save/list/get/resolve/export_copy/delete REAIS. Conferidos snapshot exato,01:30horas/taxa125.50/total188.25,cliente perfil e modo0600,bytes exatos no gerenciado/cópia,externo+download preservados após delete e origem timesheet sem alteração. Nenhum novo render ou dado pessoal. Esse caso amplia o teste frontend de adapter, que isola profiles.save com mock; aqui perfis e histórico foram ambos reais.

Frontend declarou estável8testes; auditor aguarda alvo backend corrigido para executar integração/regressões e concluir relatório. Não repetir suíte global ou QA PDF sem motivo.

## Rechecagem IH-A01 e novo limite IH-A02

IH-A01 corrigido em _validated_snapshot: valida dict/list/entrydict antes do domínio, normaliza estrutura ruim para ValueError sem capturar AttributeError genérico. Execução independente11/11 history aprovada,0,510s, incluindo novo cenário de registro bom+entries=[null] em outro; corrupto preservado e erro isolado. IH-A01 encerrado para o cenário reproduzido.

### IH-A02 — nova exportação pode sobrescrever PDF gerenciado — P2, reproduzido

Por indicação do supervisor, criado registro temporário existente e passado resolve_pdf(id) como filename a InvoiceSession.export(overwrite=True). Writer mock gravou PDF sintético distinto no caminho; export retornou warning vazio, e get do registro antigo passou a falhar integridade/hash. Todas as fontes eram sintéticas. export_copy já recusa destino no ROOT; a exportação inicial ainda não aplicava a mesma fronteira antes do writer. O fato de overwrite ter sido confirmado não autoriza alterar emissões gerenciadas imutáveis pelo requisito INV03.

Frontend/supervisor comunicados. Critério: recusar destino gerenciado antes de writer/archive/profile, incluindo caminho resolvido por symlink ancestral e ROOT sem depender de existência prévia do arquivo; preservar bytes/emissão anterior. Não alterar renderer global por esse guard de fluxo. Nenhuma correção pelo auditor, nenhuma instalação/dado real. Conclusão integrada permanece pendente até correção frontend estável e testes dirigidos.

## Parecer integrado após correções estáveis

IH-A02 corrigido em check_external_destination antes do writer: confere limite lexical absoluto e limite resolvido contra ROOT gerenciado; falha de verificação é recusada. Novo teste com registro real temporário tenta PDFgerenciado anterior, novo nome sobROOT, ancestral symlink, symlink de arquivo e caminho lexical sobROOT com ..; writer/archive/profile não são chamados, bytes/hash anteriores preservados. A rejeição lexical conservadora de caminhos sobROOT é deliberada. Não é proteção contra toda troca maliciosa de diretório após checagem por processo externo não cooperante; não se promete transação global de filesystem.

### Execução final independente

```bash
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p 'test_invoice*.py' -v
git diff --check -- extension/planner/invoice_ui.py extension/planner/invoice_history_ui.py extension/planner/planner_menu.py
```

**47/47 aprovados**,1,663s:11backendINV01+6frontendINV01+11histórico backend+9históricofrontend+10períodoINV02. São casos distintos desta execução; testes parciais anteriores não são somados novamente. AST dos6arquivos abaixo e diff-check aprovados. Nenhuma suíte global repetida. PDFs de regressão temporários usam workflow já estabelecido, sem novos renders/QA ou documento real; warning load_module preexistente da dependência sem falha.

### Revisão funcional e segurança/integridade

- Arquivo externo é copiado byte a byte ao root privado, junto a snapshot validado/metadados imutáveis por registro; novas emissões/referências repetidas geram UUIDs distintos. Paths não incluem cliente/CPF/nome. Alterar/remover externo depois não altera acervo; alterar perfis/horas não recalcula emissão anterior. Metadados não retêm caminho externo.
- Root/diretórios0700,PDF/metadata0600; lock0600/flock, staging e rename/publicação com fsync,sem índice global. Seis processos concorrentes preservaram seis IDs/cópias. Falha de metadata preserva externo/registro anterior e limpa staging. Não há alegação de resistência integral a falha física/corte de energia ou editores externos não cooperantes.
- IDs32hex rejeitam traversal/absolutos/variações; root ancestral simbólico recusado, fonte/arquivos com NOFOLLOW/NONBLOCK/fstat e limites128MiBPDF/4MiBmetadata. Links/especiais/conteúdo inesperado são recusados e preservados. Estrutura inválida de snapshot agora normalizada na fronteira; recordcorrompido não derruba listagem boa.
- Listagem lê metadata e stat de PDF, sem carregar/hash de todo acervo. Teste intercepta _read para impedir leituraPDF durante browsing. Corrupção com mesmo tamanho pode aparecer na lista e é recusada na ação; get/resolve/export/delete verificam bytes/hashes completos. Listagem não é certificação de integridade de conteúdo. Sem benchmark, não se afirma ganho percentual/desempenho medido.
- SHA256 detecta alteração acidental/entre estados esperados, não autenticidade contra usuário que possa reescrever simultaneamente PDF e metadata/hash. Root privado reduz exposição local; não é assinatura fiscal/digital nem cadeia inviolável.
- Agrupamento UI por sheet_id/client_key(CPF-CNPJnormalizado e hash)/ano-mês de emissão, não por nomes homônimos ou período do serviço. Registros do mesmo mês/mesma referência não se substituem. Labels podem coincidir por nomes, mas identidade/ação permanecem distintas; sugestão UX de melhorar diferenciação visual é separada do contrato de integridade.
- Consulta resolve/get_path validado e abre URI viaGio, sem shell. Ações só em folha/ID selecionado; cabeçalhos/canceldelete não operam arquivos. Detalhes distinguem mês de emissão e período de serviços. Lista vazia vs toda ilegível vs parcial são mensagens diferentes, mantendo invoices válidas disponíveis.
- Copiar usa no-clobber atômico sem autorização e overwrite explícito com stamp; destino dentroROOTrecusado. Confirmação nativa chooser/caminho e extensão.pdf presentes no fluxo; testes session/armazenamento não comprovam GTK real. Cancelamento não executa cópia.
- Exclusão exige confirmação UI que identifica registro/referência/cliente/emissão e limita cópia gerenciada. Backend verifica registro, rename para .deleted-id e remove somente esse diretório; não toca PDFexterno/download, notes,perfis,horas ou outrosIDs. Falha de limpeza retém tombstone e aviso; listagem reporta interrupção sem limpeza automática, não promete retry integral. Nenhuma exclusão real foi executada nesta auditoria.
- Exportação inicial preserva PDF externo bem-sucedido mesmo se archive falha; aviso parcial específico e persistência de perfil independentes. FalhaPDF não chama archive/profile. NovoguardIH-A02 impede exportar sobre armazenamento gerenciado antes de qualquer write. Integração adicional com history+profiles reais temporários, descrita acima, confirmou contrato completo sem renderer.

### Conclusão e próximos responsáveis

**IH-A01 e IH-A02 resolvidos nos cenários reproduzidos; nenhum impeditivo restante no escopo auditado.** Funcional local/limites de exclusão, privacidade e integridade aprovados pelos47testes e revisão dirigida. Não equivale a segurança integral, assinatura/inviolabilidade do acervo ou emissão oficial.

Visual/interação GTK/AT,FlowBox/foco,chooser overwrite e confirmação delete nativos permanecem pendentes. UX estático favorável é evidência separada viafrontend; não é captura gráfica. Não houve mudança no renderer/QA de PDF, nenhum render duplicado, performance medida, instalação, credencial ou acervo real. RAM/EXT e outras tarefas não são resolvidas pelo histórico.

Supervisor integra aceite/documentação e eventual atualização autorizada; usuário/frontend validam menu/consulta/cópia/cancel/exclusão na agenda real. Instalação não executada pelo auditor. Encerrar/reabrir agenda após atualizar módulos, sem necessidade demonstrada de logoutGNOME.

### Hashes finais

| Arquivo | SHA-256 |
|---|---|
| `extension/planner/invoice_history.py` | `84557f8957de8f885a7b8f0495de23fde4c21a5e4c660b2144ebf157f8354b57` |
| `extension/planner/invoice_history_ui.py` | `2967e0d2502725e8f3db356584019faff5bed10548f2fc0ed4934ba789167fa7` |
| `extension/planner/invoice_ui.py` | `017a9820405e49edba92e17472ae441e41fcedf47c485cb9ce26bdcfa201d898` |
| `extension/planner/planner_menu.py` | `725aa45d43279b601cf9b4972302fe79396f03c4b7da91d218b0629779a4ccd6` |
| `tests/test_invoice_history.py` | `8fa7071b14e89b97d841b6c97cea97fc727fe079281ba45c729ac76fce7fb31a` |
| `tests/test_invoice_history_frontend.py` | `a40c0111205009a78022fa6d2b40e3110751949374a90d32404b1b2d1b15f55e` |
