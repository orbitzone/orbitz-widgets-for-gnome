# INV-04 — auditoria dirigida de assinatura assistida — 19/10/2026

Estado: **funcional local/integridade delimitada aprovadas, sem impeditivo reproduzido; UI real e serviços externos não exercitados**. Não houve assinatura digital, validação criptográfica, upload, login gov.br, credenciais, instalação ou leitura de acervo real.

## Alvo e execução independente

Backend/frontend declarados estáveis; lidos módulos/testes, relatórios invoice-signatures-backend/frontend e mudanças no histórico. Sources/hashes no final. Auditor não modificou código. PDFbytes novos exclusivamente sintéticos, inclusive arquivo explicitamente sem assinatura; não repetida renderização/QA do PDF.

```bash
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p 'test_invoice*.py' -v
git diff --check -- extension/planner/invoice_history.py extension/planner/invoice_history_ui.py extension/planner/invoice_signatures.py extension/planner/invoice_signatures_ui.py
```

**62/62 aprovados**,2,021s:47regressõesinvoice/histórico/período+10novosbackend+5novosfrontend. AST dos6arquivos e diff-check aprovados. Sem suíte global ou mudança de dependência. Warning preexistente load_module da dependência ReportLab apareceu nas regressõesPDF, sem falha; workflowPDF já aplicado, somente temporários. Testes de assinatura não renderizam PDF nem abremURLs: launcher é mock e recebe apenas URL fixa.

## Contratos e integridade

- Registros históricos v1 sem versions continuam list/get/copy compatíveis; leitura não cria pasta. Original metadata/PDF permanecem byte a byte intactos ao importar múltiplas versões e alterar fontes externas depois. Histórico aceita somente pasta opcional versions além dos dois arquivos originais.
- Importação exige confirmação de vínculo na UI e PDF externo; root interno/IDtraversal/symlink/tamanho/prefixo inválidos recusados. UUIDhex de cada versão, sem CPF/nome/path pessoal em arquivo. Root lock comum serializa original/versões; diretórios0700 e arquivos0600. Staging/EXCL/fsync/rename protegem publicação; falha metadata limpa staging e mantém todas as cópias anteriores/externas. Seis processos mantiveram seis versões e original intacto.
- Metadata de versão registra invoice_id e hash do original, hash/tamanho do PDF importado,UTC e status fixo imported_pending_validation. Esses campos ligam armazenamento a um ID/original conhecido; **não comprovam igualdade semântica do conteúdo, existência/validade de assinatura ou identidade do signatário**. Prefixo %PDF não é validação completa de estrutura PDF. Testes aceitam deliberadamente fixture não assinada e não inferem validade.
- Lista versões valida metadata/stat sem ler todosPDFs; ações get/resolve/export/delete da versão leem/hash seus bytes. Corrupção de status verificado/hash/vínculo é recusada e isolada, versão boa e original seguem disponíveis. Alteração com mesmo tamanho pode surgir em listagem e é recusada na ação. Hash detecta alteração contra metadata esperada, não autentica contra agente que possa reescrever metadata+PDF juntos.
- Consulta/cópia roteia par invoiceID/versionID exato; Original usa API original. Shared _export_bytes mantém publicação no-clobber sem overwrite e stamp antes de substituir com autorização; destinos gerenciados recusados e temporários privados/limpos. Nenhum caminho gera upload/execshell; abrir arquivo é URI local Gio na interface lida.
- Delete de versão usa somente sua pasta/tombstone e conserva original/outra versão/externos. Deleteinvoice confirma original+todasversões gerenciadas e valida layout de versions antes de remover; links/especiais/nomes inesperados recusados. Fontes externas/downloads/horas/perfis não são alvo. Falha de limpeza mantém tombstone/aviso sem promessa de retry/limpeza automática integral. Nenhuma exclusão real nesta auditoria.

## Assistência, rótulos e cancelamento

Assinar com gov.br exibe instruções manuais, pede cópia externa e só chama launcher se cópia concluiu. Cancelamento/cópiafalha não abrem portal. Falha de launcher retorna cópia salva sem alegar portal aberto. URL constante https://assinador.iti.br/ recebe nenhum filename/conteúdo/token/identificador. Não houve navegação real, verificação remota de disponibilidade do portal ou interação com conta.

