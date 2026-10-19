# INV-04 — assinatura gov.br assistida e versões importadas — frontend — 19/10/2026

Estado: **implementado com testes específicos aprovados; parecer UX estático recebido e ajustes locais aplicados; auditoria/GTK pendentes**. Sem instalação, acervo real, navegação de portal, login, credenciais, rede, sessão ativa, publicação ou PDF QA/renderização.

## Entrega

- `invoice_history_ui.py`: folha principal identificada como Invoice; original identificado nas ações Consultar original/Salvar cópia do original e na lista de versões. Acrescentadas Assinar com gov.br, Adicionar versão assinada e Original e versões. Continuam desabilitadas em cabeçalhos/sem invoice selecionada. Exclusão da invoice confirma original **e todas as versões importadas gerenciadas**, sem PDFs externos/horas.
- `invoice_signatures_ui.py`: módulo coeso com fluxo puro de assistência, sessão de versões, chooser de cópia reutilizado e diálogos de importação/versões. Imports GTK/backend tardios, sem acesso ao acervo na importação da agenda.
- `test_invoice_signatures_frontend.py`: testes de cancelamento/URLs/estado e integração de versões em raiz temporária. Módulos de histórico/período/exportação não foram reimplementados.

## Fluxo assistido e privacidade

Assinar com gov.br mostra instruções e Cancelar default. Usuário salva uma cópia usando FileChooser seguro; só depois do retorno bem-sucedido de export_copy o helper abre **exclusivamente** `https://assinador.iti.br/` via Gio/navegador externo. Cancelar ou falhar ao copiar não abre portal. Falha do navegador depois da cópia é distinguida de falha ao copiar. Instruções: login prata/ouro no portal, upload manual, assinar, baixar, voltar e importar. Nenhum PDF, nome/path, dado de cliente ou credencial entra na URL. Nenhuma automação do navegador/login/upload foi criada.

Adicionar versão assinada usa chooser OPEN PDF e confirmação de vínculo com referência/id/cliente/período. Mensagem explícita: sem verificação criptográfica nem correspondência automática; o arquivo pode não estar assinado. Cancelar escolha/confirmação não chama import_version. Backend recebe o arquivo escolhido e guarda os bytes; frontend nunca regenera ou altera PDF importado. Original e versões anteriores permanecem.

Diálogo separado Original e versões lista o PDF gerado original e as importações com timestamp/id curto. Cada importação mostra o texto fixo **Importada — validação pendente**, independente de extensão, nome, hash ou status_label recebido. Ações Consultar/Salvar cópia operam só a seleção exata (original ou versão), usando API apropriada e Gio URI para consulta; cópia mantém guard/overwrite do backend e confirmação do chooser. Cabeçalho da lista não possui ações de arquivo.

Verificar no VALIDAR abre **exclusivamente** `https://validar.iti.gov.br/` sem arquivo ou parâmetros. O usuário faz upload manual. Abertura ou confirmação manual não altera metadados/status local e não declara validade ou existência de assinatura. Aviso na janela torna esse limite explícito. Não há opção local Marcar validada.

## API e interface

`invoice_signatures.import_version/list_versions/resolve_pdf/export_copy` alinhados diretamente com backend. Original usa history.get_path/export_copy; exclusão completa continua history.delete após confirmação. Delete de uma versão individual é opcional e não foi exposto nesta entrega. ROOT, IDs seguros, permissões, imutabilidade e hash são responsabilidade backend; nenhuma dependência criptográfica ou de renderer foi adicionada.

Versões em diálogo separado evita varrer todas as versões a cada reload geral. Modal limitado à workarea, lista com scroll/wrap e ações em FlowBox. Texto de feedback selecionável; consulta/cópia/VALIDAR ficam desabilitados sem seleção. Renderização GTK/AT/foco/longos textos e chooser nativo não exercitados, sem nova tentativa Broadway.

## Verificações

`python3 -m unittest discover -s tests -p test_invoice_signatures_frontend.py -v`: **5/5 aprovados**:

1. Cancelamento/falha de cópia nunca abre portal.
2. Só sucesso da cópia precede URL fixa do assinador; falha/retorno False do launcher preserva resultado cópia salva.
3. VALIDAR recebe URL fixa, sem dados de arquivo; status/metadata não mudam e rótulo não usa afirmação externa de validade.
4. Import cancelada não chama backend; confirmação, consulta/cópia original vs versão roteiam IDs exatos e overwrite explícito; seleção inválida bloqueia ações.
5. Integração REAL com ROOT temporária e bytes PDF sintéticos: duas importações distintas, ambas pendentes, bytes exatos, cópias privadas0600, destino dentro do acervo recusado, original metadata/PDF intactos. Exclusão cancelada mantém versões; exclusão confirmada da invoice remove somente gerenciados e preserva arquivos externos. Nenhum PDF foi renderizado ou enviado a portal.

`python3 -m unittest discover -s tests -p test_invoice_history_frontend.py -v`: **9/9 regressões aprovadas**, incluindo IH-A02 e isolamento do acervo. Sem repetição da suíte global/QA PDF. AST e diff-check das fontes frontend conferidos ao estabilizar.

## UX, auditoria e fechamento

Brief/implementação enviados ao UX pelo canal autorizado, com pedido de revisar texto de assistência manual, vínculo/estado pendente, ações por versão e confirmação de exclusão. Parecer final será repassado ao supervisor/auditor. Sem alegação de validação gráfica/criptográfica/correspondência documental.

Backend informou testes próprios de assinatura/histórico estáveis e preservação do original; evidências não foram reapresentadas como teste frontend. Supervisor coordena auditoria e RC-17 (comando de atualização/aplicação/reabertura quando autorizado). Frontend não declara instalação concluída. Branding, períodos, menu geral e hooks existentes preservados; RAM/EXT fora do escopo.

## Parecer UX e decisão de navegação

Parecer em `docs/design/2026-10-19-invoice-signatures-review.md`: textos/ordem da assistência, cancelamento, status pendente, URLs fixas/manual e confirmação de exclusão conformes ao estado examinado. Implementação usa diálogo separado de versões, opção técnica dentro da proposta de histórico que poderia mostrar folhas sob invoice; essa escolha foi informada ao supervisor, sem alegar equivalência visual com árvore inline. Folha principal agora chama-se Invoice, reservando Original às ações de arquivo e à lista de versões. Wrap da lista adapta-se à largura e cancelamento de cópia retorna foco ao acionador em ambas as janelas. Ajustes posteriores ao parecer são evidência frontend; sem reinspeção GTK/AT. Integração real já comprovada nos cinco testes, sem portal/renderer. Estado estável para auditoria dirigida.
