# INV-01 — menu da agenda e invoice/PDF — frontend — 18/10/2026

Estado: **implementado com testes específicos aprovados; parecer UX final favorável estaticamente; auditoria/validação GTK pendentes**. Sem instalação, reload, sessão ativa, commit ou push. Dados de testes exclusivamente sintéticos e temporários.

## Entrega e propriedade

- `extension/planner/calendar-app.py`: título/data e menu compartilham header horizontal; heading expande à esquerda e botão à direita. Removidos somente os dois botões de ação do footer; status preservado. Atualização de contagem de arquivadas delegada ao menu, sem mudar gestão das páginas/arquivos.
- `extension/planner/planner_menu.py`: dropdown na ordem Gerar invoice/PDF, Timesheets arquivadas, Restaurar backup. Ações existentes chamam os mesmos callbacks. `archived_button` permanece referência ao item correspondente, com label/nome acessível atualizados após render/restauração. Botão nativo de menu tem nome acessível Mais ações da agenda.
- `extension/planner/invoice_ui.py`: formulário GTK e sessão de revisão/exportação. Usa domínio/perfis/PDF do backend; nenhuma duplicação do cálculo monetário ou edição do histórico. Importação de invoice_pdf/ReportLab só ocorre na exportação, com erro amigável tanto se falhar o import do módulo quanto o import tardio dentro de write.
- `tests/test_invoice_frontend.py`: contratos do menu, sessão e integração de exportação com perfis em diretório temporário.

Backend mantém propriedade exclusiva de `invoice.py`, `invoice_profiles.py`, `invoice_pdf.py` e testes de domínio; ferramentas deploy não foram editadas.

## Formulário e comportamento

UI em português: sheet ativa/arquivada (aba atual pré-selecionada quando válida), emitente nome/CPF-CNPJ, cliente nome/CPF-CNPJ/endereço fiscal, valor por hora, moeda BRL editável independente do idioma PT/EN, todo histórico por padrão ou intervalo ISO explícito. Referência editável INV-data-8hex e emissão ISO hoje completam o contrato do documento; não são numeração fiscal nem consulta cadastral. CPF/CNPJ é campo de texto livre, compatível com o CNPJ alfanumérico suportado pelo backend.

Emitente/idioma globais; cliente/taxa/moeda por sheet, conforme contrato. A troca de sheet preserva rascunhos apenas em memória e não grava perfis. Aviso visível explica esse alcance e que só serão lembrados após salvar PDF. Cancelar diálogo/chooser não chama save; erro de validação/PDF também não grava perfil. Falha em salvar perfil após sucesso do PDF gera aviso separado, sem apresentar a exportação como falha.

Revisar prévia lê dados frescos e gera snapshot independente, com período/datas, HH:MM/minutos, taxa, moeda, total e aviso de timer ativo excluído. Qualquer alteração invalida snapshot e desabilita salvar. APPLY desabilita salvar antes de validar; falha também limpa a prévia antiga. Exportação utiliza somente o snapshot revisado, portanto mudanças posteriores na fonte não alteram silenciosamente aquele documento. Registros/timers não são modificados. A UI esclarece fatura de serviços, sem nota fiscal eletrônica, e exclusão de cronômetro em andamento.

FileChooser PDF tem confirmação nativa de substituição; backend recebe overwrite=True somente para o caminho que passou pelo sinal de confirmação antes da aceitação. Nome inicial usa apenas invoice/data, sem nome de cliente/sheet ou barras. Backend conserva recusa de overwrite sem autorização e gravação atômica/privada.

Modal default até640×680 limitado à workarea, mínimo360×280, rolagem vertical; endereço multiline com altura controlada e Tab para próximo campo. Captions têm wrap e nomes acessíveis/mnemonics sem duplicação dos atalhos principais. Nomes longos de sheet são elipsizados, com tooltip completo. Prévia/erro selecionáveis recebem foco após revisão/erro; comportamento real de foco/DPI/rolagem ainda não foi exercitado em GTK.

## Contrato integrado

`invoice.build_snapshot(sheet, issuer, client, rate, currency, language, reference, issued_on, start/end)` valida e calcula. `invoice.format_money` formata a prévia PT sem vincular moeda ao idioma do PDF. `invoice_profiles.load/save` respeitam os escopos global/sheet. `invoice_pdf.write(snapshot,path,overwrite=...)` retorna Path após PDF privado salvo; somente então a sessão chama save dos perfis. Erros não são registrados em logs; dados privados permanecem nas interfaces/arquivos locais.

## Verificações desta execução

`python3 -m unittest discover -s tests -p test_invoice_frontend.py -v`: **6/6 aprovados**:

1. Menu/header/ordem/nome acessível/callbacks e contagem1→0 após resgate.
2. PT/EN, totais por minutos, BRL independente do idioma, snapshot/timer e perfil somente após PDF.
3. Invalidação/cancelamento e validação falha sem persistência.
4. Falha PDF/arquivo existente e dependência ausente no import ou dentro de write, sem perfil salvo.
5. Snapshot lê fonte fresca, fica congelado para exportação e distingue falha de perfil pós-PDF.
6. Sessão→PDF **real** e round-trip de perfil privado em PT/EN, verificando cabeçalho PDF, modo0600 e taxa/cliente/idioma/moeda; temporários removidos. Não é repetição da QA visual.

`ast.parse`: calendar-app.py, planner_menu.py, invoice_ui.py e teste aprovados. `git diff --check` do calendário aprovado. A execução real do PDF emitiu DeprecationWarning de load_module na dependência; não houve falha nem edição de dependência vendorizada.

Supervisor informou QA visual própria de quatro páginas de amostras PT/EN, legíveis com acentos/XML/cabeçalhos repetidos; evidência pertence ao relatório/skillPDF do supervisor, não foi repetida nem apresentada como captura frontend.

## UX e limites

Primeira revisão em `docs/design/2026-10-18-invoice-review.md`. Ações A–C/E aplicadas: wrap/elipse para strings longas, atalhos distintos, prévia inválida desabilita salvar, foco explícito na prévia/erro. D alinhado com contrato backend: emitente/idioma deliberadamente globais, cliente/taxa/moeda por sheet, agora explicado na UI. Releitura final solicitada ao UX; parecer será repassado ao supervisor.

Sem execução gráfica GTK ou nova tentativa Broadway bloqueada. Testes de menu usam atores sintéticos; testes da sessão não certificam Tab/Alt/foco, workarea, chooser nativo, nomes longos ou PDF renderizado na página. Nome do documento/partes são sintéticos em testes; nenhuma credencial/perfil real lido ou copiado ao repositório.

Próximos responsáveis: UX finaliza parecer restrito; frontend encaminha estabilidade diretamente ao auditor e supervisor. Auditor revisa integração/perfis/cancel/overwrite/import tardio; supervisor consolida requisitos/documentação/QA PDF e coordena atualização somente no escopo autorizado. RAM/EXT e branding não foram alterados.

## Parecer UX final e encaminhamento

Releitura final em `docs/design/2026-10-18-invoice-review.md`: A–C tratados, D confirmado no backend como globais deliberados, E foco/warnings da revisão presentes; sem impedimento estático nos caminhos revistos. Exportação também passou a focar erro depois de destruir o chooser em caso de falha, inclusive extensão inválida. Confirmação gráfica/AT/retorno de foco permanece pendente. Checklist PDF PTEN/BRLUSD, endereços longos/acentos/descrição1000/token sem espaços/multipágina/valores altos/taxa fracionária será encaminhado ao supervisor; QA visual real permanece responsabilidade dele. Estado frontend estável para auditoria independente.