ImportOPEN seguido de confirmação de invoice/referência/cliente/período esclarece ausência de verificação criptográfica/correspondência e possibilidade de arquivo não assinado. Cancelar não chama import. UI mostra rótulo constante “Importada — validação pendente”, sem confiar em label fornecido por metadata. Original/versões ficam em diálogo separado com ações só para seleção válida; cabeçalho inválido bloqueia path/export.

VALIDAR chama apenas https://validar.iti.gov.br/ em resposta a ação do usuário; não passa arquivo e não atualiza status. Abrir portal não é obter resultado de validação. Nenhum OAuth/segredo/cofre/rede/cryptoengine implementado ou executado. Serviços e login/upload/assinatura/download/verificação são atividades manuais posteriores fora da auditoria local.

Teste integração frontend com backend REAL/ROOTtemp cria original e duas versões diferentes, confirma cópias exatas0600 e metadataoriginal intacta, recusa destino gerenciado, canceldeletepreserva e deleteinvoice remove somente gerenciados mantendo três fontes externas. Cancelamentos e seleção correta verificados sem GTK nativo.

## Achados, limites e conclusão

**Nenhum achado impeditivo reproduzido nos62casos e na revisão dirigida.** Integridade local/compatibilidade e status conservador aprovados no escopo. Não é aprovação criptográfica, jurídica/fiscal, autenticação de documento ou prova de que o PDF importado corresponde à invoice. Não se alega transação global contra editores externos nem resistência integral a corte de energia/perda de diretório. Sem benchmark/desempenho medido.

GTK/AT/foco/FlowBox/lista/chooser/confirmnativa e comportamento browser real permanecem pendentes. Parecer UX estático recebido viafrontend não substitui GUI. Sem necessidade de renderQA novo porque renderer não mudou. RAM/EXT e outras pendências separadas.

Supervisor integra documentação e aceite, coordena atualização somente autorizada e orienta testes manuais reais posteriores. Auditor não instalou/ativou/abriuportais. Após atualização de módulosPython, encerrar/reabrir agenda para carregar fontes novas; não há necessidade demonstrada de logoutGNOME por este fluxo.

## Hashes finais

| Arquivo | SHA-256 |
|---|---|
| `extension/planner/invoice_history.py` | `596158523c77a5ebbdfca58162df092c95bc226d800cdb3d7ab5aac123e6c797` |
| `extension/planner/invoice_history_ui.py` | `84b194428883a6231f3b9e00c81819c06c7c22cfdfd3a181d454aacd43266a92` |
| `extension/planner/invoice_signatures.py` | `89b94f8f66b6d8084075f7bc65ae27bcfd3cb60420456b49a8c81c922b60ebfd` |
| `extension/planner/invoice_signatures_ui.py` | `73d984d7553bf4410c86ed2e38ad15e6a194b9f7760b468867823431f5c44b05` |
| `tests/test_invoice_signatures.py` | `3fb97385c09a01c5fd0af261e4d71aa43c971909d196dc5b7893be6a0c946582` |
| `tests/test_invoice_signatures_frontend.py` | `b6c1f3d3860d16a10a9e66ca69d4616c7bc6f56becdd0226493fea79b5362ef9` |

## Integração adicional solicitada no fechamento

Script independente com history/signatures/SignatureSession/HistorySession REAIS, ROOTtemp e bytesPDFsintéticos: recordoriginal→cancelimportsemversão→attachduasversões→list→resolveoriginal→assist_sign/exportoriginal com launcherfake→open_validatorfake→resolve/exportversão→deleteindividual→canceldeleteinteira→deleteinteira. Resultado aprovado: metadataoriginal ebytes originaisintactos antesdaexclusão,outraversãopendenteacessível,cópiasexactas,PDFsfontes/downloadexternospreservados depois. ListaURLfake recebeu somente os dois endpoints fixos e nenhuma abertura real; nenhuma escrita de status validado. Este ensaio é adicional aos62testes, não contabilizado como unittest novo. Não alterou fontes,renderer,acervopessoalouinstalação.
