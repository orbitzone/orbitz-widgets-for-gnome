# INV-03 — histórico de invoices — frontend — 19/10/2026

Estado: **implementado e estável; parecer UX favorável estaticamente, auditoria/GTK pendentes**. Escopo autorizado: menu, integração pós-exportação e interface local de histórico. Backend mantém invoice_history.py; nenhuma instalação, perfil real, notes, sessão ativa ou publicação foi alterada.

## Arquivos

- `planner_menu.py`: Histórico de invoices imediatamente após Gerar invoice. Arquivadas/backup e suas referências/contagem preservados.
- `invoice_ui.py`: após write do PDF externo, chama record(snapshot,path); depois salva perfis. Falhas dessas duas etapas são avisos independentes, mantendo resultado PDF salvo. Falha no write não arquiva nem salva perfis. Aviso de formulário explica cópia privada no histórico.
- `invoice_history_ui.py`: agrupamento, sessão de ações e diálogo GTK. Carrega backend somente ao abrir; menu/importação da agenda não acessam acervo nem ReportLab.
- `test_invoice_history_frontend.py`: oito testes de contratos e integração em armazenamento temporário.
- `test_invoice_frontend.py`: todos os testes antigos de exportação agora isolam record com mock, inclusive PDF real/perfil temporário. Menu testa quatro ações, callback novo e referência arquivadas no índice2, sem apagar assertivas anteriores.

## Interface e dados

Tree: empresa/timesheet → cliente → ano/mês de **emissão** → invoice. Chaves são sheet_id/client_key, não nomes. Clientes homônimos são distinguidos no rótulo por CPF/CNPJ, apenas na UI local; nomes/documentos nunca entram em caminhos ou logs. Diferentes timesheets homônimas têm chaves distintas, embora seus rótulos ainda possam coincidir (melhoria opcional apontada UX). Múltiplas invoices com mesma referência/mês são mantidas; folhas mostram referência/total/identificador curto. Detalhes incluem empresa, cliente, emissão, período de serviços, horas, total, idioma e criação do registro. Emissão não é confundida com mês dos serviços.

Botões Consultar, Salvar cópia e Excluir ficam desabilitados sem folha selecionada ou em cabeçalhos; sessão também recusa ações sem id de invoice. Consultar usa get_path validado → Gio.File.get_uri → Gio.AppInfo.launch_default_for_uri, sem shell. Duplo clique em folha seleciona o registro antes de abrir. Copiar usa FileChooser com filtro PDF e confirmação nativa de overwrite, caminho de arquivo local; cancelar não chama export_copy. Nome inicial usa apenas invoice/data.

Excluir confirma referência, cliente, emissão, id curto e criação, com Cancelar como default. Texto explica excluir só registro/cópia do histórico, sem tocar PDF externo nem horas. Falhas recarregam a lista e mostram mensagem limitada do backend, incluindo caso de retirada da lista com limpeza privada pendente. Não se afirma que toda falha deixou registro intacto quando backend pode ter concluído parte da operação.

Lista vazia, lista parcialmente ilegível e todos os registros ilegíveis recebem mensagens distintas; demais registros permanecem disponíveis. Ler/corromper não aciona exclusão/limpeza/importação. Somente PDFs novos desde esta atualização são arquivados; nenhum diretório de PDFs antigos é varrido.

Modal820×620 limitado à workarea, mínimo420×300, TreeView com wrap adaptável/scroll, detalhes com rolagem e ações em FlowBox para quebrar em linhas. Rótulos/seleção nativos, nomes acessíveis e feedback selecionável. Interação gráfica/foco/AT/tema/minwidth ainda não comprovados.

## API alinhada

record(snapshot,path), list_records()->dict(records/errors), get_path(id), export_copy(id,path,overwrite=False), delete(id). Metadados retornam snapshot completo, client_key hash, emissão, id UUIDhex, created_at e integridade. Backend informou listagem final barata por metadados/tamanho; bytes/hash completos são verificados nas ações. UI não promete que listagem isolada certifica o conteúdo inteiro de cada PDF.

