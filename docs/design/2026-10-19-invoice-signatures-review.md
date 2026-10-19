# INV04 — revisão estática da assinatura assistida

Data: 19/10/2026. Destinatário exclusivo: frontend. Fontes: `extension/planner/invoice_signatures_ui.py` e handlers/ações/confirmação em `invoice_history_ui.py`. Sem abrir portais, GUI, dados pessoais ou PDFs; sem geração/renderização ou testes reais de assinatura. URLs foram conferidas apenas como constantes do contrato recebido, sem navegação externa. Não é validação criptográfica, auditoria do backend ou avaliação de serviços externos.

## Parecer

**Textos, sequência de assistência e estados locais correspondem ao escopo examinado, sem alegação indevida de assinatura válida identificada.** Pendência de alinhamento: a apresentação foi implementada em diálogo separado de versões, em vez de versões como filhos da invoice na árvore principal descrita no resumo inicial; frontend deve registrar essa escolha com supervisor antes de afirmar equivalência integral da navegação solicitada. Não há necessidade UX de redesenhar os demais componentes.

### Assistência e cancelamento

- Instrução prévia, com Cancelar por padrão, descreve salvar cópia, login externo prata/ouro, upload manual, assinar/baixar e voltar para importar. Explicita ausência de envio/acesso à conta/armazenamento de credenciais pelo Orbitz.
- `assist_sign` chama save_copy antes de launch; retorno None cancela sem abrir portal; exceção de cópia interrompe antes de launch. Portal é constante `https://assinador.iti.br/`, sem caminho local como parâmetro. Contrato importante: exporter deve devolver caminho somente em sucesso; isso depende da integração/testes backend, não é certificado pela leitura UX.
- Feedback distingue cancelamento, cópia salva + portal aberto e cópia salva + falha ao abrir. Não sugere upload automático ou assinatura concluída. Cópia usa chooser compartilhado com confirmação de sobrescrita.

### Importação e estados das versões

- OPEN seleciona PDF; confirmação posterior com Cancelar por padrão identifica referência, ID abreviado, cliente e período dos serviços. Aviso diz que arquivo pode não estar assinado, não há verificação criptográfica/correspondência automática e estado será “Importada — validação pendente”. Cancelar em qualquer uma dessas etapas não chama import_version.
- `PENDING_LABEL` fixo usado em cada versão com timestamp/ID abreviado; original identificado separadamente. Consultar e copiar roteiam por versão selecionada, sem editar bytes no helper UI. Preservação/imutabilidade efetiva é responsabilidade backend/auditor.
- VALIDAR usa somente `https://validar.iti.gov.br/`, não envia arquivo e não altera estado local. Nota permanente instrui upload manual e explica que abrir portal não muda status. Mensagem após ação mantém ausência de validação local; não aparece indicador “válida”.
- Ações no histórico principal dependem da invoice folha selecionada; cabeçalhos sem ação. Diálogo de versões começa com ações desabilitadas e habilita conforme seleção do original ou ID de versão. VALIDAR também fica disponível para original, coerente com aviso de que nenhum arquivo é considerado assinado/validado automaticamente.

### Exclusão

Confirmação da invoice identifica referência/cliente/emissão/ID/data de arquivamento, com Cancelar padrão, e agora inclui explicitamente original + todas as versões importadas + registro histórico. Distingue preservação do PDF externo e dos registros de horas. Cancelamento não chama delete. Resultado efetivo de exclusão e falha parcial seguem backend/auditoria; não foram exercitados por UX.

## Observações para frontend

1. **Estrutura de navegação a alinhar:** árvore principal rotula a folha “Original · referência…”, mas essa folha também é o alvo para importar versões, abrir Original e versões e excluir a invoice inteira. Dentro do diálogo separado o original é uma linha. Não foi demonstrado erro de seleção, porém “Original” na árvore pode sugerir que Excluir age só naquele arquivo, enquanto a confirmação corretamente abrange tudo. Preferência UX dentro do escopo: folha principal nomeada pela invoice/referência, reservando “Original” para Consultar original e a lista de versões; ou registrar alternativa aprovada com supervisor. Não mudar o alcance da exclusão.
2. O renderer de versões usa wrap_width fixo 500 numa janela com mínimo solicitado 400, diferentemente do histórico principal que adapta ao resize. Scroll horizontal existe, então não se afirma conteúdo inacessível; largura efetiva/rolagem de textos longos precisam de QA nativo. Sugestão local é reutilizar ajuste de wrap à alocação, se necessário, sem mudar geometria da agenda.
3. Feedback selecionável chama grab_focus em vários caminhos. Na cópia cancelada, ele pode conservar mensagem anterior e receber foco, pois não ganha texto novo. Não é alteração indevida de arquivo; verificar se retorno ao acionador/seleção é mais previsível no cancelamento. Mensagem vazia ou antiga não deve ser interpretada como resultado de uma ação cancelada.

A primeira observação exige clareza/alinhamento do alcance da seleção; as outras são riscos/ajustes locais, sem defeito gráfico reproduzido. Não há recomendação de abrir portal automaticamente ao selecionar linha ou de interpretar assinatura no Orbitz.

## Aceite pendente e evidência recebida

Frontend informou 4 testes novos e 9 regressões aprovados, sem portal/GUI; não repetidos por UX. Antes de afirmar integração concluída, evidência sintética deve cobrir cancelamento antes/depois do chooser, cópia falha sem launch, cópia concluída com launch falho, URLs fixas sem arquivo, import cancel sem mutação e roteamento original/versão pelo ID. Integração backend estável ainda estava pendente no marco recebido.

Validação GTK/AT pendente: nome e foco nos diálogos encadeados, Escape/Cancelar retornando ao acionador, FlowBox com seis ações no histórico e três nas versões, textos longos no mínimo, seleção pelo teclado, estado pendente percebido sem depender de cor e confirmação legível antes de excluir. Não pedir nova tentativa gráfica bloqueada nem novo QA de renderização PDF para este parecer. Nenhuma assinatura real deve ser usada como evidência sintética.

Somente este documento em `docs/design/` alterado por UX. Próximo responsável: frontend alinha escolha da navegação/rotulagem, integra backend e repassa parecer/limites ao supervisor/auditor pelo fluxo autorizado.