Frontend não gerencia retenção, sanitização de paths, locks ou limpeza privada, responsabilidades backend. Interfaces usam somente IDs retornados pela API. Nenhuma consulta online ou dado pessoal foi usado nos testes.

## Verificações

`python3 -m unittest discover -s tests -p test_invoice_history_frontend.py -v`: **8/8 aprovados**:

1. Chaves estáveis preservam timesheets/clientes homônimos e múltiplas invoices/mês; agrupamento pela emissão, não período de serviços.
2. Cabeçalhos/nenhuma seleção e exclusão cancelada não acionam operações de arquivo.
3. Ações usam somente registro selecionado, corrupção parcial é reportada, falha de reload limpa estado acionável.
4. Textos diferenciam vazio, parcialmente legível e todos ilegíveis.
5. Detalhes distinguem emissão e período dos serviços.
6. Falhas independentes de record/perfil após PDF salvo produzem avisos distintos.
7. Falha no PDF não chama record/save.
8. Integração real export-session → record → reload/get_path/export_copy/delete em ROOT temporário, usando bytes PDF sintéticos sem renderização; bytes exatos preservados e exclusão deixa externo/cópia baixada intactos.

`python3 -m unittest discover -s tests -p test_invoice_frontend.py -v`: **6/6 aprovados** após isolar todos os hooks record; arquivos reais de PDF/perfil continuam temporários. Warning de dependência load_module já conhecido, sem falha.

AST dos cinco arquivos frontend/testes novos/alterados aprovado. Diff-check de fontes rastreadas conferido ao estabilizar. Sem suíte global ou nova QA/renderização de PDF, conforme escopo.

## UX, auditoria e fechamento RC-17

Parecer em `docs/design/2026-10-19-invoice-history-review.md`: sem impedimento estático no fluxo revisto. Observação textual de todos ilegíveis foi corrigida e testada; opcionais de total com formato PT e rótulo de empresas homônimas seguem ao supervisor, sem bloquear este marco. Ajuste final do feedback de exclusão parcial é evidência frontend, não reinspecionada UX. GTK/AT/foco/FlowBox/longos nomes/confirmar-cancelar reais continuam pendentes.

Estado estável é comunicado diretamente ao auditor e ao supervisor. RC-17 reserva ao supervisor consolidar conclusão/limites, conferir aplicação instalada e entregar comando completo de atualização/reabertura quando aplicável. Frontend não executou atualização nem declara instalação concluída. Não se orienta reinício da sessão por esta entrega de fonte sem coordenação. RAM/EXT/períodos e outros componentes não foram alterados.

## IH-A02 — impedir exportação sobre o próprio histórico

Auditor reproduziu overwrite de um PDF gerenciado pela exportação inicial de invoice, causando divergência de hash do registro anterior. A confirmação de overwrite de um destino externo não autoriza modificar o acervo imutável.

Correção em `InvoiceSession.export`: `check_external_destination` executa **antes** de importar/chamar o writer. Compara tanto o caminho absoluto lexical quanto o caminho resolvido (incluindo symlinks ancestrais/arquivo) com `invoice_history.ROOT` lexical/resolvida e recusa qualquer destino gerenciado. Também falha de forma fechada se não puder determinar essa fronteira, sem tocar PDF/perfis/acervo. Renderer global e backend não foram alterados.

Teste novo com acervo REAL temporário e registro existente cobre: PDF do registro anterior, novo PDF dentro da raiz, ancestral symlink para a raiz, arquivo symlink para PDF gerenciado e candidato lexical dentro da raiz contendo `..`. Em todos os cinco casos, writer/record/perfis **não chamados**, bytes antigos intactos e get/hash do registro ainda válidos. Mocks legados de archive agora informam ROOT sintética, sem acessar acervo real.

Resultados desta correção: `test_invoice_history_frontend.py` **9/9** e `test_invoice_frontend.py` **6/6** aprovados. Não houve teste gráfico, alteração de instalação ou nova renderização QA. A proteção valida o destino antes da escrita; não afirma proteção geral contra processos externos trocando a árvore de diretórios depois dessa validação. Estado estável novamente encaminhado ao auditor para verificação independente do achado.
